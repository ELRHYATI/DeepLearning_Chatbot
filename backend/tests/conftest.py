"""
Pytest configuration and shared fixtures
"""
import pytest
import os
import tempfile
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from typing import Generator

# Set test environment variables before importing app
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///./test_chatbot.db"

from app.database import Base, get_db
from app.main import app
from app.models import User
from app.services.grammar_service import GrammarService
from app.services.qa_service import QAService
from app.services.reformulation_service import ReformulationService
from app.services.rag_service import RAGService


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_chatbot.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        # Clean up test database file (with retry for Windows)
        import time
        if os.path.exists("./test_chatbot.db"):
            try:
                os.remove("./test_chatbot.db")
            except PermissionError:
                # Wait a bit and try again (Windows file locking)
                time.sleep(0.1)
                try:
                    os.remove("./test_chatbot.db")
                except PermissionError:
                    pass  # Skip if still locked


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=pwd_context.hash("testpassword123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Get authentication headers for test user"""
    from jose import jwt
    from datetime import datetime, timedelta
    from app.routers.auth import SECRET_KEY, ALGORITHM
    
    expire = datetime.utcnow() + timedelta(hours=24)
    token_data = {"sub": test_user.email, "exp": expire}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def temp_dir():
    """Create a temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # Clean up with retry for Windows file locking
    import time
    try:
        shutil.rmtree(temp_path)
    except PermissionError:
        # Wait a bit and try again (Windows file locking)
        time.sleep(0.2)
        try:
            shutil.rmtree(temp_path, ignore_errors=True)
        except Exception:
            pass  # Skip if still locked


@pytest.fixture(scope="function")
def grammar_service():
    """Create a GrammarService instance for testing"""
    return GrammarService()


@pytest.fixture(scope="function")
def qa_service():
    """Create a QAService instance for testing"""
    # Note: This will load the model, which is slow
    # Use pytest.mark.slow for tests that need this
    return QAService()


@pytest.fixture(scope="function")
def reformulation_service():
    """Create a ReformulationService instance for testing"""
    # Note: This will load the model, which is slow
    return ReformulationService()


@pytest.fixture(scope="function")
def rag_service(temp_dir):
    """Create a RAGService instance with temporary directory"""
    return RAGService(persist_directory=os.path.join(temp_dir, "chroma_test"))


@pytest.fixture(scope="function")
def sample_text():
    """Sample French text with errors for testing"""
    return "Je suis allé a la bibliothèque hier. Il y avait beaucoup de livres interessants."


@pytest.fixture(scope="function")
def sample_question():
    """Sample question for QA testing"""
    return "Qu'est-ce que la photosynthèse?"


@pytest.fixture(scope="function")
def sample_context():
    """Sample context for QA testing"""
    return """
    La photosynthèse est le processus par lequel les plantes utilisent la lumière du soleil,
    l'eau et le dioxyde de carbone pour produire de l'oxygène et de l'énergie sous forme de glucose.
    Ce processus est essentiel pour la vie sur Terre.
    """


@pytest.fixture(scope="function")
def sample_document_path(temp_dir):
    """Create a sample text document for testing"""
    doc_path = os.path.join(temp_dir, "test_document.txt")
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write("""
        Ceci est un document de test pour le système RAG.
        Il contient des informations sur l'intelligence artificielle.
        L'IA est utilisée dans de nombreux domaines comme la médecine, l'éducation et la recherche.
        """)
    return doc_path

