"""
Gestion d'erreurs centralisée avec messages en français et retry logic
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional, Dict, Any, Callable, TypeVar, List
import time
import asyncio
from functools import wraps
from app.utils.logger import get_logger

logger = get_logger()

# Codes d'erreur personnalisés
class ErrorCode:
    """Codes d'erreur standardisés"""
    # Erreurs générales
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    BAD_REQUEST = "BAD_REQUEST"
    
    # Erreurs d'authentification
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    
    # Erreurs de modèles ML
    MODEL_NOT_AVAILABLE = "MODEL_NOT_AVAILABLE"
    MODEL_LOAD_ERROR = "MODEL_LOAD_ERROR"
    MODEL_INFERENCE_ERROR = "MODEL_INFERENCE_ERROR"
    
    # Erreurs de base de données
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    
    # Erreurs de fichiers
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    FILE_PROCESSING_ERROR = "FILE_PROCESSING_ERROR"
    
    # Erreurs de services externes
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


# Messages d'erreur en français
ERROR_MESSAGES: Dict[str, str] = {
    ErrorCode.INTERNAL_ERROR: "Une erreur interne s'est produite. Veuillez réessayer plus tard.",
    ErrorCode.VALIDATION_ERROR: "Les données fournies sont invalides.",
    ErrorCode.NOT_FOUND: "La ressource demandée est introuvable.",
    ErrorCode.UNAUTHORIZED: "Authentification requise. Veuillez vous connecter.",
    ErrorCode.FORBIDDEN: "Vous n'avez pas la permission d'effectuer cette action.",
    ErrorCode.BAD_REQUEST: "La requête est invalide.",
    
    ErrorCode.INVALID_CREDENTIALS: "Email ou mot de passe incorrect.",
    ErrorCode.TOKEN_EXPIRED: "Votre session a expiré. Veuillez vous reconnecter.",
    ErrorCode.TOKEN_INVALID: "Token d'authentification invalide.",
    
    ErrorCode.MODEL_NOT_AVAILABLE: "Le modèle de traitement n'est pas disponible pour le moment.",
    ErrorCode.MODEL_LOAD_ERROR: "Erreur lors du chargement du modèle.",
    ErrorCode.MODEL_INFERENCE_ERROR: "Erreur lors du traitement par le modèle.",
    
    ErrorCode.DATABASE_ERROR: "Erreur de base de données.",
    ErrorCode.DATABASE_CONNECTION_ERROR: "Impossible de se connecter à la base de données.",
    
    ErrorCode.FILE_NOT_FOUND: "Le fichier demandé est introuvable.",
    ErrorCode.FILE_TOO_LARGE: "Le fichier est trop volumineux.",
    ErrorCode.UNSUPPORTED_FILE_TYPE: "Type de fichier non supporté.",
    ErrorCode.FILE_PROCESSING_ERROR: "Erreur lors du traitement du fichier.",
    
    ErrorCode.EXTERNAL_SERVICE_ERROR: "Erreur avec un service externe.",
    ErrorCode.SERVICE_UNAVAILABLE: "Le service est temporairement indisponible.",
}


class AppException(HTTPException):
    """Exception personnalisée avec code d'erreur et message en français"""
    
    def __init__(
        self,
        error_code: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            error_code: Code d'erreur standardisé
            status_code: Code HTTP
            detail: Message d'erreur personnalisé (optionnel)
            extra_data: Données supplémentaires pour le logging
        """
        self.error_code = error_code
        self.extra_data = extra_data or {}
        
        # Utiliser le message personnalisé ou le message par défaut
        message = detail or ERROR_MESSAGES.get(error_code, "Une erreur s'est produite.")
        
        super().__init__(status_code=status_code, detail=message)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler global pour toutes les exceptions"""
    
    # Gérer les exceptions HTTP personnalisées
    if isinstance(exc, AppException):
        # Log seulement les vraies erreurs (pas les 401/403 normaux)
        if exc.status_code >= 500:
            logger.log_error_with_context(
                error=exc,
                context={
                    "path": request.url.path,
                    "method": request.method,
                    "client_ip": request.client.host if request.client else None,
                }
            )
        elif exc.status_code >= 400:
            logger.warning(
                f"{request.method} {request.url.path} - {exc.status_code}: {exc.detail}",
                extra_data={
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": exc.status_code,
                    "client_ip": request.client.host if request.client else None,
                }
            )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "error_code": exc.error_code,
                "message": exc.detail,
                "data": exc.extra_data
            }
        )
    
    # Gérer les HTTPException standard
    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        # Essayer de déterminer le code d'erreur basé sur le status code
        error_code = _get_error_code_from_status(exc.status_code)
        
        # Log seulement les vraies erreurs (401/403 sont normaux pour les utilisateurs non authentifiés)
        if exc.status_code >= 500:
            logger.log_error_with_context(
                error=exc,
                context={
                    "path": request.url.path,
                    "method": request.method,
                    "client_ip": request.client.host if request.client else None,
                }
            )
        elif exc.status_code == 401 or exc.status_code == 403:
            # Log 401/403 comme info (cas normal pour utilisateurs non authentifiés)
            logger.info(
                f"{request.method} {request.url.path} - {exc.status_code}: {exc.detail if isinstance(exc.detail, str) else str(exc.detail)}",
                extra_data={
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": exc.status_code,
                    "client_ip": request.client.host if request.client else None,
                }
            )
        elif exc.status_code >= 400:
            logger.warning(
                f"{request.method} {request.url.path} - {exc.status_code}: {exc.detail if isinstance(exc.detail, str) else str(exc.detail)}",
                extra_data={
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": exc.status_code,
                    "client_ip": request.client.host if request.client else None,
                }
            )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "error_code": error_code,
                "message": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            }
        )
    
    # Gérer les erreurs de validation
    if isinstance(exc, RequestValidationError):
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error.get("loc", []))
            errors.append({
                "field": field,
                "message": error.get("msg", "Erreur de validation"),
                "type": error.get("type", "validation_error")
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": True,
                "error_code": ErrorCode.VALIDATION_ERROR,
                "message": ERROR_MESSAGES[ErrorCode.VALIDATION_ERROR],
                "validation_errors": errors
            }
        )
    
    # Gérer toutes les autres exceptions (vraies erreurs)
    logger.log_error_with_context(
        error=exc,
        context={
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else None,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "error_code": ErrorCode.INTERNAL_ERROR,
            "message": ERROR_MESSAGES[ErrorCode.INTERNAL_ERROR],
        }
    )


def _get_error_code_from_status(status_code: int) -> str:
    """Obtient un code d'erreur basé sur le code de status HTTP"""
    if status_code == 400:
        return ErrorCode.BAD_REQUEST
    elif status_code == 401:
        return ErrorCode.UNAUTHORIZED
    elif status_code == 403:
        return ErrorCode.FORBIDDEN
    elif status_code == 404:
        return ErrorCode.NOT_FOUND
    elif status_code == 422:
        return ErrorCode.VALIDATION_ERROR
    else:
        return ErrorCode.INTERNAL_ERROR


# Retry logic
T = TypeVar('T')


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
):
    """
    Décorateur pour retry logic avec backoff exponentiel
    
    Args:
        max_attempts: Nombre maximum de tentatives
        delay: Délai initial entre les tentatives (en secondes)
        backoff: Facteur de backoff exponentiel
        exceptions: Types d'exceptions à retry
        on_retry: Callback appelé à chaque retry
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        # Dernière tentative échouée
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts",
                            exc_info=e,
                            extra_data={
                                "function": func.__name__,
                                "attempts": max_attempts,
                                "final_error": str(e)
                            }
                        )
                        raise
                    
                    # Log le retry
                    logger.warning(
                        f"Function {func.__name__} failed, retrying (attempt {attempt}/{max_attempts})",
                        exc_info=e,
                        extra_data={
                            "function": func.__name__,
                            "attempt": attempt,
                            "max_attempts": max_attempts,
                            "delay": current_delay
                        }
                    )
                    
                    # Callback on_retry
                    if on_retry:
                        on_retry(attempt, e)
                    
                    # Attendre avant le prochain retry
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # Ne devrait jamais arriver ici, mais au cas où
            if last_exception:
                raise last_exception
            
            raise RuntimeError("Retry logic failed unexpectedly")
        
        return wrapper
    
    return decorator


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
):
    """
    Décorateur pour retry logic asynchrone avec backoff exponentiel
    
    Args:
        max_attempts: Nombre maximum de tentatives
        delay: Délai initial entre les tentatives (en secondes)
        backoff: Facteur de backoff exponentiel
        exceptions: Types d'exceptions à retry
        on_retry: Callback appelé à chaque retry
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        # Dernière tentative échouée
                        logger.error(
                            f"Async function {func.__name__} failed after {max_attempts} attempts",
                            exc_info=e,
                            extra_data={
                                "function": func.__name__,
                                "attempts": max_attempts,
                                "final_error": str(e)
                            }
                        )
                        raise
                    
                    # Log le retry
                    logger.warning(
                        f"Async function {func.__name__} failed, retrying (attempt {attempt}/{max_attempts})",
                        exc_info=e,
                        extra_data={
                            "function": func.__name__,
                            "attempt": attempt,
                            "max_attempts": max_attempts,
                            "delay": current_delay
                        }
                    )
                    
                    # Callback on_retry
                    if on_retry:
                        on_retry(attempt, e)
                    
                    # Attendre avant le prochain retry
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            # Ne devrait jamais arriver ici, mais au cas où
            if last_exception:
                raise last_exception
            
            raise RuntimeError("Retry logic failed unexpectedly")
        
        return wrapper
    
    return decorator


def create_error_response(
    error_code: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None
) -> AppException:
    """
    Helper pour créer une réponse d'erreur standardisée
    
    Args:
        error_code: Code d'erreur
        status_code: Code HTTP
        detail: Message personnalisé
        extra_data: Données supplémentaires
    """
    return AppException(
        error_code=error_code,
        status_code=status_code,
        detail=detail,
        extra_data=extra_data or {}
    )

