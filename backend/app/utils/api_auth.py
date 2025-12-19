"""
Middleware d'authentification pour l'API publique (clés API ou JWT)
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import User
from app.utils.api_key_auth import get_user_from_api_key
from app.routers.auth import get_current_user as get_current_user_jwt
from app.utils.error_handler import AppException, ErrorCode

security = HTTPBearer(auto_error=False)


def get_current_user_api(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Authentifie l'utilisateur via JWT ou clé API
    
    Args:
        credentials: Credentials HTTP (Bearer token)
        db: Session de base de données
    
    Returns:
        User authentifié
    
    Raises:
        HTTPException si l'authentification échoue
    """
    if not credentials:
        raise AppException(
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise. Fournissez un token JWT ou une clé API."
        )
    
    token = credentials.credentials
    
    # Essayer d'abord avec une clé API
    if token.startswith("ak_live_"):
        user = get_user_from_api_key(db, token)
        if user:
            return user
    
    # Sinon, essayer avec JWT
    try:
        return get_current_user_jwt(credentials, db)
    except Exception:
        raise AppException(
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification invalide ou clé API invalide."
        )

