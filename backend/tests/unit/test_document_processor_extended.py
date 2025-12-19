"""
Extended unit tests for Document Processor
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import os
import tempfile
from app.services.document_processor import DocumentProcessor


@pytest.mark.unit
class TestDocumentProcessorExtended:
    """Extended test suite for Document Processor"""
    
    def test_document_processor_initialization(self):
        """Test document processor initialization"""
        processor = DocumentProcessor()
        assert processor is not None
    
    @patch('app.services.document_processor.PyPDFLoader')
    @patch('app.services.document_processor.os.path.exists')
    def test_process_pdf(self, mock_exists, mock_pdf_loader, temp_dir):
        """Test processing PDF document"""
        processor = DocumentProcessor()
        
        test_file = os.path.join(temp_dir, "test.pdf")
        mock_exists.return_value = True
        
        # Mock PDF loader
        mock_loader = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "PDF content"
        mock_loader.load.return_value = [mock_doc]
        mock_pdf_loader.return_value = mock_loader
        
        result = processor.process_document(test_file, "pdf")
        
        assert isinstance(result, dict)
        assert "original_text" in result or "processed_text" in result
    
    @patch('app.services.document_processor.os.path.exists')
    def test_process_txt(self, mock_exists, temp_dir):
        """Test processing TXT document"""
        processor = DocumentProcessor()
        
        test_file = os.path.join(temp_dir, "test.txt")
        mock_exists.return_value = True
        
        # Mock file reading
        with patch('builtins.open', mock_open(read_data="Text content")):
            result = processor.process_document(test_file, "txt")
        
        assert isinstance(result, dict)
        assert "original_text" in result or "processed_text" in result
    
    @patch('app.services.document_processor.Docx2txtLoader')
    @patch('app.services.document_processor.os.path.exists')
    def test_process_docx(self, mock_exists, mock_docx_loader, temp_dir):
        """Test processing DOCX document"""
        processor = DocumentProcessor()
        
        test_file = os.path.join(temp_dir, "test.docx")
        mock_exists.return_value = True
        
        # Mock DOCX loader
        mock_loader = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "DOCX content"
        mock_loader.load.return_value = [mock_doc]
        mock_docx_loader.return_value = mock_loader
        
        result = processor.process_document(test_file, "docx")
        
        assert isinstance(result, dict)
        assert "original_text" in result or "processed_text" in result
    
    @patch('app.services.document_processor.os.path.exists')
    def test_process_unsupported_format(self, mock_exists, temp_dir):
        """Test processing unsupported file format"""
        processor = DocumentProcessor()
        
        test_file = os.path.join(temp_dir, "test.xyz")
        mock_exists.return_value = True
        
        with pytest.raises(Exception):
            processor.process_document(test_file, "xyz")

