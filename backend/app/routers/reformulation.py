from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ReformulationRequest, ReformulationResponse
from app.services.reformulation_service import ReformulationService
from app.utils.error_handler import AppException, ErrorCode, async_retry
from app.utils.redis_cache import cache
from app.utils.logger import get_logger

router = APIRouter()
reformulation_service = ReformulationService()
logger = get_logger()

@router.post("/reformulate", response_model=ReformulationResponse)
@async_retry(max_attempts=3, delay=0.5, exceptions=(Exception,))
async def reformulate_text(request: ReformulationRequest, db: Session = Depends(get_db)):
    """
    Reformulate French text while maintaining meaning with caching.
    """
    try:
        # Générer une clé de cache (incluant le style)
        cache_key = cache._generate_key("reformulation", request.text, request.style)
        
        # Vérifier le cache
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("Reformulation retrieved from cache", extra_data={"text_length": len(request.text), "style": request.style})
            return ReformulationResponse(**cached_result)
        
        # Exécuter la reformulation
        result = reformulation_service.reformulate_text(request.text, request.style)
        
        # Mettre en cache (TTL: 12 heures pour les reformulations)
        cache.set(cache_key, result, ttl=43200)
        
        return ReformulationResponse(**result)
    except Exception as e:
        raise AppException(
            error_code=ErrorCode.MODEL_INFERENCE_ERROR,
            status_code=500,
            detail="Erreur lors de la reformulation du texte. Veuillez réessayer.",
            extra_data={"original_error": str(e)}
        )

