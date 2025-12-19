"""
Utilitaires pour le partage de sessions
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from app.utils.logger import get_logger

logger = get_logger()


def generate_share_token() -> str:
    """
    Génère un token unique pour le partage de session
    
    Returns:
        Token de partage (32 caractères hexadécimaux)
    """
    return secrets.token_urlsafe(32)


def validate_share_token(token: str) -> bool:
    """
    Valide un token de partage (vérifie le format)
    
    Args:
        token: Token à valider
    
    Returns:
        True si le format est valide
    """
    if not token or len(token) < 16:
        return False
    # Vérifier que le token contient uniquement des caractères alphanumériques et -_
    return all(c.isalnum() or c in '-_' for c in token)


def create_share_link(token: str, base_url: Optional[str] = None) -> str:
    """
    Crée un lien de partage
    
    Args:
        token: Token de partage
        base_url: URL de base (optionnel, par défaut localhost)
    
    Returns:
        Lien de partage complet
    """
    if base_url:
        return f"{base_url.rstrip('/')}/api/chat/share/{token}"
    return f"/api/chat/share/{token}"

