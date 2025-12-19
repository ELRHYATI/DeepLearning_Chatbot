"""
Utilitaires pour calculer les statistiques d'utilisation
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, extract
from sqlalchemy.orm import Session
from app.models import User, ChatSession, Message, Document
from app.utils.logger import get_logger

logger = get_logger()


def get_user_statistics(
    db: Session,
    user_id: int,
    days: int = 30
) -> Dict:
    """
    Calcule les statistiques d'utilisation pour un utilisateur
    
    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
        days: Nombre de jours pour les statistiques (défaut: 30)
    
    Returns:
        Dictionnaire avec les statistiques
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Debug logging
    logger.info(f"Calculating statistics for user_id={user_id}, days={days}")
    
    # Statistiques générales - count ALL sessions for this user (not filtered by date)
    total_sessions = db.query(ChatSession).filter(
        ChatSession.user_id == user_id
    ).count()
    
    logger.debug(f"Total sessions for user {user_id}: {total_sessions}")
    
    # Count ALL messages for this user (not filtered by date)
    total_messages = db.query(Message).join(ChatSession).filter(
        ChatSession.user_id == user_id
    ).count()
    
    logger.debug(f"Total messages for user {user_id}: {total_messages}")
    
    total_documents = db.query(Document).filter(
        Document.user_id == user_id
    ).count()
    
    # Messages par module
    messages_by_module = db.query(
        Message.module_type,
        func.count(Message.id).label('count')
    ).join(ChatSession).filter(
        ChatSession.user_id == user_id
    ).group_by(Message.module_type).all()
    
    module_stats = {
        module or "general": count
        for module, count in messages_by_module
    }
    
    # Messages par jour (progression)
    daily_messages = db.query(
        func.date(Message.created_at).label('date'),
        func.count(Message.id).label('count')
    ).join(ChatSession).filter(
        ChatSession.user_id == user_id,
        Message.created_at >= start_date
    ).group_by(func.date(Message.created_at)).order_by('date').all()
    
    # Sessions par jour
    daily_sessions = db.query(
        func.date(ChatSession.created_at).label('date'),
        func.count(ChatSession.id).label('count')
    ).filter(
        ChatSession.user_id == user_id,
        ChatSession.created_at >= start_date
    ).group_by(func.date(ChatSession.created_at)).order_by('date').all()
    
    # Messages par rôle
    messages_by_role = db.query(
        Message.role,
        func.count(Message.id).label('count')
    ).join(ChatSession).filter(
        ChatSession.user_id == user_id
    ).group_by(Message.role).all()
    
    role_stats = {
        role: count
        for role, count in messages_by_role
    }
    
    # Sessions partagées
    shared_sessions = db.query(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.is_shared == True
    ).count()
    
    # Activité récente (dernières 7 jours)
    recent_activity = db.query(Message).join(ChatSession).filter(
        ChatSession.user_id == user_id,
        Message.created_at >= end_date - timedelta(days=7)
    ).count()
    
    # Temps moyen entre les messages (approximation)
    user_messages = db.query(Message.created_at).join(ChatSession).filter(
        ChatSession.user_id == user_id
    ).order_by(Message.created_at.desc()).limit(100).all()
    
    avg_response_time = None
    if len(user_messages) > 1:
        # Calculer la différence moyenne entre les messages consécutifs
        time_diffs = []
        for i in range(len(user_messages) - 1):
            diff = (user_messages[i][0] - user_messages[i + 1][0]).total_seconds()
            if diff < 3600:  # Ignorer les différences > 1h (probablement différentes sessions)
                time_diffs.append(diff)
        
        if time_diffs:
            avg_response_time = sum(time_diffs) / len(time_diffs)
    
    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "total_documents": total_documents,
        "shared_sessions": shared_sessions,
        "recent_activity": recent_activity,
        "module_usage": module_stats,
        "role_distribution": role_stats,
        "daily_messages": [
            {
                "date": str(daily_date),
                "count": count
            }
            for daily_date, count in daily_messages
        ],
        "daily_sessions": [
            {
                "date": str(session_date),
                "count": count
            }
            for session_date, count in daily_sessions
        ],
        "average_response_time_seconds": round(avg_response_time, 2) if avg_response_time else None,
        "period_days": days,
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat()
    }


def get_usage_trends(
    db: Session,
    user_id: int,
    days: int = 30
) -> Dict:
    """
    Calcule les tendances d'utilisation sur une période
    
    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
        days: Nombre de jours
    
    Returns:
        Dictionnaire avec les tendances
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Tendance des messages (croissance)
    messages_trend = db.query(
        func.date(Message.created_at).label('date'),
        func.count(Message.id).label('count')
    ).join(ChatSession).filter(
        ChatSession.user_id == user_id,
        Message.created_at >= start_date
    ).group_by(func.date(Message.created_at)).order_by('date').all()
    
    # Tendance des modules (évolution de l'utilisation)
    module_trends = {}
    for module in ["general", "grammar", "qa", "reformulation"]:
        module_messages = db.query(
            func.date(Message.created_at).label('date'),
            func.count(Message.id).label('count')
        ).join(ChatSession).filter(
            ChatSession.user_id == user_id,
            Message.module_type == module,
            Message.created_at >= start_date
        ).group_by(func.date(Message.created_at)).order_by('date').all()
        
        module_trends[module] = [
            {
                "date": str(msg_date),
                "count": count
            }
            for msg_date, count in module_messages
        ]
    
    return {
        "messages_trend": [
            {
                "date": str(msg_date),
                "count": count
            }
            for msg_date, count in messages_trend
        ],
        "module_trends": module_trends,
        "period_days": days
    }


def get_performance_metrics(
    db: Session,
    user_id: int
) -> Dict:
    """
    Calcule les métriques de performance basées sur l'utilisation
    
    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    
    Returns:
        Dictionnaire avec les métriques de performance
    """
    # Sessions actives (créées dans les 7 derniers jours)
    active_sessions = db.query(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    # Messages moyens par session
    sessions_with_counts = db.query(
        ChatSession.id,
        func.count(Message.id).label('message_count')
    ).outerjoin(Message).filter(
        ChatSession.user_id == user_id
    ).group_by(ChatSession.id).all()
    
    avg_messages_per_session = 0
    if sessions_with_counts:
        message_counts = [count for _, count in sessions_with_counts]
        avg_messages_per_session = sum(message_counts) / len(message_counts) if message_counts else 0
    
    # Module le plus utilisé
    most_used_module = db.query(
        Message.module_type,
        func.count(Message.id).label('count')
    ).join(ChatSession).filter(
        ChatSession.user_id == user_id
    ).group_by(Message.module_type).order_by(func.count(Message.id).desc()).first()
    
    return {
        "active_sessions": active_sessions,
        "average_messages_per_session": round(avg_messages_per_session, 2),
        "most_used_module": most_used_module[0] if most_used_module else None,
        "most_used_module_count": most_used_module[1] if most_used_module else 0
    }

