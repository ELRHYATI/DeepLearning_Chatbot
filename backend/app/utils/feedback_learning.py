"""
Système d'apprentissage basé sur les feedbacks
"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models import Feedback, Message, ChatSession
from app.utils.logger import get_logger

logger = get_logger()


def analyze_feedback_patterns(
    db: Session,
    user_id: Optional[int] = None,
    module_type: Optional[str] = None
) -> Dict:
    """
    Analyse les patterns de feedback pour identifier les problèmes récurrents
    
    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur (optionnel, pour analyse globale si None)
        module_type: Type de module à analyser (optionnel)
    
    Returns:
        Dictionnaire avec les patterns identifiés
    """
    query = db.query(Feedback, Message).join(Message).join(ChatSession)
    
    if user_id:
        query = query.filter(ChatSession.user_id == user_id)
    
    if module_type:
        query = query.filter(Message.module_type == module_type)
    
    # Compter les feedbacks négatifs par module
    negative_feedbacks = query.filter(Feedback.rating == -1).all()
    
    module_issues = {}
    for feedback, message in negative_feedbacks:
        module = message.module_type or "general"
        if module not in module_issues:
            module_issues[module] = {
                "count": 0,
                "messages": []
            }
        module_issues[module]["count"] += 1
        if len(module_issues[module]["messages"]) < 5:  # Garder les 5 derniers exemples
            module_issues[module]["messages"].append({
                "message_id": message.id,
                "content_preview": message.content[:100] if message.content else "",
                "feedback_comment": feedback.comment
            })
    
    # Calculer le taux de satisfaction par module
    satisfaction_by_module = {}
    for module in ["general", "grammar", "qa", "reformulation"]:
        module_query = query.filter(Message.module_type == module)
        positive = module_query.filter(Feedback.rating == 1).count()
        negative = module_query.filter(Feedback.rating == -1).count()
        total = positive + negative
        
        if total > 0:
            satisfaction_by_module[module] = {
                "satisfaction_rate": round((positive / total) * 100, 2),
                "total_feedbacks": total,
                "positive": positive,
                "negative": negative
            }
    
    return {
        "module_issues": module_issues,
        "satisfaction_by_module": satisfaction_by_module,
        "total_negative_feedbacks": len(negative_feedbacks)
    }


def get_improvement_suggestions(
    db: Session,
    user_id: Optional[int] = None
) -> List[Dict]:
    """
    Génère des suggestions d'amélioration basées sur les feedbacks
    
    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur (optionnel)
    
    Returns:
        Liste de suggestions d'amélioration
    """
    patterns = analyze_feedback_patterns(db, user_id)
    suggestions = []
    
    # Suggérer des améliorations pour les modules avec faible satisfaction
    for module, stats in patterns["satisfaction_by_module"].items():
        if stats["satisfaction_rate"] < 70 and stats["total_feedbacks"] >= 3:
            suggestions.append({
                "type": "low_satisfaction",
                "module": module,
                "satisfaction_rate": stats["satisfaction_rate"],
                "recommendation": f"Le module {module} a un taux de satisfaction de {stats['satisfaction_rate']}%. "
                                 f"Considérer d'améliorer les réponses pour ce module.",
                "priority": "high" if stats["satisfaction_rate"] < 50 else "medium"
            })
    
    # Identifier les problèmes récurrents
    for module, issues in patterns["module_issues"].items():
        if issues["count"] >= 3:
            suggestions.append({
                "type": "recurring_issue",
                "module": module,
                "issue_count": issues["count"],
                "recommendation": f"Le module {module} a {issues['count']} feedbacks négatifs. "
                                 f"Analyser les commentaires pour identifier les problèmes communs.",
                "priority": "high",
                "sample_messages": issues["messages"]
            })
    
    return suggestions


def get_user_feedback_summary(
    db: Session,
    user_id: int
) -> Dict:
    """
    Récupère un résumé des feedbacks d'un utilisateur
    
    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    
    Returns:
        Résumé des feedbacks
    """
    total_feedbacks = db.query(func.count(Feedback.id)).filter(
        Feedback.user_id == user_id
    ).scalar() or 0
    
    positive_feedbacks = db.query(func.count(Feedback.id)).filter(
        Feedback.user_id == user_id,
        Feedback.rating == 1
    ).scalar() or 0
    
    negative_feedbacks = db.query(func.count(Feedback.id)).filter(
        Feedback.user_id == user_id,
        Feedback.rating == -1
    ).scalar() or 0
    
    # Feedback récent (derniers 7 jours)
    from datetime import datetime, timedelta
    recent_date = datetime.utcnow() - timedelta(days=7)
    recent_feedbacks = db.query(func.count(Feedback.id)).filter(
        Feedback.user_id == user_id,
        Feedback.created_at >= recent_date
    ).scalar() or 0
    
    return {
        "total_feedbacks": total_feedbacks,
        "positive_feedbacks": positive_feedbacks,
        "negative_feedbacks": negative_feedbacks,
        "recent_feedbacks": recent_feedbacks,
        "satisfaction_rate": round((positive_feedbacks / total_feedbacks * 100), 2) if total_feedbacks > 0 else 0
    }

