from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from app.database import get_db
from app.models import Document, User
from app.schemas import DocumentResponse
from app.services.rag_service import RAGService

router = APIRouter()
rag_service = RAGService()

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current authenticated user from JWT token, or return None if not authenticated"""
    from jose import JWTError, jwt
    import os
    
    if not credentials:
        # No token provided - return default user for anonymous access
        user = db.query(User).filter(User.username == "default").first()
        if not user:
            user = User(username="default", email="default@example.com", hashed_password="")
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    try:
        token = credentials.credentials
        SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        ALGORITHM = "HS256"
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            user = db.query(User).filter(User.username == "default").first()
            if not user:
                user = User(username="default", email="default@example.com", hashed_password="")
                db.add(user)
                db.commit()
                db.refresh(user)
            return user
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = db.query(User).filter(User.username == "default").first()
            if not user:
                user = User(username="default", email="default@example.com", hashed_password="")
                db.add(user)
                db.commit()
                db.refresh(user)
        return user
    except (JWTError, Exception):
        user = db.query(User).filter(User.username == "default").first()
        if not user:
            user = User(username="default", email="default@example.com", hashed_password="")
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload and process a document for RAG."""
    # Determine file type
    file_type = file.filename.split('.')[-1].lower() if '.' in file.filename else "txt"
    
    if file_type not in ["pdf", "txt", "docx"]:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, TXT, or DOCX.")
    
    # Save file
    file_path = os.path.join(UPLOAD_DIR, f"{current_user.id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Save document record first (to get document_id)
    document = Document(
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        file_type=file_type,
        processed=False
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Process document with RAG (with user_id and document_id for metadata)
    processed = rag_service.process_document(
        file_path, 
        file_type,
        user_id=current_user.id,
        document_id=document.id
    )
    
    # Update processed status
    document.processed = processed
    db.commit()
    
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        file_type=document.file_type,
        uploaded_at=document.uploaded_at,
        processed=document.processed
    )

@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all documents for the current user."""
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()
    return [
        DocumentResponse(
            id=d.id,
            filename=d.filename,
            file_type=d.file_type,
            uploaded_at=d.uploaded_at,
            processed=d.processed
        )
        for d in documents
    ]

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    db.delete(document)
    db.commit()
    return {"message": "Document deleted"}

