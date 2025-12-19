"""
Router pour la collaboration en temps réel
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from app.database import get_db
from app.models import User, ChatSession, Message, CollaborationSession
from app.routers.auth import get_current_user
from app.utils.logger import get_logger
from datetime import datetime
import json

logger = get_logger()

router = APIRouter()

# Stockage des connexions WebSocket actives
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}  # {session_id: [websockets]}
        self.user_connections: Dict[int, Dict[int, WebSocket]] = {}  # {session_id: {user_id: websocket}}
    
    async def connect(self, websocket: WebSocket, session_id: int, user_id: int):
        """Connecte un utilisateur à une session"""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        if session_id not in self.user_connections:
            self.user_connections[session_id] = {}
        
        self.active_connections[session_id].append(websocket)
        self.user_connections[session_id][user_id] = websocket
        
        logger.info(
            f"User {user_id} connected to session {session_id}",
            extra_data={"event": "websocket_connect", "user_id": user_id, "session_id": session_id}
        )
    
    def disconnect(self, websocket: WebSocket, session_id: int, user_id: int):
        """Déconnecte un utilisateur d'une session"""
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
        
        if session_id in self.user_connections:
            if user_id in self.user_connections[session_id]:
                del self.user_connections[session_id][user_id]
        
        logger.info(
            f"User {user_id} disconnected from session {session_id}",
            extra_data={"event": "websocket_disconnect", "user_id": user_id, "session_id": session_id}
        )
    
    async def broadcast_to_session(self, session_id: int, message: dict, exclude_user: int = None):
        """Diffuse un message à tous les utilisateurs d'une session"""
        if session_id not in self.active_connections:
            return
        
        disconnected = []
        for websocket in self.active_connections[session_id]:
            # Exclure l'expéditeur si spécifié
            if exclude_user and session_id in self.user_connections:
                for uid, ws in self.user_connections[session_id].items():
                    if ws == websocket and uid == exclude_user:
                        continue
            
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to websocket: {e}")
                disconnected.append(websocket)
        
        # Nettoyer les connexions déconnectées
        for ws in disconnected:
            if session_id in self.active_connections:
                self.active_connections[session_id].remove(ws)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Envoie un message personnel"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

manager = ConnectionManager()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: int,
    token: str = None,
    db: Session = Depends(get_db)
):
    """
    Endpoint WebSocket pour la collaboration en temps réel
    
    Args:
        websocket: Connexion WebSocket
        session_id: ID de la session de chat
        token: Token JWT pour authentification
        db: Session de base de données
    """
    # Authentifier l'utilisateur
    user = None
    if token:
        try:
            from jose import jwt
            import os
            SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            email = payload.get("sub")
            if email:
                user = db.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            await websocket.close(code=1008, reason="Authentication failed")
            return
    
    if not user:
        await websocket.close(code=1008, reason="Authentication required")
        return
    
    # Vérifier que la session existe et que l'utilisateur y a accès
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        await websocket.close(code=1008, reason="Session not found")
        return
    
    # Vérifier les permissions (propriétaire ou session partagée)
    if session.user_id != user.id and not session.is_shared:
        await websocket.close(code=1008, reason="Access denied")
        return
    
    # Enregistrer la collaboration
    collaboration = db.query(CollaborationSession).filter(
        CollaborationSession.session_id == session_id,
        CollaborationSession.user_id == user.id
    ).first()
    
    if not collaboration:
        collaboration = CollaborationSession(
            session_id=session_id,
            user_id=user.id,
            role="editor" if session.user_id == user.id else "viewer"
        )
        db.add(collaboration)
        db.commit()
    
    # Connecter
    await manager.connect(websocket, session_id, user.id)
    
    # Envoyer un message de bienvenue
    await manager.send_personal_message({
        "type": "connected",
        "message": f"Connecté à la session {session_id}",
        "user_id": user.id,
        "username": user.username
    }, websocket)
    
    # Notifier les autres utilisateurs
    await manager.broadcast_to_session(session_id, {
        "type": "user_joined",
        "user_id": user.id,
        "username": user.username,
        "timestamp": datetime.utcnow().isoformat()
    }, exclude_user=user.id)
    
    try:
        while True:
            # Recevoir les messages
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type")
            
            if message_type == "message":
                # Nouveau message de chat
                content = message_data.get("content")
                module_type = message_data.get("module_type", "general")
                
                # Sauvegarder le message
                new_message = Message(
                    session_id=session_id,
                    role="user",
                    content=content,
                    module_type=module_type
                )
                db.add(new_message)
                db.commit()
                db.refresh(new_message)
                
                # Diffuser le message à tous les participants
                await manager.broadcast_to_session(session_id, {
                    "type": "new_message",
                    "message": {
                        "id": new_message.id,
                        "role": new_message.role,
                        "content": new_message.content,
                        "module_type": new_message.module_type,
                        "created_at": new_message.created_at.isoformat()
                    },
                    "user_id": user.id,
                    "username": user.username,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message_type == "typing":
                # Indicateur de frappe
                await manager.broadcast_to_session(session_id, {
                    "type": "typing",
                    "user_id": user.id,
                    "username": user.username,
                    "is_typing": message_data.get("is_typing", True),
                    "timestamp": datetime.utcnow().isoformat()
                }, exclude_user=user.id)
            
            elif message_type == "cursor":
                # Position du curseur (pour édition collaborative)
                await manager.broadcast_to_session(session_id, {
                    "type": "cursor",
                    "user_id": user.id,
                    "username": user.username,
                    "position": message_data.get("position"),
                    "timestamp": datetime.utcnow().isoformat()
                }, exclude_user=user.id)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id, user.id)
        # Notifier les autres utilisateurs
        await manager.broadcast_to_session(session_id, {
            "type": "user_left",
            "user_id": user.id,
            "username": user.username,
            "timestamp": datetime.utcnow().isoformat()
        })


@router.get("/sessions/{session_id}/collaborators")
async def get_collaborators(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère la liste des collaborateurs d'une session
    
    Args:
        session_id: ID de la session
        db: Session de base de données
        current_user: Utilisateur actuel
    
    Returns:
        Liste des collaborateurs
    """
    # Vérifier les permissions
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    if session.user_id != current_user.id and not session.is_shared:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Récupérer les collaborateurs
    collaborators = db.query(CollaborationSession).filter(
        CollaborationSession.session_id == session_id
    ).all()
    
    return {
        "collaborators": [
            {
                "user_id": col.user_id,
                "role": col.role,
                "joined_at": col.joined_at.isoformat(),
                "last_active": col.last_active.isoformat()
            }
            for col in collaborators
        ]
    }

