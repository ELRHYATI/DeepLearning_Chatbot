from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./academic_chatbot.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from app.models import User, ChatSession, Message, Document, Feedback, APIKey, CollaborationSession, FineTuningJob, MessageCorrection
    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)
    
    # Exécuter les migrations pour les colonnes manquantes
    try:
        migrate_sharing_columns()
    except Exception as e:
        # Log l'erreur mais ne pas bloquer le démarrage
        import logging
        logging.warning(f"Could not run sharing migration: {e}")


def migrate_sharing_columns():
    """Ajoute les colonnes share_token et is_shared si elles n'existent pas"""
    import sqlite3
    
    # Extraire le chemin de la base de données depuis l'URL
    db_url = SQLALCHEMY_DATABASE_URL
    if "sqlite" in db_url:
        # Format: sqlite:///./academic_chatbot.db
        db_path = db_url.replace("sqlite:///", "").replace("./", "")
        if not os.path.exists(db_path):
            return  # La base de données sera créée avec toutes les colonnes
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Vérifier si les colonnes existent déjà
            cursor.execute("PRAGMA table_info(chat_sessions)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Ajouter share_token si manquant
            if 'share_token' not in columns:
                cursor.execute("ALTER TABLE chat_sessions ADD COLUMN share_token VARCHAR")
            
            # Ajouter is_shared si manquant
            if 'is_shared' not in columns:
                cursor.execute("ALTER TABLE chat_sessions ADD COLUMN is_shared BOOLEAN DEFAULT 0")
            
            # Créer un index unique sur share_token si nécessaire
            try:
                cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_chat_sessions_share_token ON chat_sessions(share_token)")
            except sqlite3.OperationalError:
                pass  # L'index existe peut-être déjà
            
            conn.commit()
            conn.close()
        except Exception as e:
            # Si la migration échoue, ce n'est pas critique - les nouvelles bases de données auront les colonnes
            pass

