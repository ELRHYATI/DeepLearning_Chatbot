"""
Comprehensive unit tests for QA Service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.qa_service import QAService


@pytest.mark.unit
class TestQAServiceComprehensive:
    """Comprehensive test suite for QA Service"""
    
    @patch('app.services.qa_service.pipeline')
    def test_qa_service_initialization(self, mock_pipeline):
        """Test QA service initialization"""
        service = QAService()
        assert service is not None
    
    @patch('app.services.qa_service.QAService._load_model')
    def test_answer_question_basic(self, mock_load):
        """Test answering a basic question"""
        service = QAService()
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [{
            "answer": "Test answer",
            "score": 0.9
        }]
        service.qa_pipeline = mock_pipeline
        
        result = service.answer_question(
            question="What is AI?",
            context="AI is artificial intelligence."
        )
        
        assert result is not None
        assert isinstance(result, str) or isinstance(result, dict)
    
    @patch('app.services.qa_service.QAService._load_model')
    def test_answer_question_no_context(self, mock_load):
        """Test answering question without context"""
        service = QAService()
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [{
            "answer": "No answer",
            "score": 0.1
        }]
        service.qa_pipeline = mock_pipeline
        
        result = service.answer_question(
            question="What is AI?",
            context=""
        )
        
        assert result is not None
    
    @patch('app.services.qa_service.QAService._load_model')
    def test_answer_question_empty_question(self, mock_load):
        """Test answering empty question"""
        service = QAService()
        result = service.answer_question(
            question="",
            context="Some context"
        )
        
        # Should handle gracefully
        assert result is not None or result == ""
    
    @patch('app.services.qa_service.QAService._load_model')
    def test_build_context_from_history(self, mock_load):
        """Test building context from message history"""
        service = QAService()
        messages = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "Question 2"}
        ]
        
        context = service._build_context_from_history(messages)
        
        assert isinstance(context, str)
        assert len(context) > 0
    
    @patch('app.services.qa_service.QAService._load_model')
    def test_build_context_empty_history(self, mock_load):
        """Test building context from empty history"""
        service = QAService()
        context = service._build_context_from_history([])
        
        assert isinstance(context, str)
    
    @patch('app.services.qa_service.QAService._load_model')
    @patch('app.services.qa_service.RAGService')
    def test_answer_question_with_rag(self, mock_rag_class, mock_load):
        """Test answering question with RAG"""
        service = QAService()
        mock_rag = MagicMock()
        mock_rag.retrieve_context.return_value = [
            {"content": "Context from RAG", "score": 0.8}
        ]
        mock_rag_class.return_value = mock_rag
        
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [{
            "answer": "RAG answer",
            "score": 0.9
        }]
        service.qa_pipeline = mock_pipeline
        
        result = service.answer_question(
            question="What is AI?",
            context="",
            use_rag=True,
            user_id=1
        )
        
        assert result is not None
    
    @patch('app.services.qa_service.QAService._load_model')
    def test_answer_question_low_confidence(self, mock_load):
        """Test handling low confidence answer"""
        service = QAService()
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [{
            "answer": "Uncertain answer",
            "score": 0.1
        }]
        service.qa_pipeline = mock_pipeline
        
        result = service.answer_question(
            question="What is AI?",
            context="Some context"
        )
        
        assert result is not None
    
    @patch('app.services.qa_service.QAService._load_model')
    def test_answer_question_multiple_answers(self, mock_load):
        """Test handling multiple answer candidates"""
        service = QAService()
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [
            {"answer": "Answer 1", "score": 0.9},
            {"answer": "Answer 2", "score": 0.7}
        ]
        service.qa_pipeline = mock_pipeline
        
        result = service.answer_question(
            question="What is AI?",
            context="Some context"
        )
        
        assert result is not None

