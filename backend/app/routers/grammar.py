from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import GrammarRequest, GrammarResponse
from app.services.grammar_service import GrammarService
from app.utils.error_handler import AppException, ErrorCode, async_retry
from app.utils.redis_cache import cache
from app.utils.logger import get_logger

router = APIRouter()
grammar_service = GrammarService()
logger = get_logger()

@router.post("/correct", response_model=GrammarResponse)
@async_retry(max_attempts=3, delay=0.5, exceptions=(Exception,))
async def correct_grammar(request: GrammarRequest, db: Session = Depends(get_db)):
    """
    Correct French text grammar and provide explanations.
    """
    try:
        # Générer une clé de cache
        cache_key = cache._generate_key("grammar", request.text)
        
        # Vérifier le cache
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("Grammar correction retrieved from cache", extra_data={"text_length": len(request.text)})
            return GrammarResponse(**cached_result)
        
        result = grammar_service.correct_text(request.text)
        
        # Mettre en cache (TTL: 24 heures pour les corrections grammaticales)
        cache.set(cache_key, result, ttl=86400)
        
        return GrammarResponse(**result)
    except Exception as e:
        raise AppException(
            error_code=ErrorCode.MODEL_INFERENCE_ERROR,
            status_code=500,
            detail="Erreur lors de la correction grammaticale. Veuillez réessayer.",
            extra_data={"original_error": str(e)}
        )

