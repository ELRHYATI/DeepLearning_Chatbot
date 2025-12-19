"""
Utilitaires pour la recherche full-text dans l'historique
"""
from typing import List, Dict, Optional
from datetime import datetime, date
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Session
from app.models import ChatSession, Message
from app.utils.logger import get_logger

logger = get_logger()


def search_messages_fulltext(
    db: Session,
    user_id: int,
    query: str,
    module_type: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    role: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict:
    """
    Recherche full-text dans les messages avec filtres
    
    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
        query: Terme de recherche
        module_type: Filtrer par type de module (grammar, qa, reformulation, general)
        date_from: Date de début (optionnel)
        date_to: Date de fin (optionnel)
        role: Filtrer par rôle (user, assistant)
        limit: Nombre maximum de résultats
        offset: Offset pour la pagination
    
    Returns:
        Dictionnaire avec les résultats et métadonnées
    """
    # Construire la requête de base
    base_query = db.query(Message).join(ChatSession).filter(
        ChatSession.user_id == user_id
    )
    
    # Recherche full-text dans le contenu
    if query:
        search_term = f"%{query}%"
        base_query = base_query.filter(
            or_(
                Message.content.ilike(search_term),
                ChatSession.title.ilike(search_term)
            )
        )
    
    # Filtres
    filters = []
    
    if module_type:
        filters.append(Message.module_type == module_type)
    
    if role:
        filters.append(Message.role == role)
    
    if date_from:
        filters.append(func.date(Message.created_at) >= date_from)
    
    if date_to:
        filters.append(func.date(Message.created_at) <= date_to)
    
    if filters:
        base_query = base_query.filter(and_(*filters))
    
    # Compter le total avant pagination
    total = base_query.count()
    
    # Appliquer pagination et tri
    results = base_query.order_by(
        Message.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    # Formater les résultats
    formatted_results = []
    for message in results:
        formatted_results.append({
            "id": message.id,
            "session_id": message.session_id,
            "session_title": message.session.title,
            "role": message.role,
            "content": message.content,
            "module_type": message.module_type,
            "created_at": message.created_at.isoformat() if message.created_at else None,
            "highlight": _highlight_text(message.content, query) if query else message.content
        })
    
    return {
        "results": formatted_results,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total
    }


def search_sessions(
    db: Session,
    user_id: int,
    query: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    module_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> Dict:
    """
    Recherche dans les sessions avec filtres
    
    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
        query: Terme de recherche dans le titre
        date_from: Date de début (optionnel)
        date_to: Date de fin (optionnel)
        module_type: Filtrer par type de module utilisé dans les messages
        limit: Nombre maximum de résultats
        offset: Offset pour la pagination
    
    Returns:
        Dictionnaire avec les résultats et métadonnées
    """
    base_query = db.query(ChatSession).filter(
        ChatSession.user_id == user_id
    )
    
    # Recherche dans le titre
    if query:
        search_term = f"%{query}%"
        base_query = base_query.filter(
            ChatSession.title.ilike(search_term)
        )
    
    # Filtres de date
    filters = []
    
    if date_from:
        filters.append(func.date(ChatSession.created_at) >= date_from)
    
    if date_to:
        filters.append(func.date(ChatSession.created_at) <= date_to)
    
    if filters:
        base_query = base_query.filter(and_(*filters))
    
    # Filtrer par module_type si spécifié
    if module_type:
        base_query = base_query.join(Message).filter(
            Message.module_type == module_type
        ).distinct()
    
    # Compter le total
    total = base_query.count()
    
    # Appliquer pagination et tri
    results = base_query.order_by(
        ChatSession.updated_at.desc()
    ).offset(offset).limit(limit).all()
    
    # Formater les résultats
    formatted_results = []
    for session in results:
        # Compter les messages par module
        module_counts = {}
        for msg in session.messages:
            module = msg.module_type or "general"
            module_counts[module] = module_counts.get(module, 0) + 1
        
        formatted_results.append({
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "message_count": len(session.messages),
            "module_counts": module_counts,
            "is_shared": session.is_shared
        })
    
    return {
        "results": formatted_results,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total
    }


def _highlight_text(text: str, query: str, max_length: int = 200) -> str:
    """
    Met en évidence le terme de recherche dans le texte
    
    Args:
        text: Texte à traiter
        query: Terme de recherche
        max_length: Longueur maximale du texte retourné
    
    Returns:
        Texte avec le terme mis en évidence
    """
    if not query or not text:
        return text[:max_length] + "..." if len(text) > max_length else text
    
    query_lower = query.lower()
    text_lower = text.lower()
    
    # Trouver la position du terme
    pos = text_lower.find(query_lower)
    
    if pos == -1:
        # Si pas trouvé, retourner le début du texte
        return text[:max_length] + "..." if len(text) > max_length else text
    
    # Extraire un contexte autour du terme
    start = max(0, pos - 50)
    end = min(len(text), pos + len(query) + 50)
    
    context = text[start:end]
    
    # Mettre en évidence le terme (simple, le frontend peut faire mieux)
    highlighted = context.replace(
        query,
        f"**{query}**",
        1
    )
    
    if start > 0:
        highlighted = "..." + highlighted
    if end < len(text):
        highlighted = highlighted + "..."
    
    return highlighted


def get_search_suggestions(
    db: Session,
    user_id: int,
    query: str,
    limit: int = 10
) -> List[str]:
    """
    Obtient des suggestions de recherche basées sur l'historique
    
    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
        query: Terme de recherche partiel
        limit: Nombre maximum de suggestions
    
    Returns:
        Liste de suggestions
    """
    if len(query) < 2:
        return []
    
    search_term = f"%{query}%"
    
    # Rechercher dans les titres de sessions
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.title.ilike(search_term)
    ).limit(limit).all()
    
    suggestions = [s.title for s in sessions]
    
    # Rechercher des mots-clés dans les messages
    messages = db.query(Message.content).join(ChatSession).filter(
        ChatSession.user_id == user_id,
        Message.content.ilike(search_term)
    ).limit(limit).all()
    
    # Extraire des mots-clés des messages
    for msg_content, in messages:
        words = msg_content.split()
        for word in words:
            if query.lower() in word.lower() and word not in suggestions:
                suggestions.append(word)
                if len(suggestions) >= limit:
                    break
        if len(suggestions) >= limit:
            break
    
    return suggestions[:limit]

