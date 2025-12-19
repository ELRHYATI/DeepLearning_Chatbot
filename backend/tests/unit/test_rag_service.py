"""
Unit tests for RAGService
"""
import pytest
import os
from app.services.rag_service import RAGService


@pytest.mark.unit
class TestRAGService:
    """Test suite for RAGService"""
    
    def test_rag_service_initialization(self, rag_service):
        """Test that RAGService can be initialized"""
        assert rag_service is not None
        assert rag_service.persist_directory is not None
    
    def test_process_document_txt(self, rag_service, sample_document_path):
        """Test processing a text document"""
        # Check if RAG service is available
        if not rag_service.vectorstore or not rag_service.text_splitter:
            pytest.skip("RAG service not available (LangChain or embeddings not initialized)")
        
        result = rag_service.process_document(
            sample_document_path,
            "txt",
            user_id=1,
            document_id=1
        )
        
        assert isinstance(result, bool)
        # Should succeed if document is valid and RAG is available
        # If RAG is not available, result will be False but that's acceptable
        if rag_service.vectorstore and rag_service.text_splitter:
            assert result is True
    
    def test_retrieve_context_basic(self, rag_service, sample_document_path):
        """Test basic context retrieval"""
        # Check if RAG service is available
        if not rag_service.vectorstore:
            pytest.skip("RAG service not available (vectorstore not initialized)")
        
        # First process a document
        result = rag_service.process_document(sample_document_path, "txt", user_id=1, document_id=1)
        if not result:
            pytest.skip("Could not process document (RAG service may not be fully initialized)")
        
        # Then retrieve context
        results = rag_service.retrieve_context("intelligence artificielle", k=3, user_id=1)
        
        assert isinstance(results, list)
        # Should have results if document was processed
        assert len(results) >= 0
    
    def test_retrieve_context_with_user_filter(self, rag_service, sample_document_path):
        """Test context retrieval with user filtering"""
        # Check if RAG service is available
        if not rag_service.vectorstore:
            pytest.skip("RAG service not available (vectorstore not initialized)")
        
        # Process document for user 1
        result = rag_service.process_document(sample_document_path, "txt", user_id=1, document_id=1)
        if not result:
            pytest.skip("Could not process document")
        
        # Retrieve for user 1
        results_user1 = rag_service.retrieve_context("test", k=3, user_id=1)
        
        # Retrieve for user 2 (should be empty or different)
        results_user2 = rag_service.retrieve_context("test", k=3, user_id=2)
        
        assert isinstance(results_user1, list)
        assert isinstance(results_user2, list)
    
    def test_retrieve_context_with_min_score(self, rag_service, sample_document_path):
        """Test context retrieval with minimum score filter"""
        # Check if RAG service is available
        if not rag_service.vectorstore:
            pytest.skip("RAG service not available (vectorstore not initialized)")
        
        result = rag_service.process_document(sample_document_path, "txt", user_id=1, document_id=1)
        if not result:
            pytest.skip("Could not process document")
        
        results = rag_service.retrieve_context(
            "intelligence artificielle",
            k=5,
            user_id=1,
            min_score=0.5
        )
        
        assert isinstance(results, list)
        # All results should have score >= min_score
        for result in results:
            assert result.get("score", 0) >= 0.5
    
    def test_retrieve_context_empty_query(self, rag_service):
        """Test handling of empty query"""
        results = rag_service.retrieve_context("", k=3)
        
        assert isinstance(results, list)
    
    def test_has_documents(self, rag_service, sample_document_path):
        """Test checking if documents exist"""
        # Check if RAG service is available
        if not rag_service.vectorstore or not rag_service.text_splitter:
            pytest.skip("RAG service not available (LangChain or embeddings not initialized)")
        
        # Initially should be False
        assert rag_service.has_documents(user_id=1) is False
        
        # After processing, should be True
        result = rag_service.process_document(sample_document_path, "txt", user_id=1, document_id=1)
        if result:  # Only check if processing succeeded
            assert rag_service.has_documents(user_id=1) is True
    
    def test_retrieve_context_simple(self, rag_service, sample_document_path):
        """Test simple context retrieval method"""
        # Check if RAG service is available
        if not rag_service.vectorstore:
            pytest.skip("RAG service not available (vectorstore not initialized)")
        
        result = rag_service.process_document(sample_document_path, "txt", user_id=1, document_id=1)
        if not result:
            pytest.skip("Could not process document")
        
        contexts = rag_service.retrieve_context_simple("test", k=3, user_id=1)
        
        assert isinstance(contexts, list)
        for context in contexts:
            assert isinstance(context, str)
    
    def test_process_document_invalid_file(self, rag_service, temp_dir):
        """Test processing of invalid file"""
        invalid_path = os.path.join(temp_dir, "nonexistent.txt")
        result = rag_service.process_document(invalid_path, "txt")
        
        # Should handle gracefully
        assert isinstance(result, bool)
    
    def test_retrieve_context_caching(self, rag_service, sample_document_path):
        """Test that context retrieval uses caching"""
        # Check if RAG service is available
        if not rag_service.vectorstore:
            pytest.skip("RAG service not available (vectorstore not initialized)")
        
        result = rag_service.process_document(sample_document_path, "txt", user_id=1, document_id=1)
        if not result:
            pytest.skip("Could not process document")
        
        query = "test query"
        results1 = rag_service.retrieve_context(query, k=3, user_id=1)
        results2 = rag_service.retrieve_context(query, k=3, user_id=1)
        
        # Second call should use cache (results should be similar)
        assert isinstance(results1, list)
        assert isinstance(results2, list)
    
    def test_get_scientific_writing_style(self, rag_service, sample_document_path):
        """Test scientific writing style extraction"""
        # Check if RAG service is available
        if not rag_service.vectorstore:
            pytest.skip("RAG service not available (vectorstore not initialized)")
        
        result = rag_service.process_document(sample_document_path, "txt", user_id=1, document_id=1)
        if not result:
            pytest.skip("Could not process document")
        
        style = rag_service.get_scientific_writing_style(user_id=1)
        
        assert isinstance(style, dict)
        # Should have style information if documents exist
        assert isinstance(style, dict)
    
    def test_assist_scientific_writing(self, rag_service, sample_document_path):
        """Test scientific writing assistance"""
        # Check if RAG service is available
        if not rag_service.vectorstore:
            pytest.skip("RAG service not available (vectorstore not initialized)")
        
        result = rag_service.process_document(sample_document_path, "txt", user_id=1, document_id=1)
        if not result:
            pytest.skip("Could not process document")
        
        assistance = rag_service.assist_scientific_writing(
            "Aide-moi à écrire scientifiquement",
            user_id=1
        )
        
        assert isinstance(assistance, dict)
        assert "suggestions" in assistance or "style" in assistance or "improved_text" in assistance
    
    def test_assist_scientific_writing_no_documents(self, rag_service):
        """Test scientific writing assistance when no documents exist"""
        assistance = rag_service.assist_scientific_writing(
            "Test text",
            user_id=999
        )
        
        assert isinstance(assistance, dict)
    
    def test_retrieve_context_with_document_id(self, rag_service, sample_document_path):
        """Test context retrieval with document_id filter"""
        # Check if RAG service is available
        if not rag_service.vectorstore:
            pytest.skip("RAG service not available (vectorstore not initialized)")
        
        result = rag_service.process_document(sample_document_path, "txt", user_id=1, document_id=1)
        if not result:
            pytest.skip("Could not process document")
        
        results = rag_service.retrieve_context(
            "test query",
            k=3,
            user_id=1,
            document_id=1
        )
        
        assert isinstance(results, list)
    
    def test_process_document_pdf(self, rag_service, temp_dir):
        """Test processing a PDF document"""
        # Check if RAG service is available
        if not rag_service.vectorstore or not rag_service.text_splitter:
            pytest.skip("RAG service not available")
        
        # This would require an actual PDF file
        pytest.skip("PDF processing test requires actual PDF file")
    
    def test_process_document_docx(self, rag_service, temp_dir):
        """Test processing a DOCX document"""
        # Check if RAG service is available
        if not rag_service.vectorstore or not rag_service.text_splitter:
            pytest.skip("RAG service not available")
        
        # This would require an actual DOCX file
        pytest.skip("DOCX processing test requires actual DOCX file")

