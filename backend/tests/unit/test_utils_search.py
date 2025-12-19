"""
Unit tests for Search utilities
"""
import pytest
from unittest.mock import Mock, patch
from app.utils.search import (
    search_messages_fulltext,
    search_sessions,
    get_search_suggestions
)
from app.models import User, ChatSession, Message


@pytest.mark.unit
class TestSearchUtils:
    """Test suite for Search utilities"""
    
    def test_search_messages_fulltext(self, db_session, test_user):
        """Test fulltext message search"""
        # Create test data
        session = ChatSession(user_id=test_user.id, title="Test Session")
        db_session.add(session)
        db_session.commit()
        
        message = Message(
            session_id=session.id,
            role="user",
            content="Test search content",
            module_type="general"
        )
        db_session.add(message)
        db_session.commit()
        
        results = search_messages_fulltext(
            db_session,
            test_user.id,
            query="search",
            limit=10
        )
        
        assert isinstance(results, dict)
        assert "results" in results
        assert isinstance(results["results"], list)
    
    def test_search_sessions(self, db_session, test_user):
        """Test session search"""
        session = ChatSession(user_id=test_user.id, title="Test Session")
        db_session.add(session)
        db_session.commit()
        
        results = search_sessions(
            db_session,
            test_user.id,
            query="Test",
            limit=10
        )
        
        assert isinstance(results, dict)
        assert "results" in results
        assert isinstance(results["results"], list)
    
    def test_get_search_suggestions(self, db_session, test_user):
        """Test getting search suggestions"""
        suggestions = get_search_suggestions(
            db_session,
            test_user.id,
            query="test"
        )
        
        assert isinstance(suggestions, list)

