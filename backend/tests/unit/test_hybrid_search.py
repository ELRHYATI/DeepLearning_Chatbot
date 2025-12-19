"""
Unit tests for Hybrid Search utility
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.utils.hybrid_search import HybridSearch
from app.models import Message, ChatSession


@pytest.mark.unit
class TestHybridSearch:
    """Test suite for Hybrid Search"""
    
    def test_hybrid_search_initialization(self):
        """Test HybridSearch initialization"""
        search = HybridSearch()
        assert search is not None
        assert hasattr(search, 'bm25_available')
    
    def test_tokenize_basic(self):
        """Test basic tokenization"""
        search = HybridSearch()
        text = "Hello world test"
        tokens = search._tokenize(text)
        
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert all(isinstance(t, str) for t in tokens)
    
    def test_tokenize_with_punctuation(self):
        """Test tokenization with punctuation"""
        search = HybridSearch()
        text = "Hello, world! Test."
        tokens = search._tokenize(text)
        
        assert isinstance(tokens, list)
        # Should remove punctuation
        assert all(not any(c in t for c in ',!.') for t in tokens)
    
    def test_tokenize_filters_stop_words(self):
        """Test that stop words are filtered"""
        search = HybridSearch()
        text = "le la les un une test"
        tokens = search._tokenize(text)
        
        # Should filter out stop words
        assert "le" not in tokens
        assert "la" not in tokens
        assert "test" in tokens or len(tokens) == 0
    
    def test_build_bm25_index_empty(self):
        """Test building BM25 index with empty documents"""
        search = HybridSearch()
        result = search._build_bm25_index([])
        
        assert result is None
    
    def test_build_bm25_index_with_documents(self):
        """Test building BM25 index with documents"""
        search = HybridSearch()
        documents = ["Hello world", "Test document", "Another test"]
        result = search._build_bm25_index(documents)
        
        # Should return something (index or dict)
        assert result is not None
    
    @patch('app.utils.hybrid_search.BM25_AVAILABLE', False)
    def test_build_bm25_index_fallback(self):
        """Test BM25 fallback implementation"""
        search = HybridSearch()
        documents = ["Hello world", "Test document"]
        result = search._build_bm25_index(documents)
        
        # Should use fallback
        assert result is not None
    
    
    def test_hybrid_search_basic(self, db_session):
        """Test hybrid search functionality"""
        search = HybridSearch()
        
        # Create test session
        session = ChatSession(user_id=1, title="Test")
        db_session.add(session)
        db_session.commit()
        
        # Create test messages
        msg1 = Message(
            session_id=session.id,
            role="user",
            content="Hello world test",
            module_type="general"
        )
        db_session.add(msg1)
        db_session.commit()
        
        results = search.hybrid_search(
            db=db_session,
            user_id=1,
            query="test",
            k=10
        )
        
        assert isinstance(results, list)
    
    def test_simple_similarity(self):
        """Test simple similarity calculation"""
        search = HybridSearch()
        
        score = search._simple_similarity("hello world", "hello test")
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_simple_similarity_empty(self):
        """Test similarity with empty strings"""
        search = HybridSearch()
        
        score = search._simple_similarity("", "test")
        
        assert score == 0.0

