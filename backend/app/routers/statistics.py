"""
Router pour les statistiques d'utilisation
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import User, ChatSession
from app.routers.auth import get_current_user_optional
from app.utils.statistics import get_user_statistics, get_usage_trends, get_performance_metrics
from app.utils.logger import get_logger

logger = get_logger()

router = APIRouter()


def get_empty_stats():
    """Retourne des statistiques vides pour les utilisateurs non authentifiés"""
    return {
        "total_messages": 0,
        "total_sessions": 0,
        "shared_sessions": 0,
        "total_documents": 0,
        "recent_activity": 0,
        "module_usage": {},
        "role_distribution": {},
        "daily_messages": [],
        "daily_sessions": []
    }


@router.get("/stats")
async def get_statistics(
    days: int = Query(30, ge=1, le=365, description="Nombre de jours pour les statistiques"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Récupère les statistiques d'utilisation de l'utilisateur
    
    Args:
        days: Nombre de jours pour les statistiques (1-365)
        db: Session de base de données
        current_user: Utilisateur actuel (optionnel)
    
    Returns:
        Statistiques d'utilisation
    """
    if not current_user:
        logger.info("Statistics requested without authentication, returning empty stats")
        return get_empty_stats()
    
    try:
        # Debug: Log user info and check session count
        session_count = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).count()
        logger.info(
            f"Statistics request for user {current_user.id} (email: {current_user.email}), found {session_count} sessions",
            extra_data={"event": "statistics_request", "user_id": current_user.id, "email": current_user.email, "session_count": session_count, "days": days}
        )
        
        stats = get_user_statistics(db, current_user.id, days)
        
        logger.info(
            f"Statistics retrieved for user {current_user.id}: {stats.get('total_sessions', 0)} sessions, {stats.get('total_messages', 0)} messages",
            extra_data={"event": "statistics_retrieved", "user_id": current_user.id, "days": days, "total_sessions": stats.get('total_sessions', 0), "total_messages": stats.get('total_messages', 0)}
        )
        return stats
    except Exception as e:
        logger.error(f"Error retrieving statistics for user {current_user.id if current_user else 'unknown'}: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des statistiques")


@router.get("/stats/trends")
async def get_trends(
    days: int = Query(30, ge=1, le=365, description="Nombre de jours pour les tendances"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Récupère les tendances d'utilisation
    
    Args:
        days: Nombre de jours pour les tendances (1-365)
        db: Session de base de données
        current_user: Utilisateur actuel (optionnel)
    
    Returns:
        Tendances d'utilisation
    """
    if not current_user:
        logger.info("Trends requested without authentication, returning empty trends")
        return {"daily_activity": [], "module_trends": {}}
    
    try:
        trends = get_usage_trends(db, current_user.id, days)
        logger.info(
            f"Trends retrieved for user {current_user.id}",
            extra_data={"event": "trends_retrieved", "user_id": current_user.id, "days": days}
        )
        return trends
    except Exception as e:
        logger.error(f"Error retrieving trends: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des tendances")


@router.get("/stats/performance")
async def get_performance(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Récupère les métriques de performance
    
    Args:
        db: Session de base de données
        current_user: Utilisateur actuel (optionnel)
    
    Returns:
        Métriques de performance
    """
    if not current_user:
        logger.info("Performance metrics requested without authentication, returning empty metrics")
        return {
            "most_used_module": None,
            "most_used_module_count": 0,
            "average_messages_per_session": 0,
            "active_sessions": 0
        }
    
    try:
        metrics = get_performance_metrics(db, current_user.id)
        logger.info(
            f"Performance metrics retrieved for user {current_user.id}",
            extra_data={"event": "performance_metrics_retrieved", "user_id": current_user.id}
        )
        return metrics
    except Exception as e:
        logger.error(f"Error retrieving performance metrics: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des métriques de performance")

