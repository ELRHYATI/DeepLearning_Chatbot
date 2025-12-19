"""
Middleware pour le tracking des performances des requêtes API
"""
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from app.utils.logger import get_logger


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware pour tracker les performances des requêtes"""
    
    def __init__(self, app, logger=None):
        super().__init__(app)
        self.logger = logger or get_logger()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Intercepte les requêtes pour mesurer les performances"""
        start_time = time.time()
        
        # Obtenir l'IP du client
        client_ip = request.client.host if request.client else None
        
        # Obtenir l'ID utilisateur si disponible (depends de l'auth)
        user_id = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id
        
        # Exécuter la requête
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Logger la requête
            self.logger.log_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=user_id,
                client_ip=client_ip,
                query_params=dict(request.query_params) if request.query_params else None
            )
            
            # Ajouter le header de durée de réponse
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            
            return response
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Logger l'erreur
            self.logger.log_error_with_context(
                error=e,
                context={
                    "method": request.method,
                    "path": request.url.path,
                    "user_id": user_id,
                    "client_ip": client_ip,
                    "duration_ms": duration_ms
                }
            )
            
            raise

