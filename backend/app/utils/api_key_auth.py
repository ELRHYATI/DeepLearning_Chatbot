"""
Utilitaires pour l'authentification par clé API
"""
import hashlib
import secrets
from typing import Optional
from sqlalchemy.orm import Session
from app.models import APIKey, User
from app.utils.logger import get_logger
from datetime import datetime

logger = get_logger()


def generate_api_key() -> str:
    """
    Génère une nouvelle clé API sécurisée
    
    Returns:
        Clé API au format: ak_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    """
    random_bytes = secrets.token_bytes(32)
    key_suffix = secrets.token_urlsafe(24)
    return f"ak_live_{key_suffix}"


def hash_api_key(api_key: str) -> str:
    """
    Hash une clé API pour stockage sécurisé
    
    Args:
        api_key: Clé API en clair
    
    Returns:
        Hash SHA-256 de la clé
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, key_hash: str) -> bool:
    """
    Vérifie si une clé API correspond au hash stocké
    
    Args:
        api_key: Clé API en clair
        key_hash: Hash stocké
    
    Returns:
        True si la clé correspond
    """
    return hash_api_key(api_key) == key_hash


def get_user_from_api_key(db: Session, api_key: str) -> Optional[User]:
    """
    Récupère l'utilisateur associé à une clé API
    
    Args:
        db: Session de base de données
        api_key: Clé API
    
    Returns:
        User si la clé est valide, None sinon
    """
    if not api_key or not api_key.startswith("ak_live_"):
        return None
    
    key_hash = hash_api_key(api_key)
    
    # Rechercher la clé dans la base de données
    api_key_obj = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active == True
    ).first()
    
    if not api_key_obj:
        return None
    
    # Vérifier l'expiration
    if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
        logger.warning(f"API key expired: {api_key_obj.id}")
        return None
    
    # Mettre à jour la dernière utilisation
    api_key_obj.last_used = datetime.utcnow()
    db.commit()
    
    # Récupérer l'utilisateur
    user = db.query(User).filter(User.id == api_key_obj.user_id).first()
    
    logger.info(
        f"API key authenticated for user {user.id if user else None}",
        extra_data={"api_key_id": api_key_obj.id, "user_id": api_key_obj.user_id}
    )
    
    return user

