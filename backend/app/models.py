from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="New Chat")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    share_token = Column(String, unique=True, index=True, nullable=True)  # Token pour le partage
    is_shared = Column(Boolean, default=False)  # Indique si la session est partagée
    
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String)  # "user" or "assistant"
    content = Column(Text)
    module_type = Column(String)  # "grammar", "qa", "reformulation", "general"
    message_metadata = Column(Text)  # JSON string for additional data (renamed from metadata to avoid SQLAlchemy conflict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("ChatSession", back_populates="messages")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String)
    file_path = Column(String)
    file_type = Column(String)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(Boolean, default=False)
    
    user = relationship("User")

class Feedback(Base):
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer)  # 1 for 👍 (positive), -1 for 👎 (negative)
    comment = Column(Text, nullable=True)  # Optional comment from user
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    message = relationship("Message")
    user = relationship("User")

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_name = Column(String, nullable=False)  # Nom descriptif de la clé
    api_key = Column(String, unique=True, index=True, nullable=False)  # La clé API (hashée)
    key_hash = Column(String, nullable=False)  # Hash de la clé pour vérification
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optionnel: expiration
    
    user = relationship("User")

class CollaborationSession(Base):
    __tablename__ = "collaboration_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, default="viewer")  # owner, editor, viewer
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("ChatSession")
    user = relationship("User")

class FineTuningJob(Base):
    __tablename__ = "fine_tuning_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_name = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # grammar, qa, reformulation
    training_data = Column(Text, nullable=False)  # JSON string avec les données d'entraînement
    status = Column(String, default="pending")  # pending, training, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    model_path = Column(String, nullable=True)  # Chemin vers le modèle fine-tuné
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    user = relationship("User")

class MessageCorrection(Base):
    __tablename__ = "message_corrections"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_content = Column(Text, nullable=False)  # Contenu original de l'IA
    corrected_content = Column(Text, nullable=False)  # Contenu corrigé par l'utilisateur
    correction_type = Column(String, nullable=False)  # grammar, qa, reformulation, general
    correction_notes = Column(Text, nullable=True)  # Notes explicatives de l'utilisateur
    is_used_for_learning = Column(Boolean, default=True)  # Si la correction est utilisée pour l'apprentissage
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    message = relationship("Message")
    user = relationship("User")

