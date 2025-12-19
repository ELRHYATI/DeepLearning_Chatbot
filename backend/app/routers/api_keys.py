"""
Router pour la gestion des clés API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import User, APIKey
from app.routers.auth import get_current_user as get_current_user_jwt
from app.utils.api_key_auth import generate_api_key, hash_api_key
from app.utils.logger import get_logger
from app.schemas import APIKeyCreate, APIKeyResponse, APIKeyListResponse
from datetime import datetime, timedelta

logger = get_logger()

router = APIRouter()


@router.post("/", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_jwt)
):
    """
    Crée une nouvelle clé API
    
    Args:
        key_data: Données de la clé (nom, expiration optionnelle)
        db: Session de base de données
        current_user: Utilisateur actuel
    
    Returns:
        Clé API créée (affichée une seule fois)
    """
    # Générer la clé API
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    
    # Calculer la date d'expiration si fournie
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
    
    # Créer l'entrée dans la base de données
    new_api_key = APIKey(
        user_id=current_user.id,
        key_name=key_data.key_name,
        api_key=api_key,  # Stocker en clair pour affichage initial (à supprimer après)
        key_hash=key_hash,
        is_active=True,
        expires_at=expires_at
    )
    
    db.add(new_api_key)
    db.commit()
    db.refresh(new_api_key)
    
    logger.info(
        f"API key created for user {current_user.id}",
        extra_data={"api_key_id": new_api_key.id, "key_name": key_data.key_name}
    )
    
    # Retourner la clé (affichée une seule fois)
    return APIKeyResponse(
        id=new_api_key.id,
        key_name=new_api_key.key_name,
        api_key=api_key,  # Afficher la clé une seule fois
        is_active=new_api_key.is_active,
        created_at=new_api_key.created_at,
        expires_at=new_api_key.expires_at,
        last_used=new_api_key.last_used
    )


@router.get("/", response_model=List[APIKeyListResponse])
async def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_jwt)
):
    """
    Liste toutes les clés API de l'utilisateur
    
    Args:
        db: Session de base de données
        current_user: Utilisateur actuel
    
    Returns:
        Liste des clés API (sans la clé elle-même pour sécurité)
    """
    api_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id
    ).order_by(APIKey.created_at.desc()).all()
    
    return [
        APIKeyListResponse(
            id=key.id,
            key_name=key.key_name,
            is_active=key.is_active,
            created_at=key.created_at,
            expires_at=key.expires_at,
            last_used=key.last_used,
            masked_key=f"{key.api_key[:12]}...{key.api_key[-4:]}" if key.api_key else "***"
        )
        for key in api_keys
    ]


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_jwt)
):
    """
    Révoque une clé API
    
    Args:
        key_id: ID de la clé API
        db: Session de base de données
        current_user: Utilisateur actuel
    
    Returns:
        Message de confirmation
    """
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="Clé API non trouvée")
    
    # Désactiver la clé au lieu de la supprimer (pour audit)
    api_key.is_active = False
    db.commit()
    
    logger.info(
        f"API key revoked: {key_id}",
        extra_data={"api_key_id": key_id, "user_id": current_user.id}
    )
    
    return {"message": "Clé API révoquée avec succès"}


@router.post("/{key_id}/regenerate", response_model=APIKeyResponse)
async def regenerate_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_jwt)
):
    """
    Régénère une clé API existante
    
    Args:
        key_id: ID de la clé API
        db: Session de base de données
        current_user: Utilisateur actuel
    
    Returns:
        Nouvelle clé API
    """
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="Clé API non trouvée")
    
    # Générer une nouvelle clé
    new_api_key = generate_api_key()
    new_key_hash = hash_api_key(new_api_key)
    
    # Mettre à jour
    api_key.api_key = new_api_key  # Stocker temporairement pour affichage
    api_key.key_hash = new_key_hash
    api_key.is_active = True
    api_key.last_used = None
    db.commit()
    db.refresh(api_key)
    
    logger.info(
        f"API key regenerated: {key_id}",
        extra_data={"api_key_id": key_id, "user_id": current_user.id}
    )
    
    return APIKeyResponse(
        id=api_key.id,
        key_name=api_key.key_name,
        api_key=new_api_key,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        last_used=api_key.last_used
    )

