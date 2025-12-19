from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import QARequest, QAResponse
from app.services.qa_service import QAService
from app.services.rag_service import RAGService
from app.utils.error_handler import AppException, ErrorCode, async_retry
from app.utils.redis_cache import cache
from app.utils.logger import get_logger

router = APIRouter()
qa_service = QAService()
rag_service = RAGService()
logger = get_logger()

@router.post("/answer", response_model=QAResponse)
@async_retry(max_attempts=3, delay=0.5, exceptions=(Exception,))
async def answer_question(request: QARequest, db: Session = Depends(get_db)):
    """
    Answer a question in French using the QA model and RAG if available.
    """
    try:
        # Try to get context from RAG first
        context = request.context
        if not context:
            # Use enhanced retrieval with better context
            try:
                rag_results = rag_service.retrieve_context(request.question, k=5, min_score=0.3)
                if rag_results:
                    context_parts = [r["content"] for r in rag_results[:3]]  # Use top 3
                    context = "\n\n".join(context_parts)
            except Exception as rag_error:
                # RAG non disponible, continuer sans contexte
                context = None
        
        # Générer une clé de cache
        cache_key = cache._generate_key("qa", request.question, context or "")
        
        # Vérifier le cache
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("QA answer retrieved from cache", extra_data={"question": request.question[:50]})
            return QAResponse(**cached_result)
        
        result = qa_service.answer_question(request.question, context)
        
        # Format answer in academic style
        if result["confidence"] > 0.3:
            result["answer"] = qa_service.format_academic_answer(
                result["answer"], 
                result["confidence"]
            )
        
        # Mettre en cache (TTL: 1 heure)
        cache.set(cache_key, result, ttl=3600)
        
        return QAResponse(**result)
    except AppException:
        # Re-raise les exceptions personnalisées
        raise
    except Exception as e:
        raise AppException(
            error_code=ErrorCode.MODEL_INFERENCE_ERROR,
            status_code=500,
            detail="Erreur lors de la génération de la réponse. Veuillez réessayer.",
            extra_data={"original_error": str(e)}
        )

