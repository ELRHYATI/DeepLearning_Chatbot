from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, AsyncGenerator, Tuple
import os
import shutil
import json
from datetime import datetime
from app.database import get_db
from app.models import ChatSession, Message, User
from app.schemas import (
    ChatSessionCreate, ChatSessionResponse, ChatSessionDetail,
    MessageCreate, MessageResponse
)
from app.services.grammar_service import GrammarService
from app.services.qa_service import QAService
from app.services.reformulation_service import ReformulationService
from app.services.summarization_service import SummarizationService
from app.services.plan_service import PlanService
from app.services.rag_service import RAGService
from app.services.document_processor import DocumentProcessor
from app.services.ollama_service import OllamaService
from app.utils.streaming import (
    stream_text_progressive, 
    create_streaming_response,
    format_sse_event
)
from app.utils.logger import get_logger
from app.utils.error_handler import AppException, ErrorCode
from app.utils.export import export_to_markdown, export_to_pdf
from app.utils.sharing import generate_share_token, create_share_link, validate_share_token
from app.utils.search import search_messages_fulltext, search_sessions, get_search_suggestions
from app.utils.hybrid_search import HybridSearch
from app.utils.redis_cache import cache, cache_result
from app.schemas import SearchRequest, SearchResponse, SessionSearchRequest, SessionSearchResponse
from fastapi.responses import Response, StreamingResponse
import os

router = APIRouter()
grammar_service = GrammarService()
qa_service = QAService()
reformulation_service = ReformulationService()
summarization_service = SummarizationService()
plan_service = PlanService()
rag_service = RAGService()
document_processor = DocumentProcessor()
hybrid_search = HybridSearch()
logger = get_logger()


def detect_and_fix_incomplete_greeting(text: str) -> Tuple[str, bool]:
    """
    Detect and fix incomplete or misspelled greetings.
    Returns (corrected_text, is_greeting_detected)
    """
    text_lower = text.lower().strip()
    
    # Remove spaces and check if it matches common greetings
    text_no_spaces = text_lower.replace(" ", "")
    
    # Common greeting patterns and their corrections
    greeting_patterns = {
        "salut": ["salut", "salu", "sal", "sa lut", "sa lut e", "salut e", "salu t"],
        "bonjour": ["bonjour", "bon jour", "bonjour", "bonj", "bon jour"],
        "bonsoir": ["bonsoir", "bon soir", "bonsoi", "bon soir"],
        "hello": ["hello", "helo", "hel lo", "he llo"],
        "hi": ["hi", "h i", "hii"],
        "hey": ["hey", "he y", "heyy"]
    }
    
    # Check if text (with or without spaces) matches a greeting pattern
    for correct_greeting, variations in greeting_patterns.items():
        # Check exact matches (with or without spaces)
        if text_lower in variations or text_no_spaces in variations:
            return correct_greeting, True
        
        # Check if removing spaces from variations matches
        for variation in variations:
            variation_no_spaces = variation.replace(" ", "")
            if text_no_spaces == variation_no_spaces:
                return correct_greeting, True
        
        # Check if removing spaces makes it match the correct greeting
        if text_no_spaces == correct_greeting.replace(" ", ""):
            return correct_greeting, True
        
        # Check similarity (simple character matching for incomplete words)
        if len(text_no_spaces) >= 3:
            # Check if first 3-4 characters match
            if correct_greeting.startswith(text_no_spaces[:min(4, len(text_no_spaces))]):
                if len(text_no_spaces) <= len(correct_greeting) + 2:  # Allow small differences
                    return correct_greeting, True
    
    return text, False

# Initialize Ollama service (optional, will check on first use)
ollama_service = None
try:
    ollama_service = OllamaService()
    if ollama_service.is_available():
        logger.info(f"Ollama initialized with models: {ollama_service.get_available_models()}")
    else:
        logger.info("Ollama not available, will use QA service as fallback")
except Exception as e:
    logger.warning(f"Could not initialize Ollama service: {e}")
    ollama_service = None

UPLOAD_DIR = "./chat_uploads"
PROCESSED_DIR = "./processed_documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

UPLOAD_DIR = "./chat_uploads"
PROCESSED_DIR = "./processed_documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Import proper authentication from auth router
from app.routers.auth import get_current_user as get_authenticated_user

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current authenticated user from JWT token, or return default user for anonymous access.
    This allows anonymous users to use the chat, but authenticated users get their actual user.
    """
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
            # Return default user if token invalid
            user = db.query(User).filter(User.username == "default").first()
            if not user:
                user = User(username="default", email="default@example.com", hashed_password="")
                db.add(user)
                db.commit()
                db.refresh(user)
            return user
        
        # Get the actual authenticated user
        user = db.query(User).filter(User.email == email).first()
        if user:
            # Log successful authentication for debugging
            logger.debug(f"Authenticated user: {user.id} ({user.email})")
            return user
        else:
            # User not found - return default user
            logger.warning(f"User with email {email} not found in database")
            user = db.query(User).filter(User.username == "default").first()
            if not user:
                user = User(username="default", email="default@example.com", hashed_password="")
                db.add(user)
                db.commit()
                db.refresh(user)
            return user
    except (JWTError, Exception) as e:
        # Log the error for debugging
        logger.warning(f"Authentication error: {e}, falling back to default user")
        # Return default user on any error
        user = db.query(User).filter(User.username == "default").first()
        if not user:
            user = User(username="default", email="default@example.com", hashed_password="")
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    session_data: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new chat session."""
    session = ChatSession(
        user_id=current_user.id,
        title=session_data.title or "New Chat"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0
    )

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all chat sessions for the current user."""
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).all()
    return [
        ChatSessionResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=len(s.messages)
        )
        for s in sessions
    ]

@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
async def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific chat session with messages."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return ChatSessionDetail(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(session.messages),
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                module_type=m.module_type,
                created_at=m.created_at,
                metadata=json.loads(m.message_metadata) if m.message_metadata else None
            )
            for m in session.messages
        ]
    )

@router.put("/sessions/{session_id}")
async def update_session(
    session_id: int,
    session_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a chat session (e.g., title)."""
    from pydantic import BaseModel
    
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if "title" in session_data:
        session.title = session_data["title"]
        session.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(session.messages)
    )

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a chat session."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db.delete(session)
    db.commit()
    return {"message": "Session deleted"}

@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def create_message(
    session_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new message and get AI response."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if this is the first user message (before adding new one)
    existing_user_messages = [m for m in session.messages if m.role == "user"]
    is_first_message = len(existing_user_messages) == 0
    
    # Save user message
    user_message = Message(
        session_id=session_id,
        role="user",
        content=message_data.content,
        module_type=message_data.module_type
    )
    db.add(user_message)
    
    # Update session title based on first message if title is still default
    if is_first_message and (session.title.startswith("Conversation ") or session.title.startswith("New Chat") or session.title == "Nouvelle conversation"):
        # Generate title from message content (truncate to 50 chars)
        title = message_data.content.strip()
        # Remove markdown and extra whitespace
        import re
        title = re.sub(r'[#*_`]', '', title)  # Remove markdown
        title = re.sub(r'\s+', ' ', title)  # Normalize whitespace
        if len(title) > 50:
            title = title[:47] + "..."
        if not title:
            title = "Nouvelle conversation"
        session.title = title
    
    db.commit()
    
    # Check for greetings first
    def is_greeting(text: str) -> bool:
        """Check if the message is a greeting."""
        greetings = [
            "bonjour", "bonsoir", "salut", "hello", "hi", "hey",
            "bonne journée", "bonne soirée", "bon matin",
            "comment allez-vous", "comment ça va", "ça va",
            "comment vas-tu", "comment allez vous"
        ]
        text_lower = text.lower().strip()
        # Also check without spaces
        text_no_spaces = text_lower.replace(" ", "")
        return any(greeting in text_lower or greeting == text_no_spaces for greeting in greetings)
    
    def is_conversational_question(text: str) -> bool:
        """Check if the message is a simple conversational question that needs a natural response."""
        conversational_patterns = [
            "vous pouvez", "tu peux", "pouvez-vous", "peux-tu",
            "vous pouvez m'aider", "tu peux m'aider", "pouvez vous m'aider",
            "aidez-moi", "aide-moi", "aide moi",
            "comment faire", "comment puis-je", "comment je peux",
            "qu'est-ce que tu", "qu'est-ce que vous",
            "qui es-tu", "qui êtes-vous", "c'est quoi",
            "ça marche", "ça fonctionne", "comment ça marche",
            "merci", "de rien", "pas de problème"
        ]
        text_lower = text.lower().strip()
        # Check if it's a short conversational message (less than 50 chars)
        if len(text) < 50:
            return any(pattern in text_lower for pattern in conversational_patterns)
        return False
    
    def get_conversational_response(text: str) -> str:
        """Generate a natural, comprehensive conversational response."""
        text_lower = text.lower().strip()
        
        if any(word in text_lower for word in ["vous pouvez", "tu peux", "pouvez-vous", "peux-tu", "aider", "aide"]):
            return """Bien sûr ! Je suis votre assistant académique AI et je suis là pour vous aider. 

Je peux vous assister avec :
• **Correction grammaticale** : Corrigez vos textes en français
• **Questions académiques** : Répondez à vos questions scientifiques et académiques
• **Reformulation** : Reformulez vos textes dans un style académique
• **Rédaction scientifique** : Aidez-vous à écrire dans le style de vos documents de référence

Quelle est votre question ou votre demande ?"""
        
        elif any(word in text_lower for word in ["merci", "thanks", "thank you"]):
            return """Je vous en prie ! C'est un plaisir de vous aider. 

N'hésitez pas si vous avez d'autres questions. Je suis toujours disponible pour vous assister dans vos travaux académiques."""
        
        elif any(word in text_lower for word in ["qui es-tu", "qui êtes-vous", "c'est quoi", "qu'est-ce que tu"]):
            return """Je suis votre assistant académique AI spécialisé dans l'aide aux étudiants et chercheurs. 

**Mes capacités :**
• Correction grammaticale et orthographique en français
• Réponses aux questions académiques et scientifiques
• Reformulation de textes dans un style académique
• Aide à la rédaction scientifique basée sur vos documents de référence
• Traitement et amélioration de documents (PDF, DOCX, TXT)

Je peux utiliser vos documents uploadés comme source de connaissances et de style pour vous fournir des réponses plus précises et adaptées à votre domaine.

Comment puis-je vous aider aujourd'hui ?"""
        
        elif any(word in text_lower for word in ["comment faire", "comment puis-je", "comment je peux"]):
            return """Je peux vous guider étape par étape ! 

Pour mieux vous aider, pouvez-vous me donner plus de détails sur :
• Ce que vous souhaitez accomplir
• Le type de document ou de texte concerné
• Votre objectif (correction, reformulation, rédaction, etc.)

Expliquez-moi votre besoin et je vous fournirai des instructions claires et détaillées."""
        
        else:
            return """Je comprends. Je suis là pour vous aider avec vos travaux académiques.

**Que puis-je faire pour vous ?**
• Corriger un texte
• Répondre à une question académique
• Reformuler un texte
• Vous aider à écrire dans un style scientifique
• Traiter un document

Quelle est votre demande ?"""
    
    def get_greeting_response() -> str:
        """Generate an appropriate greeting response."""
        responses = [
            "Bonjour ! Je suis votre assistant académique AI. Comment puis-je vous aider aujourd'hui ?",
            "Bonjour ! Je suis là pour vous aider avec la correction grammaticale, les questions-réponses académiques, et la reformulation de textes. Que souhaitez-vous faire ?",
            "Salut ! Je suis votre assistant académique. Je peux vous aider à corriger votre français, répondre à vos questions, ou reformuler vos textes. Par quoi commençons-nous ?"
        ]
        import random
        return random.choice(responses)
    
    # Generate AI response based on module type
    ai_response_content = ""
    try:
        # Handle greetings in general mode
        if message_data.module_type == "general" and is_greeting(message_data.content):
            ai_response_content = get_greeting_response()
        
        elif message_data.module_type == "ollama":
            # Ollama AI mode - use Ollama for all operations
            selected_model = None
            if message_data.metadata and "model" in message_data.metadata:
                selected_model = message_data.metadata["model"]
            
            if not ollama_service or not ollama_service.is_available():
                ai_response_content = "⚠️ **Ollama n'est pas disponible.**\n\n"
                ai_response_content += "Pour utiliser le mode Ollama AI:\n"
                ai_response_content += "1. Installez Ollama depuis https://ollama.ai\n"
                ai_response_content += "2. Exécutez `ollama pull mistral`\n"
                ai_response_content += "3. Assurez-vous qu'Ollama est en cours d'exécution\n\n"
                ai_response_content += "En attendant, je peux vous aider avec les autres modes disponibles."
            else:
                # Use Ollama for all operations based on content analysis
                text_lower = message_data.content.lower()
                
                # Detect if it's a question
                is_question = any(word in text_lower for word in ["qu'est", "comment", "pourquoi", "explique", "définir", "qu'est-ce", "?"])
                
                # Detect if it's grammar correction
                is_grammar = any(word in text_lower for word in ["corrige", "correction", "grammaire", "orthographe", "fautes"])
                
                # Detect if it's reformulation request
                is_reformulation = any(word in text_lower for word in ["reformule", "réécris", "paraphrase", "améliore", "style"])
                
                if is_question:
                    # Use Ollama for QA
                    context = None
                    try:
                        # Get user document IDs
                        from app.models import Document
                        user_docs = db.query(Document).filter(
                            Document.user_id == current_user.id,
                            Document.processed == True
                        ).all()
                        user_document_ids = [str(doc.id) for doc in user_docs]
                        
                        rag_results = rag_service.search(
                            query=message_data.content,
                            user_documents=user_document_ids,
                            top_k=4
                        )
                    except Exception as e:
                        logger.warning(f"RAG search failed: {e}")
                        rag_results = []
                    if rag_results:
                        context = "\n\n".join([r.get("text", "") or r.get("content", "") for r in rag_results[:3] if r.get("text") or r.get("content")])
                    
                    result = ollama_service.answer_question_sync(message_data.content, context, model=selected_model)
                    if result and not result.get('error'):
                        ai_response_content = f"**Réponse:**\n\n{result['answer']}\n\n"
                        if result.get('confidence', 0) > 0:
                            confidence = result['confidence']
                            if confidence > 0.75:
                                confidence_label = "très élevée"
                            elif confidence > 0.60:
                                confidence_label = "élevée"
                            elif confidence > 0.45:
                                confidence_label = "modérée"
                            else:
                                confidence_label = "acceptable"
                            ai_response_content += f"*Niveau de confiance: {confidence_label} ({confidence:.0%})*\n"
                    else:
                        ai_response_content = result.get('answer', 'Erreur lors de la génération de la réponse.')
                
                elif is_grammar:
                    # Use Ollama for grammar correction
                    system_prompt = (
                        "Tu es un expert en grammaire et orthographe française. "
                        "Corrige le texte suivant en identifiant et corrigeant toutes les erreurs grammaticales, "
                        "orthographiques et de style. Retourne le texte corrigé avec des explications brèves pour chaque correction."
                    )
                    result = ollama_service.generate_response_sync(
                        prompt=f"Corrige ce texte: {message_data.content}",
                        model=selected_model,
                        system_prompt=system_prompt,
                        temperature=0.2,
                        max_tokens=2000
                    )
                    if result and not result.get('error'):
                        ai_response_content = f"✅ **Texte corrigé:**\n\n{result.get('response', message_data.content)}\n\n"
                    else:
                        ai_response_content = "Erreur lors de la correction grammaticale."
                
                elif is_reformulation:
                    # Use Ollama for reformulation
                    style = "academic"  # Default style
                    if message_data.metadata and "style" in message_data.metadata:
                        style = message_data.metadata["style"]
                    
                    result = ollama_service.reformulate_text_sync(message_data.content, style, model=selected_model)
                    if result and not result.get('changes', {}).get('error'):
                        reformulated = result.get('reformulated_text', message_data.content)
                        ai_response_content = f"**Texte reformulé ({style}):**\n\n{reformulated}\n\n"
                    else:
                        ai_response_content = "Erreur lors de la reformulation."
                
                else:
                    # General conversation with Ollama
                    if is_greeting(message_data.content):
                        ai_response_content = get_greeting_response()
                    else:
                        system_prompt = (
                            "Tu es un assistant académique français intelligent et serviable. "
                            "Réponds de manière précise, structurée et académique. "
                            "Utilise un langage clair et professionnel."
                        )
                        result = ollama_service.generate_response_sync(
                            prompt=message_data.content,
                            model=selected_model,
                            system_prompt=system_prompt,
                            temperature=0.7,
                            max_tokens=2000
                        )
                        if result and not result.get('error'):
                            ai_response_content = result.get('response', 'Erreur lors de la génération de la réponse.')
                        else:
                            ai_response_content = "Erreur lors de la génération de la réponse."
        
        elif message_data.module_type == "grammar":
            # First check for incomplete/misspelled greetings
            corrected_greeting, is_greeting_detected = detect_and_fix_incomplete_greeting(message_data.content)
            
            if is_greeting_detected and corrected_greeting != message_data.content:
                # Provide helpful correction for incomplete greeting
                ai_response_content = f"✅ **Correction détectée:**\n\n"
                ai_response_content += f"**Texte original:** {message_data.content}\n"
                ai_response_content += f"**Texte corrigé:** {corrected_greeting}\n\n"
                ai_response_content += f"💡 **Explication:** Il semble que vous vouliez dire \"{corrected_greeting}\". "
                ai_response_content += "J'ai corrigé votre message. "
                ai_response_content += f"{get_greeting_response()}"
            else:
                # Use grammar service for normal grammar correction
                result = grammar_service.correct_text(message_data.content)
                if result.get('corrections'):
                    ai_response_content = f"✅ **Texte corrigé:**\n\n{result['corrected_text']}\n\n"
                    ai_response_content += "**Corrections apportées:**\n"
                    for corr in result['corrections']:
                        ai_response_content += f"• {corr['original']} → **{corr['corrected']}**\n  *{corr['explanation']}*\n"
                else:
                    ai_response_content = f"✅ Votre texte semble correct!\n\n{result['corrected_text']}"
        
        elif message_data.module_type == "qa":
            # Use RAG service for context retrieval
            context = None
            sources = []
            user_document_ids = None
            
            # Get user's document IDs if available
            if current_user:
                from app.models import Document
                user_docs = db.query(Document).filter(
                    Document.user_id == current_user.id,
                    Document.processed == True
                ).all()
                user_document_ids = [str(doc.id) for doc in user_docs]
            
            # Try RAG first if documents are available (using new RAG service)
            if user_document_ids or True:  # Always try knowledge base
                try:
                    # Use new RAG service integrated in QA service
                    # The QA service will handle RAG internally
                    # Get use_web_search from request body
                    use_web_search = getattr(message_data, 'use_web_search', None) if hasattr(message_data, 'use_web_search') else None
                    result = qa_service.answer_question(
                        question=message_data.content,
                        context=None,  # Let RAG service find context
                        use_web_search=use_web_search,
                        user_id=str(current_user.id) if current_user else None,
                        user_document_ids=user_document_ids,
                        metadata=message_data.metadata if hasattr(message_data, 'metadata') else None
                    )
                except Exception as e:
                    logger.warning(f"RAG-enhanced QA failed: {e}, using fallback")
                    # Fallback to old method - use search instead
                    try:
                        rag_results = rag_service.search(
                            query=message_data.content,
                            user_documents=user_document_ids,
                            top_k=6
                        )
                        context = None
                        if rag_results:
                            context_parts = [r.get("text", "") or r.get("content", "") for r in rag_results[:4] if r.get("text") or r.get("content")]
                            context = "\n\n".join(context_parts)
                        result = qa_service.answer_question(message_data.content, context)
                    except Exception as fallback_error:
                        logger.error(f"Fallback RAG also failed: {fallback_error}")
                        result = qa_service.answer_question(message_data.content, None)
            else:
                result = qa_service.answer_question(message_data.content, context)
            
            if result.get('answer') and result['answer'] != "Désolé, le modèle de question-réponse n'est pas disponible pour le moment.":
                ai_response_content = f"**Réponse:**\n\n{result['answer']}\n\n"
                if result.get('confidence', 0) > 0:
                    # Improved confidence labels with better thresholds
                    confidence = result['confidence']
                    if confidence > 0.75:
                        confidence_label = "très élevée"
                    elif confidence > 0.60:
                        confidence_label = "élevée"
                    elif confidence > 0.45:
                        confidence_label = "modérée"
                    else:
                        confidence_label = "acceptable"
                    ai_response_content += f"*Niveau de confiance: {confidence_label} ({confidence:.0%})*\n"
                
                # Display sources with better formatting
                sources_list = []
                if result.get('sources') and len(result['sources']) > 0:
                    sources_list = result['sources']
                elif sources:
                    sources_list = sources
                
                if sources_list:
                    ai_response_content += "\n\n**📚 Sources:**\n"
                    for i, source in enumerate(sources_list[:5], 1):
                        if isinstance(source, dict):
                            title = source.get('title', 'Source inconnue')
                            url = source.get('url', '')
                            snippet = source.get('snippet', '')
                            if url:
                                ai_response_content += f"{i}. [{title}]({url})\n"
                            else:
                                ai_response_content += f"{i}. {title}\n"
                            if snippet:
                                ai_response_content += f"   *{snippet[:100]}...*\n"
                        else:
                            # Handle string sources
                            ai_response_content += f"{i}. {source}\n"
            else:
                # Fallback response for QA
                ai_response_content = f"**Réponse à votre question:**\n\n"
                if "qu'est-ce que" in message_data.content.lower() or "qu'est ce que" in message_data.content.lower():
                    ai_response_content += f"Basé sur votre question, je peux vous fournir une explication générale. Pour une réponse plus précise, le modèle de question-réponse est en cours de chargement.\n\n"
                    ai_response_content += "**Suggestion:** Essayez de reformuler votre question ou utilisez le mode 'Général' pour une réponse plus détaillée."
                elif "explique" in message_data.content.lower() or "expliquer" in message_data.content.lower():
                    ai_response_content += f"Je comprends que vous souhaitez une explication. Le modèle spécialisé est en cours de chargement.\n\n"
                    ai_response_content += "En attendant, voici une réponse générale basée sur votre demande."
                else:
                    ai_response_content += f"Je traite votre question. Le modèle de question-réponse est en cours de chargement depuis Hugging Face.\n\n"
                    ai_response_content += "**Note:** Le premier chargement peut prendre quelques minutes. Les prochaines questions seront plus rapides."
        
        elif message_data.module_type == "reformulation":
            # Extract style from metadata if provided, default to "academic"
            style = "academic"
            if message_data.metadata and "style" in message_data.metadata:
                style = message_data.metadata["style"]
            
            # Get selected model from metadata if provided
            selected_model = None
            if message_data.metadata and "model" in message_data.metadata:
                selected_model = message_data.metadata["model"]
            
            # Try Ollama first if available, otherwise use reformulation service
            result = None
            used_ollama_reform = False
            if ollama_service and ollama_service.is_available():
                try:
                    result = ollama_service.reformulate_text_sync(message_data.content, style, model=selected_model)
                    if result and not result.get('changes', {}).get('error'):
                        used_ollama_reform = True
                        logger.debug(f"Using Ollama ({result.get('changes', {}).get('model', 'unknown')}) for reformulation")
                except Exception as e:
                    logger.warning(f"Ollama reformulation error: {e}, falling back to reformulation service", exc_info=e)
            
            # Fallback to reformulation service if Ollama failed or not available
            if not result or result.get('changes', {}).get('error'):
                result = reformulation_service.reformulate_text(message_data.content, style)
                used_ollama_reform = False
                logger.debug("Using reformulation service (T5) for reformulation")
                
                # Enhance T5 reformulation with Ollama if available
                if ollama_service and ollama_service.is_available():
                    try:
                        reformulated_text_temp = result.get('reformulated_text', message_data.content)
                        enhancement = ollama_service.enhance_reformulation_sync(
                            reformulated_text_temp,
                            message_data.content,
                            style,
                            model=selected_model  # Use selected model for enhancement
                        )
                        if enhancement and not enhancement.get('error') and enhancement.get('enhanced_reformulation'):
                            result['reformulated_text'] = enhancement['enhanced_reformulation']
                            logger.debug(f"Reformulation enhanced by Ollama ({enhancement.get('model', 'unknown')})")
                    except Exception as e:
                        logger.warning(f"Ollama reformulation enhancement error: {e}, using original reformulation")
            
            reformulated_text = result.get('reformulated_text', message_data.content)
            
            # Check if reformulation actually changed the text
            similarity = 0.0
            if result.get('changes') and 'similarity_estimate' in result['changes']:
                similarity = result['changes']['similarity_estimate']
            else:
                # Quick similarity check
                original_words = set(message_data.content.lower().split())
                reformulated_words = set(reformulated_text.lower().split())
                if original_words and reformulated_words:
                    intersection = original_words.intersection(reformulated_words)
                    union = original_words.union(reformulated_words)
                    similarity = len(intersection) / len(union) if union else 1.0
            
            # Only show reformulated text if it's actually different
            if reformulated_text != message_data.content and similarity < 0.90:
                style_name = result.get('changes', {}).get('style', style)
                ai_response_content = f"**Texte reformulé ({style_name}):**\n\n{reformulated_text}\n\n"
                
                if result.get('changes'):
                    changes_info = result['changes']
                    if 'word_count_change' in changes_info:
                        word_change = changes_info['word_count_change']
                        if word_change != 0:
                            ai_response_content += f"*Modification: {abs(word_change)} mot(s) {'ajouté(s)' if word_change > 0 else 'retiré(s)'}*\n"
            else:
                # If reformulation didn't work well, try one more time with aggressive mode
                if ollama_service and ollama_service.is_available():
                    try:
                        # Try with more aggressive parameters
                        aggressive_result = ollama_service.reformulate_text_sync(
                            message_data.content, 
                            style="paraphrase" if style == "academic" else style
                        )
                        if aggressive_result.get('reformulated_text') and aggressive_result['reformulated_text'] != message_data.content:
                            ai_response_content = f"**Texte reformulé ({style}):**\n\n{aggressive_result['reformulated_text']}\n\n"
                        else:
                            # Last resort: show original with explanation
                            ai_response_content = f"**Texte original:**\n{message_data.content}\n\n"
                            ai_response_content += "*Note: La reformulation n'a pas apporté de changements significatifs. Le texte est déjà dans un style approprié.*"
                    except:
                        ai_response_content = f"**Texte original:**\n{message_data.content}\n\n"
                        ai_response_content += "*Note: La reformulation n'a pas apporté de changements significatifs.*"
                else:
                    ai_response_content = f"**Texte original:**\n{message_data.content}\n\n"
                    ai_response_content += "*Note: La reformulation n'a pas apporté de changements significatifs. Essayez d'utiliser Ollama avec Mistral pour de meilleurs résultats.*"
        
        else:  # general
            # Classify question type for better handling
            question_type = is_conversational_question(message_data.content)
            if question_type:
                question_type = "conversational"
            else:
                # Determine if it's an academic question
                text_lower = message_data.content.lower()
                academic_patterns = [
                    "qu'est-ce que", "qu'est ce que", "qu'est", "comment", "pourquoi", 
                    "explique", "expliquer", "définir", "définition", "signifie", 
                    "veut dire", "c'est quoi", "qu'est-ce", "décris", "décrire"
                ]
                if any(pattern in text_lower for pattern in academic_patterns) and len(message_data.content) > 15:
                    question_type = "academic"
                else:
                    question_type = "general"
            
            # Check for scientific writing assistance requests
            scientific_writing_keywords = [
                "aide-moi à écrire", "aide moi à écrire", "aide pour écrire",
                "comment écrire", "style scientifique", "rédaction scientifique",
                "améliore mon texte", "améliore ce texte", "corrige mon texte scientifique",
                "écris dans le style de", "écris comme dans", "style de mes documents"
            ]
            is_scientific_writing_request = any(
                keyword in message_data.content.lower() 
                for keyword in scientific_writing_keywords
            )
            
            # Check for conversational questions first (before trying QA)
            if is_greeting(message_data.content):
                ai_response_content = get_greeting_response()
            elif question_type == "conversational":
                ai_response_content = get_conversational_response(message_data.content)
            elif is_scientific_writing_request:
                # Provide scientific writing assistance based on uploaded documents
                has_docs = rag_service.has_documents(user_id=current_user.id)
                if has_docs:
                    # Extract the text to improve (if provided)
                    user_text = message_data.content
                    # Try to extract text after keywords
                    for keyword in scientific_writing_keywords:
                        if keyword in user_text.lower():
                            parts = user_text.lower().split(keyword, 1)
                            if len(parts) > 1 and parts[1].strip():
                                user_text = parts[1].strip()
                            break
                    
                    writing_assistance = rag_service.assist_scientific_writing(user_text, user_id=current_user.id)
                    
                    if writing_assistance.get("available"):
                        ai_response_content = "**Aide à la rédaction scientifique**\n\n"
                        ai_response_content += "Basé sur vos documents uploadés, voici des suggestions pour améliorer votre texte:\n\n"
                        
                        if writing_assistance.get("style_examples"):
                            ai_response_content += "**Exemples de style de vos documents:**\n"
                            for i, example in enumerate(writing_assistance["style_examples"][:2], 1):
                                ai_response_content += f"{i}. *{example['example']}*\n"
                                ai_response_content += f"   (Source: {example['source']})\n\n"
                        
                        if writing_assistance.get("terminology"):
                            ai_response_content += f"**Terminologie utilisée dans vos documents:** {', '.join(writing_assistance['terminology'][:10])}\n\n"
                        
                        if writing_assistance.get("writing_patterns"):
                            ai_response_content += "**Modèles de phrases académiques:**\n"
                            for pattern in writing_assistance["writing_patterns"][:3]:
                                ai_response_content += f"• {pattern}\n"
                            ai_response_content += "\n"
                        
                        if writing_assistance.get("suggestions"):
                            ai_response_content += "**Suggestions:**\n"
                            for suggestion in writing_assistance["suggestions"]:
                                ai_response_content += f"• {suggestion}\n"
                    else:
                        ai_response_content = "Je peux vous aider avec la rédaction scientifique, mais vous devez d'abord uploader des documents de référence dans le chat.\n\n"
                        ai_response_content += "Une fois vos documents uploadés, je pourrai vous fournir des suggestions de style basées sur ces documents."
                else:
                    ai_response_content = "Pour vous aider avec la rédaction scientifique, veuillez d'abord uploader un ou plusieurs documents de référence dans le chat.\n\n"
                    ai_response_content += "Ces documents serviront de base pour adapter le style de vos écrits."
            else:
                # Always check if documents are available first
                has_docs = rag_service.has_documents(user_id=current_user.id)
                
                # Try RAG + QA for academic questions, or if documents are available
                should_try_qa = (
                    question_type in ["academic", "definition", "explanation"] or
                    len(message_data.content.strip()) > 15 or  # Lower threshold
                    has_docs  # Always try if documents exist
                )
                
                if should_try_qa:
                    # Always try RAG first if documents exist, otherwise use general context
                    rag_results = []
                    if has_docs:
                        try:
                            # Get user document IDs
                            from app.models import Document
                            user_docs = db.query(Document).filter(
                                Document.user_id == current_user.id,
                                Document.processed == True
                            ).all()
                            user_document_ids = [str(doc.id) for doc in user_docs]
                            
                            rag_results = rag_service.search(
                                query=message_data.content,
                                user_documents=user_document_ids,
                                top_k=6
                            )
                        except Exception as e:
                            logger.warning(f"RAG search failed: {e}")
                            rag_results = []
                    
                    context = None
                    sources = []
                    
                    if rag_results:
                        # Use enhanced context with scores - prioritize high-scoring results
                        context_parts = []
                        high_score_results = [r for r in rag_results if r.get("score", 0) > 0.5]
                        
                        # Use high-scoring results first, then top results
                        if high_score_results:
                            for r in high_score_results[:5]:  # Use top 5 high-scoring
                                text = r.get("text", "") or r.get("content", "")
                                if text:
                                    context_parts.append(text)
                                # Extract source information
                                source = r.get("source", "")
                                title = r.get("title", "")
                                if source or title:
                                    sources.append(title if title else source)
                        else:
                            # Fallback to top results by score
                            for r in rag_results[:5]:  # Use top 5
                                if r.get("score", 0) >= 0.3:  # Lower threshold for more context
                                    text = r.get("text", "") or r.get("content", "")
                                    if text:
                                        context_parts.append(text)
                                    # Extract source information
                                    source = r.get("source", "")
                                    title = r.get("title", "")
                                    if source or title:
                                        sources.append(title if title else source)
                        
                        if context_parts:
                            context = "\n\n".join(context_parts)
                    
                    # Try Ollama first if available, otherwise fallback to QA service
                    result = None
                    used_ollama = False
                    selected_model = None
                    if message_data.metadata and "model" in message_data.metadata:
                        selected_model = message_data.metadata["model"]
                    
                    if ollama_service and ollama_service.is_available():
                        try:
                            result = ollama_service.answer_question_sync(
                                message_data.content, 
                                context,
                                model=selected_model  # Use selected model if provided
                            )
                            if result and not result.get('error'):
                                used_ollama = True
                                logger.debug(f"Using Ollama ({result.get('model', 'unknown')}) for question answering")
                        except Exception as e:
                            logger.warning(f"Ollama error: {e}, falling back to QA service", exc_info=e)
                    
                    # Fallback to QA service if Ollama failed or not available
                    if not result or result.get('error'):
                        result = qa_service.answer_question(message_data.content, context)
                        used_ollama = False
                        logger.debug("Using QA service (Camembert) for question answering")
                    
                    # Store confidence and model info for later use
                    confidence_value = result.get('confidence', 0.0)
                    model_name = result.get('model') if used_ollama else None
                    
                    if result.get('answer') and result['confidence'] > 0.15 and "n'est pas disponible" not in result['answer'] and "Erreur" not in result['answer']:
                        # Format comprehensive answer (remove text confidence indicator, will use visual component)
                        ai_response_content = f"**Réponse:**\n\n{result['answer']}\n\n"
                        
                        # Add sources if available
                        if sources:
                            unique_sources = list(set(sources))[:3]
                            ai_response_content += f"**Sources:** {', '.join(unique_sources)}\n\n"
                        elif result.get('sources'):
                            ai_response_content += f"**Sources:** {', '.join(result['sources'][:2])}\n\n"
                        
                        # Add helpful follow-up if confidence is moderate
                        if 0.3 <= result.get('confidence', 0) < 0.7:
                            ai_response_content += "*💡 Pour une réponse plus précise, vous pouvez uploader des documents pertinents ou reformuler votre question.*"
                    else:
                        # Enhanced fallback with better context
                        if has_docs:
                            ai_response_content = f"**Réponse basée sur vos documents:**\n\n"
                            if rag_results:
                                # Use best matching context as answer
                                best_result = rag_results[0]
                                ai_response_content += f"{best_result['content'][:300]}...\n\n"
                                ai_response_content += f"*Source: {best_result.get('metadata', {}).get('source', 'Document')}*\n\n"
                                ai_response_content += "*Note: Pour une réponse plus précise, essayez de reformuler votre question ou utilisez le mode 'Questions' (QA).*"
                            else:
                                ai_response_content += "Je n'ai pas trouvé de contexte directement pertinent dans vos documents pour cette question.\n\n"
                                ai_response_content += "*Suggestion: Reformulez votre question ou uploader des documents plus pertinents.*"
                        else:
                            # If QA didn't work well and no docs, give a helpful conversational response
                            ai_response_content = get_conversational_response(message_data.content)
                            ai_response_content += "\n\n*💡 Astuce: Uploader des documents pertinents peut améliorer la qualité de mes réponses.*"
                else:
                    # For short or non-academic messages, give a conversational response
                    ai_response_content = get_conversational_response(message_data.content)
    
    except Exception as e:
        print(f"Error generating response: {e}")
        import traceback
        traceback.print_exc()
        # Provide a helpful fallback response
        if is_greeting(message_data.content):
            ai_response_content = get_greeting_response()
        elif is_conversational_question(message_data.content):
            ai_response_content = get_conversational_response(message_data.content)
        else:
            ai_response_content = f"**Réponse:**\n\nJe traite votre demande. Une erreur s'est produite: {str(e)}\n\n"
            ai_response_content += "Veuillez réessayer ou sélectionner un autre mode."
    
    # Prepare metadata with confidence, sources, and model info
    message_metadata = {}
    if 'confidence_value' in locals() and confidence_value > 0:
        message_metadata['confidence'] = confidence_value
    if 'sources' in locals() and sources:
        message_metadata['sources'] = sources[:5]  # Store up to 5 sources
    
    # Track which model was used
    if message_data.module_type == "ollama":
        # Ollama AI mode always uses Ollama
        message_metadata['model'] = 'Ollama/Mistral'
        message_metadata['model_type'] = 'ollama'
    elif message_data.module_type == "qa":
        if 'model_name' in locals() and model_name:
            # Model name from Ollama result (primary)
            message_metadata['model'] = model_name if isinstance(model_name, str) else str(model_name)
            message_metadata['model_type'] = 'ollama'
        elif 'used_ollama' in locals() and used_ollama:
            message_metadata['model'] = 'Ollama/Mistral'
            message_metadata['model_type'] = 'ollama'
        else:
            message_metadata['model'] = 'Camembert (Hugging Face)'
            message_metadata['model_type'] = 'huggingface'
            # Check if Ollama enhanced the response
            if 'used_ollama_enhancement' in locals() and used_ollama_enhancement:
                message_metadata['enhanced_by'] = ollama_enhancement_model if 'ollama_enhancement_model' in locals() and ollama_enhancement_model else 'Ollama/Mistral'
                message_metadata['enhancement_type'] = 'ollama'
    elif message_data.module_type == "reformulation":
        if 'used_ollama_reform' in locals() and used_ollama_reform and 'result' in locals() and result:
            model_from_result = result.get('changes', {}).get('model')
            if model_from_result:
                message_metadata['model'] = model_from_result
            else:
                message_metadata['model'] = 'Ollama/Mistral'
            message_metadata['model_type'] = 'ollama'
        else:
            message_metadata['model'] = 'T5 (Hugging Face)'
            message_metadata['model_type'] = 'huggingface'
            # Check if Ollama enhanced the reformulation
            if 'reformulation_enhanced' in locals() and reformulation_enhanced and reformulation_enhancement_model:
                message_metadata['enhanced_by'] = reformulation_enhancement_model
                message_metadata['enhancement_type'] = 'ollama'
    elif message_data.module_type == "grammar":
        message_metadata['model'] = 'LanguageTool'
        message_metadata['model_type'] = 'languagetool'
        # Check if Ollama enhanced the grammar correction
        if 'ollama_enhanced' in locals() and ollama_enhanced:
            message_metadata['enhanced_by'] = ollama_model_name if 'ollama_model_name' in locals() and ollama_model_name else 'Ollama/Mistral'
            message_metadata['enhancement_type'] = 'ollama'
    
    # Save AI response
    ai_message = Message(
        session_id=session_id,
        role="assistant",
        content=ai_response_content,
        module_type=message_data.module_type,
        message_metadata=json.dumps(message_metadata) if message_metadata else None
    )
    db.add(ai_message)
    
    # Update session timestamp
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ai_message)
    
    return MessageResponse(
        id=ai_message.id,
        role=ai_message.role,
        content=ai_message.content,
        module_type=ai_message.module_type,
        created_at=ai_message.created_at,
        metadata=message_metadata if message_metadata else None
    )


async def generate_ai_response_stream(
    message_data: MessageCreate,
    session_id: int,
    current_user: User,
    db: Session
) -> AsyncGenerator[dict, None]:
    """Génère une réponse AI en streaming"""
    
    # Helper functions (réutilisées depuis create_message)
    def is_greeting(text: str) -> bool:
        greetings = [
            "bonjour", "bonsoir", "salut", "hello", "hi", "hey",
            "bonne journée", "bonne soirée", "bon matin",
            "comment allez-vous", "comment ça va", "ça va",
            "comment vas-tu", "comment allez vous"
        ]
        text_lower = text.lower().strip()
        return any(greeting in text_lower for greeting in greetings)
    
    def get_greeting_response() -> str:
        responses = [
            "Bonjour ! Je suis votre assistant académique AI. Comment puis-je vous aider aujourd'hui ?",
            "Bonjour ! Je suis là pour vous aider avec la correction grammaticale, les questions-réponses académiques, et la reformulation de textes. Que souhaitez-vous faire ?",
            "Salut ! Je suis votre assistant académique. Je peux vous aider à corriger votre français, répondre à vos questions, ou reformuler vos textes. Par quoi commençons-nous ?"
        ]
        import random
        return random.choice(responses)
    
    def is_conversational_question(text: str) -> bool:
        conversational_patterns = [
            "vous pouvez", "tu peux", "pouvez-vous", "peux-tu",
            "vous pouvez m'aider", "tu peux m'aider", "pouvez vous m'aider",
            "aidez-moi", "aide-moi", "aide moi",
            "comment faire", "comment puis-je", "comment je peux",
            "qu'est-ce que tu", "qu'est-ce que vous",
            "qui es-tu", "qui êtes-vous", "c'est quoi",
            "ça marche", "ça fonctionne", "comment ça marche",
            "merci", "de rien", "pas de problème"
        ]
        text_lower = text.lower().strip()
        if len(text) < 50:
            return any(pattern in text_lower for pattern in conversational_patterns)
        return False
    
    def get_conversational_response(text: str) -> str:
        text_lower = text.lower().strip()
        
        if any(word in text_lower for word in ["vous pouvez", "tu peux", "pouvez-vous", "peux-tu", "aider", "aide"]):
            return """Bien sûr ! Je suis votre assistant académique AI et je suis là pour vous aider. 

Je peux vous assister avec :
• **Correction grammaticale** : Corrigez vos textes en français
• **Questions académiques** : Répondez à vos questions scientifiques et académiques
• **Reformulation** : Reformulez vos textes dans un style académique
• **Rédaction scientifique** : Aidez-vous à écrire dans le style de vos documents de référence

Quelle est votre question ou votre demande ?"""
        elif any(word in text_lower for word in ["merci", "thanks", "thank you"]):
            return """Je vous en prie ! C'est un plaisir de vous aider. 

N'hésitez pas si vous avez d'autres questions. Je suis toujours disponible pour vous assister dans vos travaux académiques."""
        else:
            return """Je comprends. Je suis là pour vous aider avec vos travaux académiques.

**Que puis-je faire pour vous ?**
• Corriger un texte
• Répondre à une question académique
• Reformuler un texte
• Vous aider à écrire dans un style scientifique
• Traiter un document

Quelle est votre demande ?"""
    
    try:
        # Générer la réponse complète d'abord
        ai_response_content = ""
        
        # Handle greetings
        if message_data.module_type == "general" and is_greeting(message_data.content):
            ai_response_content = get_greeting_response()
        
        elif message_data.module_type == "ollama":
            # Ollama AI mode - use Ollama for all operations (streaming version)
            selected_model = None
            if message_data.metadata and "model" in message_data.metadata:
                selected_model = message_data.metadata["model"]
            
            if not ollama_service or not ollama_service.is_available():
                ai_response_content = "⚠️ **Ollama n'est pas disponible.**\n\n"
                ai_response_content += "Pour utiliser le mode Ollama AI:\n"
                ai_response_content += "1. Installez Ollama depuis https://ollama.ai\n"
                ai_response_content += "2. Exécutez `ollama pull mistral`\n"
                ai_response_content += "3. Assurez-vous qu'Ollama est en cours d'exécution\n\n"
                ai_response_content += "En attendant, je peux vous aider avec les autres modes disponibles."
            else:
                # Use Ollama for all operations based on content analysis
                text_lower = message_data.content.lower()
                
                # Detect if it's a question
                is_question = any(word in text_lower for word in ["qu'est", "comment", "pourquoi", "explique", "définir", "qu'est-ce", "?"])
                
                # Detect if it's grammar correction
                is_grammar = any(word in text_lower for word in ["corrige", "correction", "grammaire", "orthographe", "fautes"])
                
                # Detect if it's reformulation request
                is_reformulation = any(word in text_lower for word in ["reformule", "réécris", "paraphrase", "améliore", "style"])
                
                if is_question:
                    # Use Ollama for QA
                    context = None
                    try:
                        # Get user document IDs
                        from app.models import Document
                        user_docs = db.query(Document).filter(
                            Document.user_id == current_user.id,
                            Document.processed == True
                        ).all()
                        user_document_ids = [str(doc.id) for doc in user_docs]
                        
                        rag_results = rag_service.search(
                            query=message_data.content,
                            user_documents=user_document_ids,
                            top_k=4
                        )
                    except Exception as e:
                        logger.warning(f"RAG search failed: {e}")
                        rag_results = []
                    if rag_results:
                        context = "\n\n".join([r.get("text", "") or r.get("content", "") for r in rag_results[:3] if r.get("text") or r.get("content")])
                    
                    result = ollama_service.answer_question_sync(message_data.content, context, model=selected_model)
                    if result and not result.get('error'):
                        ai_response_content = f"**Réponse:**\n\n{result['answer']}\n\n"
                        if result.get('confidence', 0) > 0:
                            confidence = result['confidence']
                            if confidence > 0.75:
                                confidence_label = "très élevée"
                            elif confidence > 0.60:
                                confidence_label = "élevée"
                            elif confidence > 0.45:
                                confidence_label = "modérée"
                            else:
                                confidence_label = "acceptable"
                            ai_response_content += f"*Niveau de confiance: {confidence_label} ({confidence:.0%})*\n"
                    else:
                        ai_response_content = result.get('answer', 'Erreur lors de la génération de la réponse.')
                
                elif is_grammar:
                    # Use Ollama for grammar correction
                    system_prompt = (
                        "Tu es un expert en grammaire et orthographe française. "
                        "Corrige le texte suivant en identifiant et corrigeant toutes les erreurs grammaticales, "
                        "orthographiques et de style. Retourne le texte corrigé avec des explications brèves pour chaque correction."
                    )
                    result = ollama_service.generate_response_sync(
                        prompt=f"Corrige ce texte: {message_data.content}",
                        model=selected_model,
                        system_prompt=system_prompt,
                        temperature=0.2,
                        max_tokens=2000
                    )
                    if result and not result.get('error'):
                        ai_response_content = f"✅ **Texte corrigé:**\n\n{result.get('response', message_data.content)}\n\n"
                    else:
                        ai_response_content = "Erreur lors de la correction grammaticale."
                
                elif is_reformulation:
                    # Use Ollama for reformulation
                    style = "academic"  # Default style
                    if message_data.metadata and "style" in message_data.metadata:
                        style = message_data.metadata["style"]
                    
                    result = ollama_service.reformulate_text_sync(message_data.content, style, model=selected_model)
                    if result and not result.get('changes', {}).get('error'):
                        reformulated = result.get('reformulated_text', message_data.content)
                        ai_response_content = f"**Texte reformulé ({style}):**\n\n{reformulated}\n\n"
                    else:
                        ai_response_content = "Erreur lors de la reformulation."
                
                else:
                    # General conversation with Ollama
                    if is_greeting(message_data.content):
                        ai_response_content = get_greeting_response()
                    else:
                        system_prompt = (
                            "Tu es un assistant académique français intelligent et serviable. "
                            "Réponds de manière précise, structurée et académique. "
                            "Utilise un langage clair et professionnel."
                        )
                        result = ollama_service.generate_response_sync(
                            prompt=message_data.content,
                            model=selected_model,
                            system_prompt=system_prompt,
                            temperature=0.7,
                            max_tokens=2000
                        )
                        if result and not result.get('error'):
                            ai_response_content = result.get('response', 'Erreur lors de la génération de la réponse.')
                        else:
                            ai_response_content = "Erreur lors de la génération de la réponse."
        
        elif message_data.module_type == "grammar":
            # First check for incomplete/misspelled greetings
            corrected_greeting, is_greeting_detected = detect_and_fix_incomplete_greeting(message_data.content)
            
            if is_greeting_detected and corrected_greeting != message_data.content:
                # Provide helpful correction for incomplete greeting
                ai_response_content = f"✅ **Correction détectée:**\n\n"
                ai_response_content += f"**Texte original:** {message_data.content}\n"
                ai_response_content += f"**Texte corrigé:** {corrected_greeting}\n\n"
                ai_response_content += f"💡 **Explication:** Il semble que vous vouliez dire \"{corrected_greeting}\". "
                ai_response_content += "J'ai corrigé votre message. "
                ai_response_content += f"{get_greeting_response()}"
            else:
                # Use grammar service for normal grammar correction
                result = grammar_service.correct_text(message_data.content)
                corrected_text = result.get('corrected_text', message_data.content)
                corrections = result.get('corrections', [])
                
                # Enhance with Ollama if available
                ollama_enhanced = False
                ollama_model_name = None
                selected_model_enhance = None
                if message_data.metadata and "model" in message_data.metadata:
                    selected_model_enhance = message_data.metadata["model"]
                
                if ollama_service and ollama_service.is_available() and corrected_text:
                    try:
                        enhancement = ollama_service.enhance_grammar_correction_sync(
                            corrected_text,
                            message_data.content,
                            corrections,
                            model=selected_model_enhance  # Use selected model for enhancement
                        )
                        if enhancement and not enhancement.get('error') and enhancement.get('enhanced_corrected_text'):
                            corrected_text = enhancement['enhanced_corrected_text']
                            ollama_enhanced = True
                            ollama_model_name = enhancement.get('model', 'Ollama/Mistral')
                            if enhancement.get('additional_corrections'):
                                corrections.extend([{"original": "", "corrected": "", "explanation": imp} 
                                                   for imp in enhancement['additional_corrections']])
                            logger.debug(f"Grammar correction enhanced by Ollama ({ollama_model_name})")
                    except Exception as e:
                        logger.warning(f"Ollama grammar enhancement error: {e}, using original correction")
                
                if corrections:
                    ai_response_content = f"✅ **Texte corrigé:**\n\n{corrected_text}\n\n"
                    ai_response_content += "**Corrections apportées:**\n"
                    for corr in corrections:
                        if corr.get('original') and corr.get('corrected'):
                            ai_response_content += f"• {corr['original']} → **{corr['corrected']}**\n  *{corr['explanation']}*\n"
                        elif corr.get('explanation'):
                            ai_response_content += f"• {corr['explanation']}\n"
                else:
                    ai_response_content = f"✅ Votre texte semble correct!\n\n{corrected_text}"
        
        elif message_data.module_type == "plan":
            # Extract plan type and structure from metadata
            plan_type = message_data.metadata.get("plan_type", "academic") if message_data.metadata else "academic"
            structure = message_data.metadata.get("structure", "classic") if message_data.metadata else "classic"
            
            # Get selected model from metadata if provided
            selected_model = None
            if message_data.metadata and "model" in message_data.metadata:
                selected_model = message_data.metadata["model"]
            
            # Try Ollama first if available for better plan generation
            result = None
            used_ollama_plan = False
            if ollama_service and ollama_service.is_available():
                try:
                    # Use Ollama to generate a plan
                    prompt = f"""Génère un plan détaillé pour un essai académique en français.

Sujet: {message_data.content}
Type de plan: {plan_type}
Structure: {structure}

Génère un plan structuré avec:
- Introduction (accroche, problématique, annonce du plan)
- Développement (2-3 parties principales avec sous-parties détaillées)
- Conclusion (synthèse, ouverture)

Format le plan de manière claire et structurée."""
                    
                    ollama_result = ollama_service.generate_response_sync(prompt, model=selected_model)
                    if ollama_result and not ollama_result.get('error'):
                        used_ollama_plan = True
                        plan_text = ollama_result.get('response', '')
                        result = {
                            "topic": message_data.content,
                            "plan_type": plan_type,
                            "structure": structure,
                            "full_plan": plan_text,
                            "model": ollama_result.get('model', selected_model or 'ollama')
                        }
                        logger.debug(f"Using Ollama ({result.get('model', 'unknown')}) for plan generation")
                except Exception as e:
                    logger.warning(f"Ollama plan generation error: {e}, falling back to plan service", exc_info=e)
            
            # Fallback to plan service if Ollama failed or not available
            if not result or result.get('error'):
                result = plan_service.generate_plan(message_data.content, plan_type=plan_type, structure=structure)
                logger.debug("Using plan service (BART) for plan generation")
                
                # Enhance plan with Ollama if available
                if ollama_service and ollama_service.is_available() and not used_ollama_plan:
                    try:
                        enhancement_prompt = f"""Améliore et enrichis ce plan d'essai académique en français. Ajoute plus de détails et de structure.

Plan actuel:
{result.get('full_plan', '')}

Génère un plan amélioré avec plus de détails pour chaque section."""
                        
                        enhancement = ollama_service.generate_response_sync(enhancement_prompt, model=selected_model)
                        if enhancement and not enhancement.get('error'):
                            enhanced_plan = enhancement.get('response', '')
                            result['full_plan'] = enhanced_plan
                            result['enhanced_by'] = enhancement.get('model', selected_model or 'ollama')
                            result['enhancement_type'] = 'plan_improvement'
                            logger.debug(f"Plan enhanced by Ollama ({result.get('enhanced_by', 'unknown')})")
                    except Exception as e:
                        logger.warning(f"Ollama plan enhancement error: {e}, using original plan", exc_info=e)
            
            # Format the response
            if result and not result.get('error'):
                ai_response_content = f"# 📋 Plan d'Essai\n\n"
                ai_response_content += f"**Sujet:** {result.get('topic', message_data.content)}\n\n"
                ai_response_content += f"**Type:** {result.get('plan_type', plan_type).title()}\n"
                ai_response_content += f"**Structure:** {result.get('structure', structure).title()}\n\n"
                ai_response_content += "---\n\n"
                ai_response_content += result.get('full_plan', '')
                
                if result.get('enhanced_by'):
                    ai_response_content += f"\n\n---\n\n*✨ Plan amélioré par {result.get('enhanced_by', 'Ollama')}*"
            else:
                ai_response_content = f"❌ Erreur lors de la génération du plan. Veuillez réessayer."
        
        elif message_data.module_type == "summarization":
            # Extract length style from metadata if provided, default to "medium"
            length_style = "medium"
            if message_data.metadata and "length_style" in message_data.metadata:
                length_style = message_data.metadata["length_style"]
            
            # Get selected model from metadata if provided
            selected_model = None
            if message_data.metadata and "model" in message_data.metadata:
                selected_model = message_data.metadata["model"]
            
            # Try Ollama first if available, otherwise use summarization service
            result = None
            used_ollama_summary = False
            if ollama_service and ollama_service.is_available():
                try:
                    result = ollama_service.summarize_text_sync(message_data.content, length_style, model=selected_model)
                    if result and not result.get('error'):
                        used_ollama_summary = True
                        logger.debug(f"Using Ollama ({result.get('model', 'unknown')}) for summarization")
                except Exception as e:
                    logger.warning(f"Ollama summarization error: {e}, falling back to summarization service", exc_info=e)
            
            # Fallback to summarization service if Ollama failed or not available
            if not result or result.get('error'):
                result = summarization_service.summarize_text(message_data.content, length_style=length_style)
                used_ollama_summary = False
                logger.debug("Using summarization service (T5) for summarization")
                
                # Enhance T5 summarization with Ollama if available
                if ollama_service and ollama_service.is_available():
                    try:
                        summary_temp = result.get('summary', message_data.content)
                        enhancement = ollama_service.enhance_summarization_sync(
                            summary_temp,
                            message_data.content,
                            length_style,
                            model=selected_model  # Use selected model for enhancement
                        )
                        if enhancement and not enhancement.get('error') and enhancement.get('enhanced_summary'):
                            result['summary'] = enhancement['enhanced_summary']
                            logger.debug(f"Summarization enhanced by Ollama ({enhancement.get('model', 'unknown')})")
                    except Exception as e:
                        logger.warning(f"Ollama summarization enhancement error: {e}, using original summary")
            
            summary = result.get('summary', message_data.content)
            original_length = result.get('original_length', len(message_data.content))
            summary_length = result.get('summary_length', len(summary))
            compression_ratio = result.get('compression_ratio', 1.0)
            
            length_style_names = {
                "short": "Court",
                "medium": "Moyen",
                "long": "Long",
                "detailed": "Détaillé"
            }
            style_name = length_style_names.get(length_style, length_style)
            
            ai_response_content = f"**Résumé ({style_name}):**\n\n{summary}\n\n"
            ai_response_content += f"**Statistiques:**\n"
            ai_response_content += f"• Longueur originale: {original_length} caractères\n"
            ai_response_content += f"• Longueur du résumé: {summary_length} caractères\n"
            ai_response_content += f"• Ratio de compression: {compression_ratio:.1%}\n"
            
            if result.get('key_points'):
                ai_response_content += f"\n**Points clés:**\n"
                for point in result['key_points'][:5]:
                    ai_response_content += f"• {point}\n"
        
        elif message_data.module_type == "qa":
            # Try RAG first - use search method
            try:
                # Get user document IDs if available
                user_document_ids = None
                if current_user:
                    from app.models import Document
                    user_docs = db.query(Document).filter(
                        Document.user_id == current_user.id,
                        Document.processed == True
                    ).all()
                    user_document_ids = [str(doc.id) for doc in user_docs]
                
                rag_results = rag_service.search(
                    query=message_data.content,
                    user_documents=user_document_ids,
                    top_k=6
                )
            except Exception as e:
                logger.warning(f"RAG search failed in stream: {e}")
                rag_results = []
            context = None
            sources = []
            
            if rag_results:
                context_parts = []
                high_score_results = [r for r in rag_results if r.get("score", 0) > 0.5]
                
                if high_score_results:
                    for r in high_score_results[:4]:
                        # RAG search returns 'text' or 'content' field
                        text = r.get("text") or r.get("content", "")
                        if text:
                            context_parts.append(text)
                        # Extract source information
                        source = r.get("source", "")
                        title = r.get("title", "")
                        if source or title:
                            sources.append(title if title else source)
                else:
                    for r in rag_results[:4]:
                        # RAG search returns 'text' or 'content' field
                        text = r.get("text") or r.get("content", "")
                        if text:
                            context_parts.append(text)
                        # Extract source information
                        source = r.get("source", "")
                        title = r.get("title", "")
                        if source or title:
                            sources.append(title if title else source)
                
                if context_parts:
                    context = "\n\n".join(context_parts)
            
            result = qa_service.answer_question(message_data.content, context)
            
            if result.get('answer') and result['answer'] != "Désolé, le modèle de question-réponse n'est pas disponible pour le moment.":
                answer = result['answer']
                used_ollama_enhancement = False
                ollama_enhancement_model = None
                
                # Enhance with Ollama if available
                selected_model_enhance = None
                if message_data.metadata and "model" in message_data.metadata:
                    selected_model_enhance = message_data.metadata["model"]
                
                if ollama_service and ollama_service.is_available():
                    try:
                        enhancement = ollama_service.enhance_qa_response_sync(
                            answer,
                            message_data.content,
                            context,
                            model=selected_model_enhance  # Use selected model for enhancement
                        )
                        if enhancement and not enhancement.get('error') and enhancement.get('enhanced_answer'):
                            answer = enhancement['enhanced_answer']
                            used_ollama_enhancement = True
                            ollama_enhancement_model = enhancement.get('model', 'Ollama/Mistral')
                            logger.debug(f"QA response enhanced by Ollama ({ollama_enhancement_model})")
                    except Exception as e:
                        logger.warning(f"Ollama QA enhancement error: {e}, using original answer")
                
                ai_response_content = f"**Réponse:**\n\n{answer}\n\n"
                if result.get('confidence', 0) > 0:
                    confidence = result['confidence']
                    if confidence > 0.75:
                        confidence_label = "très élevée"
                    elif confidence > 0.60:
                        confidence_label = "élevée"
                    elif confidence > 0.45:
                        confidence_label = "modérée"
                    else:
                        confidence_label = "acceptable"
                    ai_response_content += f"*Niveau de confiance: {confidence_label} ({confidence:.0%})*\n"
                if sources:
                    unique_sources = list(set(sources))[:3]
                    ai_response_content += f"\n**Sources:** {', '.join(unique_sources)}"
                elif result.get('sources'):
                    ai_response_content += f"\n**Sources:** {', '.join(result['sources'][:2])}"
            else:
                ai_response_content = f"**Réponse à votre question:**\n\n"
                ai_response_content += "Le modèle de question-réponse est en cours de chargement. Veuillez réessayer dans quelques instants."
        
        elif message_data.module_type == "reformulation":
            # Extract style from metadata if provided, default to "academic"
            style = "academic"
            if message_data.metadata and "style" in message_data.metadata:
                style = message_data.metadata["style"]
            
            # Get selected model from metadata if provided
            selected_model = None
            if message_data.metadata and "model" in message_data.metadata:
                selected_model = message_data.metadata["model"]
            
            # Try Ollama first if available, otherwise use reformulation service
            result = None
            used_ollama_reform = False
            if ollama_service and ollama_service.is_available():
                try:
                    result = ollama_service.reformulate_text_sync(message_data.content, style, model=selected_model)
                    if result and not result.get('changes', {}).get('error'):
                        used_ollama_reform = True
                        logger.debug(f"Using Ollama ({result.get('changes', {}).get('model', 'unknown')}) for reformulation")
                except Exception as e:
                    logger.warning(f"Ollama reformulation error: {e}, falling back to reformulation service", exc_info=e)
            
            # Fallback to reformulation service if Ollama failed or not available
            if not result or result.get('changes', {}).get('error'):
                result = reformulation_service.reformulate_text(message_data.content, style)
                used_ollama_reform = False
                logger.debug("Using reformulation service (T5) for reformulation")
                
                # Enhance T5 reformulation with Ollama if available
                if ollama_service and ollama_service.is_available():
                    try:
                        reformulated_text_temp = result.get('reformulated_text', message_data.content)
                        enhancement = ollama_service.enhance_reformulation_sync(
                            reformulated_text_temp,
                            message_data.content,
                            style,
                            model=selected_model  # Use selected model for enhancement
                        )
                        if enhancement and not enhancement.get('error') and enhancement.get('enhanced_reformulation'):
                            result['reformulated_text'] = enhancement['enhanced_reformulation']
                            logger.debug(f"Reformulation enhanced by Ollama ({enhancement.get('model', 'unknown')})")
                    except Exception as e:
                        logger.warning(f"Ollama reformulation enhancement error: {e}, using original reformulation")
            
            reformulated_text = result.get('reformulated_text', message_data.content)
            ai_response_content = f"**Texte reformulé ({style}):**\n\n{reformulated_text}\n\n"
            if result.get('improvements'):
                ai_response_content += "**Améliorations apportées:**\n"
                for imp in result['improvements'][:5]:
                    ai_response_content += f"• {imp}\n"
        
        else:
            # General mode
            if is_greeting(message_data.content):
                ai_response_content = get_greeting_response()
            elif is_conversational_question(message_data.content):
                ai_response_content = get_conversational_response(message_data.content)
            else:
                # Try QA as fallback
                try:
                    # Get user document IDs
                    from app.models import Document
                    user_docs = db.query(Document).filter(
                        Document.user_id == current_user.id,
                        Document.processed == True
                    ).all()
                    user_document_ids = [str(doc.id) for doc in user_docs]
                    
                    rag_results = rag_service.search(
                        query=message_data.content,
                        user_documents=user_document_ids,
                        top_k=5
                    )
                    context = None
                    if rag_results:
                        context_parts = [r.get("text", "") or r.get("content", "") for r in rag_results[:3] if r.get("text") or r.get("content")]
                        context = "\n\n".join(context_parts)
                    
                    result = qa_service.answer_question(message_data.content, context)
                    confidence_value = result.get('confidence', 0.0)
                    
                    if result.get('answer') and result['confidence'] > 0.15:
                        ai_response_content = f"**Réponse:**\n\n{result['answer']}\n\n"
                    else:
                        ai_response_content = get_conversational_response(message_data.content)
                        confidence_value = 0.0
                except:
                    ai_response_content = get_conversational_response(message_data.content)
                    confidence_value = 0.0
        
        # Stream la réponse
        async for chunk in stream_text_progressive(ai_response_content, words_per_chunk=2, delay=0.02, character_by_character=True):
            yield chunk
        
        # Prepare metadata with confidence and model info
        message_metadata = {}
        if 'confidence_value' in locals() and confidence_value > 0:
            message_metadata['confidence'] = confidence_value
        
        # Track which model was used (streaming uses fallback services for now)
        if message_data.module_type == "ollama":
            # Ollama AI mode always uses Ollama
            message_metadata['model'] = 'Ollama/Mistral'
            message_metadata['model_type'] = 'ollama'
        elif message_data.module_type == "qa":
            message_metadata['model'] = 'Camembert (Hugging Face)'
            message_metadata['model_type'] = 'huggingface'
        elif message_data.module_type == "reformulation":
            message_metadata['model'] = 'T5 (Hugging Face)'
            message_metadata['model_type'] = 'huggingface'
        elif message_data.module_type == "grammar":
            message_metadata['model'] = 'LanguageTool'
            message_metadata['model_type'] = 'languagetool'
        elif message_data.module_type == "summarization":
            if 'used_ollama_summary' in locals() and used_ollama_summary:
                message_metadata['model'] = result.get('model', 'Ollama/Mistral') if 'result' in locals() and result else 'Ollama/Mistral'
                message_metadata['model_type'] = 'ollama'
            else:
                message_metadata['model'] = 'T5 (Hugging Face)'
                message_metadata['model_type'] = 'huggingface'
                # Check if Ollama enhanced the summary
                if 'enhancement' in locals() and enhancement and not enhancement.get('error'):
                    message_metadata['enhanced_by'] = enhancement.get('model', 'Ollama/Mistral')
                    message_metadata['enhancement_type'] = 'ollama'
        
        # Sauvegarder le message final dans la base de données
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        ).first()
        
        if session:
            ai_message = Message(
                session_id=session_id,
                role="assistant",
                content=ai_response_content,
                module_type=message_data.module_type,
                message_metadata=json.dumps(message_metadata) if message_metadata else None
            )
            db.add(ai_message)
            session.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(ai_message)
            
            # Envoyer l'ID du message final avec metadata
            yield {
                "type": "message_id",
                "message_id": ai_message.id,
                "metadata": message_metadata if message_metadata else None,
                "done": True
            }
    
    except Exception as e:
        logger.error("Error in generate_ai_response_stream", exc_info=e)
        error_text = f"Une erreur s'est produite: {str(e)}"
        async for chunk in stream_text_progressive(error_text, words_per_chunk=2, delay=0.03):
            yield chunk


@router.post("/sessions/{session_id}/messages/stream")
async def create_message_stream(
    session_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée un message et retourne la réponse AI en streaming (SSE).
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise AppException(
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            detail="Session introuvable."
        )
    
    # Sauvegarder le message utilisateur
    user_message = Message(
        session_id=session_id,
        role="user",
        content=message_data.content,
        module_type=message_data.module_type
    )
    db.add(user_message)
    db.commit()
    
    # Créer le générateur de streaming
    async def stream_generator() -> AsyncGenerator[str, None]:
        # Envoyer l'ID du message utilisateur
        yield format_sse_event({
            "type": "user_message_id",
            "message_id": user_message.id
        }, event="start")
        
        # Générer et streamer la réponse
        async for chunk in generate_ai_response_stream(message_data, session_id, current_user, db):
            if isinstance(chunk, dict):
                yield format_sse_event(chunk, event="message")
    
    return create_streaming_response(stream_generator())


@router.post("/sessions/{session_id}/documents")
async def process_document_in_chat(
    session_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process a document: extract, correct grammar, reformulate, and generate new document."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Determine file type
    file_type = file.filename.split('.')[-1].lower() if '.' in file.filename else "txt"
    
    if file_type not in ["pdf", "txt", "docx"]:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, TXT, or DOCX.")
    
    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, f"{current_user.id}_{session_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Save document record first
    from app.models import Document
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
    rag_processed = rag_service.process_document(
        file_path, 
        file_type, 
        user_id=current_user.id,
        document_id=document.id
    )
    if rag_processed:
        document.processed = True
        db.commit()
    
    # Save user message about document upload
    user_message = Message(
        session_id=session_id,
        role="user",
        content=f"📄 Document uploadé: {file.filename}",
        module_type="general"
    )
    db.add(user_message)
    db.commit()
    
    def create_thinking_message(content: str):
        """Helper to create and save a thinking message"""
        thinking_msg = Message(
            session_id=session_id,
            role="assistant",
            content=content,
            module_type="general"
        )
        db.add(thinking_msg)
        db.commit()
        db.refresh(thinking_msg)
        return thinking_msg
    
    try:
        print(f"Processing document: {file.filename}, type: {file_type}, path: {file_path}")
        
        # Create thinking messages during processing
        thinking_msg1 = create_thinking_message("🔍 **Analyse du document en cours...**\n\nJe suis en train d'extraire le texte de votre document. Veuillez patienter.")
        
        # Process document with better error handling
        thinking_messages = [thinking_msg1]  # Track all thinking messages for cleanup
        try:
            # Extract text first
            extracted_text = document_processor.extract_text_from_document(file_path, file_type)
            thinking_msg2 = create_thinking_message(f"✅ **Texte extrait avec succès!**\n\nJ'ai extrait {len(extracted_text)} caractères de votre document.\n\n🔧 **Correction grammaticale en cours...**\n\nJe suis en train de corriger les erreurs grammaticales et orthographiques.")
            thinking_messages.append(thinking_msg2)
            
            # Process document (grammar correction ONLY to preserve structure)
            # preserve_structure=True ensures original document structure is maintained
            process_result = document_processor.process_document(file_path, file_type, preserve_structure=True)
            thinking_msg3 = create_thinking_message(f"✅ **Corrections terminées!**\n\n{process_result['statistics'].get('corrections_count', 0)} correction(s) apportée(s).\n\n📄 **Préservation de la structure...**\n\nJe préserve la structure originale de votre document (titres, sections, formatage).")
            thinking_messages.append(thinking_msg3)
            
            # Generate document
            thinking_msg4 = create_thinking_message("📄 **Génération du document amélioré...**\n\nJe suis en train de créer votre nouveau document avec toutes les améliorations.")
            thinking_messages.append(thinking_msg4)
            
            # Generate output filename
            original_filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(original_filename)[0]
            output_filename = f"{name_without_ext}_amélioré.{file_type}"
            output_path = os.path.join(PROCESSED_DIR, output_filename)
            
            generated_path = document_processor.generate_document(
                process_result['processed_text'],
                output_path,
                file_type,
                original_file_path=file_path  # Pass original file for structure preservation
            )
            
            result = {
                **process_result,
                "generated_document_path": generated_path,
                "generated_document_filename": output_filename
            }
            
            print(f"Document processed successfully: {result.get('generated_document_filename', 'unknown')}")
            
            # Remove thinking messages before final response
            for msg in thinking_messages:
                db.query(Message).filter(Message.id == msg.id).delete()
            db.commit()
        except Exception as process_error:
            print(f"Error in process_and_generate: {process_error}")
            import traceback
            traceback.print_exc()
            
            # Remove thinking messages on error
            try:
                for msg in thinking_messages:
                    db.query(Message).filter(Message.id == msg.id).delete()
                db.commit()
            except Exception as cleanup_error:
                print(f"Error cleaning up thinking messages: {cleanup_error}")
            
            # Try to extract text at least
            try:
                extracted_text = document_processor.extract_text_from_document(file_path, file_type)
                print(f"Successfully extracted {len(extracted_text)} characters from document")
                # Process in smaller chunks to avoid timeout
                result = {
                    "original_text": extracted_text,
                    "processed_text": extracted_text,  # Skip processing if error
                    "corrections": [],
                    "statistics": {
                        "original_length": len(extracted_text),
                        "processed_length": len(extracted_text),
                        "corrections_count": 0,
                        "paragraphs_processed": 1
                    },
                    "generated_document_path": None,
                    "generated_document_filename": None,
                    "error": str(process_error)
                }
            except Exception as extract_error:
                print(f"Error extracting text: {extract_error}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Impossible d'extraire le texte du document. Erreur: {str(extract_error)}"
                )
        
        # Create AI response with processing results
        if result.get('error'):
            ai_response_content = f"""⚠️ **Document partiellement traité**

📄 **Fichier:** {file.filename}

**Statut:** Le texte a été extrait mais le traitement complet a échoué.
**Erreur:** {result['error']}

**Texte extrait:** {len(result.get('original_text', ''))} caractères

Veuillez réessayer ou contactez le support si le problème persiste.
"""
        else:
            corrections_summary = ""
            if result.get('corrections'):
                corrections_summary = f"\n\n**Corrections apportées:** {len(result['corrections'])} erreur(s) corrigée(s)\n"
                for i, corr in enumerate(result['corrections'][:5], 1):  # Show first 5
                    corrections_summary += f"{i}. {corr.get('original', '')} → {corr.get('corrected', '')}\n"
                if len(result['corrections']) > 5:
                    corrections_summary += f"... et {len(result['corrections']) - 5} autre(s) correction(s)\n"
            
            stats = result.get('statistics', {})
            download_path = ""
            if result.get('generated_document_path'):
                download_path = f"/api/chat/download/{os.path.basename(result['generated_document_path'])}"
            
            ai_response_content = f"""✅ **Document traité avec succès!**

📄 **Fichier original:** {file.filename}
📝 **Fichier amélioré:** {result.get('generated_document_filename', 'N/A')}

**Résumé du traitement:**
• Texte extrait et analysé
• {stats.get('corrections_count', 0)} correction(s) grammaticale(s) apportée(s)
• Structure originale préservée (titres, sections, formatage)
• {stats.get('paragraphs_processed', 0)} paragraphe(s) traité(s)
{corrections_summary}"""
            
            if download_path:
                ai_response_content += f"""

**Téléchargement:** Le document amélioré est prêt. Utilisez le bouton ci-dessous pour le télécharger.

DOWNLOAD_BUTTON:{download_path}
"""
        
        # Save AI response
        ai_message = Message(
            session_id=session_id,
            role="assistant",
            content=ai_response_content,
            module_type="general"
        )
        db.add(ai_message)
        
        # Update session
        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(ai_message)
        
        return {
            "message": "Document processed successfully" if not result.get('error') else "Document partially processed",
            "original_filename": file.filename,
            "processed_filename": result.get('generated_document_filename'),
            "download_path": download_path if result.get('generated_document_path') else None,
            "corrections_count": stats.get('corrections_count', 0),
            "statistics": stats
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up uploaded file on error
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        print(f"Error processing document: {e}")
        import traceback
        traceback.print_exc()
        
        error_message = str(e)
        # Make error message more user-friendly
        if "not available" in error_message.lower():
            error_message = "Les bibliothèques nécessaires ne sont pas disponibles. Veuillez contacter l'administrateur."
        elif "extract" in error_message.lower():
            error_message = f"Impossible d'extraire le texte du document. {error_message}"
        
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du document: {error_message}")

@router.get("/download/{filename}")
async def download_processed_document(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Download a processed document."""
    file_path = os.path.join(PROCESSED_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=filename
    )


@router.get("/sessions/{session_id}/export/markdown")
async def export_session_markdown(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export a chat session as Markdown."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise AppException(
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            detail="Session introuvable."
        )
    
    # Préparer les messages
    messages_data = [
        {
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in session.messages
    ]
    
    # Générer le Markdown
    md_content = export_to_markdown(
        session_title=session.title,
        messages=messages_data,
        created_at=session.created_at.isoformat() if session.created_at else None
    )
    
    # Créer le nom de fichier
    filename = f"conversation_{session_id}_{datetime.utcnow().strftime('%Y%m%d')}.md"
    
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/sessions/{session_id}/export/pdf")
async def export_session_pdf(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export a chat session as PDF."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise AppException(
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            detail="Session introuvable."
        )
    
    # Préparer les messages
    messages_data = [
        {
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in session.messages
    ]
    
    # Générer le PDF
    try:
        pdf_buffer = export_to_pdf(
            session_title=session.title,
            messages=messages_data,
            created_at=session.created_at.isoformat() if session.created_at else None
        )
        
        # Créer le nom de fichier
        filename = f"conversation_{session_id}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        logger.error("Error exporting PDF", exc_info=e)
        raise AppException(
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=500,
            detail="Erreur lors de la génération du PDF."
        )


@router.post("/sessions/{session_id}/share")
async def share_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a shareable link for a chat session."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise AppException(
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            detail="Session introuvable."
        )
    
    # Générer un token de partage s'il n'existe pas
    if not session.share_token:
        session.share_token = generate_share_token()
        session.is_shared = True
        db.commit()
        db.refresh(session)
    
    # Obtenir l'URL de base depuis les variables d'environnement ou utiliser une valeur par défaut
    base_url = os.getenv("BASE_URL", "http://localhost:5173")
    share_link = create_share_link(session.share_token, base_url)
    
    logger.info(
        "Session shared",
        extra_data={
            "event": "session_shared",
            "session_id": session_id,
            "user_id": current_user.id
        }
    )
    
    return {
        "share_token": session.share_token,
        "share_link": share_link,
        "is_shared": session.is_shared
    }


@router.delete("/sessions/{session_id}/share")
async def unshare_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove sharing from a chat session."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise AppException(
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            detail="Session introuvable."
        )
    
    session.share_token = None
    session.is_shared = False
    db.commit()
    
    logger.info(
        "Session unshared",
        extra_data={
            "event": "session_unshared",
            "session_id": session_id,
            "user_id": current_user.id
        }
    )
    
    return {"message": "Partage supprimé", "is_shared": False}


@router.get("/share/{share_token}")
async def get_shared_session(
    share_token: str,
    db: Session = Depends(get_db)
):
    """Get a shared chat session (public access, no authentication required)."""
    if not validate_share_token(share_token):
        raise AppException(
            error_code=ErrorCode.BAD_REQUEST,
            status_code=400,
            detail="Token de partage invalide."
        )
    
    session = db.query(ChatSession).filter(
        ChatSession.share_token == share_token,
        ChatSession.is_shared == True
    ).first()
    
    if not session:
        raise AppException(
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            detail="Session partagée introuvable ou non disponible."
        )
    
    # Retourner les détails de la session (sans informations sensibles)
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "message_count": len(session.messages),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "module_type": m.module_type,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in session.messages
        ],
        "is_shared": True
    }


@router.post("/search/messages", response_model=SearchResponse)
async def search_messages(
    search_request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recherche full-text dans les messages avec filtres par date, module et rôle.
    """
    try:
        result = search_messages_fulltext(
            db=db,
            user_id=current_user.id,
            query=search_request.query or "",
            module_type=search_request.module_type,
            date_from=search_request.date_from,
            date_to=search_request.date_to,
            role=search_request.role,
            limit=min(search_request.limit, 100),  # Limiter à 100 max
            offset=search_request.offset
        )
        
        logger.info(
            "Search performed",
            extra_data={
                "event": "search_messages",
                "user_id": current_user.id,
                "query": search_request.query,
                "results_count": len(result["results"]),
                "total": result["total"]
            }
        )
        
        return SearchResponse(**result)
    
    except Exception as e:
        logger.error("Error in search_messages", exc_info=e)
        raise AppException(
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=500,
            detail="Erreur lors de la recherche."
        )

@router.post("/search/hybrid", response_model=SearchResponse)
async def hybrid_search_messages(
    search_request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recherche hybride (BM25 + Sémantique) dans les messages
    """
    try:
        # Utiliser la recherche hybride
        results = hybrid_search.hybrid_search(
            db=db,
            user_id=current_user.id,
            query=search_request.query or "",
            k=search_request.limit or 50,
            bm25_weight=0.4,
            semantic_weight=0.6
        )
        
        # Convertir en format SearchResponse
        search_results = []
        for result in results:
            # Récupérer la session
            session = db.query(ChatSession).filter(ChatSession.id == result["session_id"]).first()
            
            search_results.append({
                "id": result["message_id"],
                "session_id": result["session_id"],
                "session_title": session.title if session else "Unknown",
                "role": result["role"],
                "content": result["content"],
                "module_type": result["module_type"],
                "created_at": result["created_at"],
                "highlight": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
            })
        
        logger.info(
            f"Hybrid search completed for user {current_user.id}",
            extra_data={
                "event": "hybrid_search",
                "user_id": current_user.id,
                "query": search_request.query,
                "results_count": len(search_results)
            }
        )
        
        return SearchResponse(
            results=search_results,
            total=len(search_results),
            limit=search_request.limit or 50,
            offset=search_request.offset or 0,
            has_more=False
        )
    except Exception as e:
        logger.error("Error in hybrid search", exc_info=e)
        raise AppException(
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=500,
            detail="Erreur lors de la recherche hybride."
        )


@router.post("/search/sessions", response_model=SessionSearchResponse)
async def search_sessions_endpoint(
    search_request: SessionSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recherche dans les sessions avec filtres par date et module.
    """
    try:
        result = search_sessions(
            db=db,
            user_id=current_user.id,
            query=search_request.query,
            date_from=search_request.date_from,
            date_to=search_request.date_to,
            module_type=search_request.module_type,
            limit=min(search_request.limit, 50),  # Limiter à 50 max
            offset=search_request.offset
        )
        
        logger.info(
            "Session search performed",
            extra_data={
                "event": "search_sessions",
                "user_id": current_user.id,
                "query": search_request.query,
                "results_count": len(result["results"]),
                "total": result["total"]
            }
        )
        
        return SessionSearchResponse(**result)
    
    except Exception as e:
        logger.error("Error in search_sessions", exc_info=e)
        raise AppException(
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=500,
            detail="Erreur lors de la recherche de sessions."
        )


@router.get("/search/suggestions")
async def get_search_suggestions_endpoint(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtient des suggestions de recherche basées sur l'historique.
    """
    if len(q) < 2:
        return {"suggestions": []}
    
    try:
        suggestions = get_search_suggestions(
            db=db,
            user_id=current_user.id,
            query=q,
            limit=10
        )
        
        return {"suggestions": suggestions}
    
    except Exception as e:
        logger.error("Error getting search suggestions", exc_info=e)
        return {"suggestions": []}

