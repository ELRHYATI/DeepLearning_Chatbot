"""
Router for plagiarism detection
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
from app.database import get_db
from app.models import User, Document
from app.routers.auth import get_current_user, get_current_user_optional
from app.schemas import PlagiarismCheckRequest, PlagiarismCheckResponse, PlagiarismSummary
from app.services.plagiarism_service import PlagiarismService
from app.services.ai_detection_service import AIDetectionService
from app.services.document_processor import DocumentProcessor
from app.utils.logger import get_logger
import os

logger = get_logger()

router = APIRouter()
plagiarism_service = PlagiarismService()
ai_detection_service = AIDetectionService()
document_processor = DocumentProcessor()


@router.post("/check-text", response_model=PlagiarismCheckResponse)
async def check_text_plagiarism(
    request: PlagiarismCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check text for plagiarism against stored documents
    
    Args:
        request: Text to check and options
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Plagiarism check results
    """
    try:
        results = plagiarism_service.check_plagiarism(
            text=request.text,
            db=db,
            user_id=current_user.id,
            exclude_document_ids=request.exclude_document_ids,
            min_similarity=request.min_similarity or 0.7
        )
        
        summary = plagiarism_service.get_plagiarism_summary(results)
        
        logger.info(
            f"Plagiarism check completed for user {current_user.id}",
            extra_data={
                "event": "plagiarism_check",
                "user_id": current_user.id,
                "plagiarism_detected": results['plagiarism_detected'],
                "similarity": results['overall_similarity']
            }
        )
        
        return PlagiarismCheckResponse(
            **results,
            summary=summary
        )
    
    except Exception as e:
        logger.error(f"Error in plagiarism check: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Erreur lors de la vérification: {str(e)}")


@router.post("/check-document/{document_id}", response_model=PlagiarismCheckResponse)
async def check_document_plagiarism(
    document_id: int,
    min_similarity: Optional[float] = 0.7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check a specific document for plagiarism
    
    Args:
        document_id: ID of document to check
        min_similarity: Minimum similarity threshold (0-1)
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Plagiarism check results
    """
    # Verify document belongs to user
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document non trouvé ou vous n'avez pas la permission"
        )
    
    try:
        results = plagiarism_service.check_document_plagiarism(
            document_id=document_id,
            db=db,
            min_similarity=min_similarity
        )
        
        summary = plagiarism_service.get_plagiarism_summary(results)
        
        logger.info(
            f"Document plagiarism check completed: {document_id}",
            extra_data={
                "event": "document_plagiarism_check",
                "user_id": current_user.id,
                "document_id": document_id,
                "plagiarism_detected": results['plagiarism_detected']
            }
        )
        
        return PlagiarismCheckResponse(
            **results,
            summary=summary
        )
    
    except Exception as e:
        logger.error(f"Error checking document plagiarism: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Erreur lors de la vérification: {str(e)}")


@router.post("/check-upload", response_model=PlagiarismCheckResponse)
async def check_uploaded_file_plagiarism(
    file: UploadFile = File(...),
    min_similarity: Optional[float] = 0.7,
    exclude_document_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check an uploaded file for plagiarism
    
    Args:
        file: File to check
        min_similarity: Minimum similarity threshold
        exclude_document_ids: Document IDs to exclude
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Plagiarism check results
    """
    # Determine file type
    file_type = file.filename.split('.')[-1].lower() if '.' in file.filename else "txt"
    
    if file_type not in ["pdf", "txt", "docx"]:
        raise HTTPException(
            status_code=400,
            detail="Type de fichier non supporté. Utilisez PDF, TXT ou DOCX."
        )
    
    # Save file temporarily
    import tempfile
    import shutil
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        tmp_path = tmp_file.name
    
    try:
        # Extract text
        text = document_processor.extract_text_from_document(tmp_path, file_type)
        
        # Check for plagiarism
        results = plagiarism_service.check_plagiarism(
            text=text,
            db=db,
            user_id=current_user.id,
            exclude_document_ids=exclude_document_ids,
            min_similarity=min_similarity
        )
        
        summary = plagiarism_service.get_plagiarism_summary(results)
        
        logger.info(
            f"Uploaded file plagiarism check completed",
            extra_data={
                "event": "upload_plagiarism_check",
                "user_id": current_user.id,
                "filename": file.filename,
                "plagiarism_detected": results['plagiarism_detected']
            }
        )
        
        return PlagiarismCheckResponse(
            **results,
            summary=summary
        )
    
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/check-with-ai-detection")
async def check_plagiarism_with_ai_detection(
    request: PlagiarismCheckRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Check text for both plagiarism and AI generation
    
    Args:
        request: Text to check
        db: Database session
        current_user: Optional current authenticated user (for personalized plagiarism checking)
    
    Returns:
        Combined plagiarism and AI detection results
    """
    try:
        # Get user_id if authenticated, otherwise None (check only against knowledge base)
        user_id = current_user.id if current_user else None
        
        # Check plagiarism (will check against knowledge base if no user_id)
        plagiarism_results = plagiarism_service.check_plagiarism(
            text=request.text,
            db=db,
            user_id=user_id,
            exclude_document_ids=request.exclude_document_ids,
            min_similarity=request.min_similarity or 0.7
        )
        
        plagiarism_summary = plagiarism_service.get_plagiarism_summary(plagiarism_results)
        
        # Detect AI
        ai_results = ai_detection_service.detect_ai_text(request.text, include_details=True)
        
        # Combined analysis
        combined = ai_detection_service.combined_analysis(
            request.text,
            plagiarism_results
        )
        
        logger.info(
            f"Combined analysis completed" + (f" for user {current_user.id}" if current_user else " (anonymous)"),
            extra_data={
                "event": "combined_analysis",
                "user_id": current_user.id if current_user else None,
                "ai_probability": ai_results['ai_probability'],
                "plagiarism_detected": plagiarism_results['plagiarism_detected']
            }
        )
        
        return {
            'plagiarism': {
                **plagiarism_results,
                'summary': plagiarism_summary
            },
            'ai_detection': ai_results,
            'combined': combined
        }
    
    except Exception as e:
        logger.error(f"Error in combined analysis: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")


@router.post("/detect-ai")
async def detect_ai_text(
    request: PlagiarismCheckRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Detect if text is AI-generated
    
    Args:
        request: Text to analyze (only 'text' field is used)
        current_user: Optional current user
    
    Returns:
        AI detection results
    """
    try:
        results = ai_detection_service.detect_ai_text(request.text, include_details=True)
        
        return results
    
    except Exception as e:
        logger.error(f"Error in AI detection: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Erreur lors de la détection: {str(e)}")

