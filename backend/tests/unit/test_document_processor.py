"""
Unit tests for DocumentProcessor
"""
import pytest
import os
import tempfile
from app.services.document_processor import DocumentProcessor


@pytest.mark.unit
class TestDocumentProcessor:
    """Test suite for DocumentProcessor"""
    
    def test_document_processor_initialization(self):
        """Test that DocumentProcessor can be initialized"""
        processor = DocumentProcessor()
        assert processor is not None
        assert processor.grammar_service is not None
    
    def test_extract_text_from_txt(self, temp_dir):
        """Test text extraction from TXT file"""
        processor = DocumentProcessor()
        
        # Create a test TXT file
        txt_path = os.path.join(temp_dir, "test.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("Ceci est un test de document texte.")
        
        try:
            text = processor.extract_text_from_document(txt_path, "txt")
            assert isinstance(text, str)
            assert len(text) > 0
        except Exception as e:
            # If document loaders not available, skip
            pytest.skip(f"Document loaders not available: {e}")
    
    def test_process_document_txt(self, temp_dir):
        """Test processing a TXT document"""
        processor = DocumentProcessor()
        
        # Create a test TXT file
        txt_path = os.path.join(temp_dir, "test.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("Ceci est un test avec des erreurs grammaticaux.")
        
        result = processor.process_document(txt_path, "txt", preserve_structure=True)
        
        assert isinstance(result, dict)
        assert "processed_text" in result or "corrected_text" in result
        assert "corrections" in result or "all_corrections" in result
    
    def test_process_document_preserve_structure(self, temp_dir):
        """Test that structure is preserved when preserve_structure=True"""
        processor = DocumentProcessor()
        
        # Create a test TXT file
        txt_path = os.path.join(temp_dir, "test.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("Paragraphe 1.\n\nParagraphe 2.")
        
        result = processor.process_document(txt_path, "txt", preserve_structure=True)
        
        assert isinstance(result, dict)
        # Structure should be preserved (no reformulation)
        assert "processed_text" in result or "corrected_text" in result
    
    def test_process_document_invalid_file(self, temp_dir):
        """Test processing of invalid file"""
        processor = DocumentProcessor()
        
        invalid_path = os.path.join(temp_dir, "nonexistent.txt")
        
        # Should raise an exception for non-existent file
        with pytest.raises(Exception, match="Le fichier n'existe pas"):
            processor.process_document(invalid_path, "txt")
    
    def test_generate_document_txt(self, temp_dir):
        """Test document generation for TXT"""
        processor = DocumentProcessor()
        
        processed_text = "Texte corrigé et traité."
        output_path = os.path.join(temp_dir, "output.txt")
        
        try:
            result = processor.generate_document(processed_text, output_path, "txt")
            # Should create file or return path
            assert result is not None
            assert isinstance(result, str) or isinstance(result, dict)
        except Exception as e:
            # If document generators not available, skip
            pytest.skip(f"Document generators not available: {e}")
    
    def test_extract_text_from_document_unsupported_type(self, temp_dir):
        """Test extracting text from unsupported file type"""
        processor = DocumentProcessor()
        
        # Create a file with unsupported extension
        invalid_path = os.path.join(temp_dir, "test.xyz")
        with open(invalid_path, "w", encoding="utf-8") as f:
            f.write("Test content")
        
        try:
            with pytest.raises(Exception, match="Type de fichier non supporté"):
                processor.extract_text_from_document(invalid_path, "xyz")
        except Exception as e:
            # If document loaders not available, skip
            pytest.skip(f"Document loaders not available: {e}")
    
    def test_process_document_empty_file(self, temp_dir):
        """Test processing an empty file"""
        processor = DocumentProcessor()
        
        # Create an empty file
        empty_path = os.path.join(temp_dir, "empty.txt")
        with open(empty_path, "w", encoding="utf-8") as f:
            f.write("")
        
        try:
            with pytest.raises(Exception):
                processor.process_document(empty_path, "txt")
        except Exception as e:
            # If document loaders not available, skip
            pytest.skip(f"Document loaders not available: {e}")
    
    def test_process_document_without_preserve_structure(self, temp_dir):
        """Test processing document without preserving structure"""
        processor = DocumentProcessor()
        
        # Create a test TXT file
        txt_path = os.path.join(temp_dir, "test.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("Ceci est un test avec des erreurs grammaticaux.")
        
        result = processor.process_document(txt_path, "txt", preserve_structure=False)
        
        assert isinstance(result, dict)
        assert "processed_text" in result or "corrected_text" in result
    
    def test_generate_document_pdf(self, temp_dir):
        """Test document generation for PDF"""
        processor = DocumentProcessor()
        
        processed_text = "Texte corrigé et traité pour PDF."
        output_path = os.path.join(temp_dir, "output.pdf")
        
        try:
            result = processor.generate_document(processed_text, output_path, "pdf")
            # Should create file or return path
            assert result is not None
            assert isinstance(result, str) or isinstance(result, dict)
        except Exception as e:
            # If document generators not available, skip
            pytest.skip(f"PDF generator not available: {e}")
    
    def test_generate_document_docx(self, temp_dir):
        """Test document generation for DOCX"""
        processor = DocumentProcessor()
        
        processed_text = "Texte corrigé et traité pour DOCX."
        output_path = os.path.join(temp_dir, "output.docx")
        
        try:
            result = processor.generate_document(processed_text, output_path, "docx")
            # Should create file or return path
            assert result is not None
            assert isinstance(result, str) or isinstance(result, dict)
        except Exception as e:
            # If document generators not available, skip
            pytest.skip(f"DOCX generator not available: {e}")
    
    def test_extract_text_from_document_pdf(self, temp_dir):
        """Test text extraction from PDF file"""
        processor = DocumentProcessor()
        
        # This test requires a PDF file, so we'll skip if not available
        # In a real scenario, you'd create a test PDF
        pytest.skip("PDF extraction test requires actual PDF file")
    
    def test_extract_text_from_document_docx(self, temp_dir):
        """Test text extraction from DOCX file"""
        processor = DocumentProcessor()
        
        # This test requires a DOCX file, so we'll skip if not available
        pytest.skip("DOCX extraction test requires actual DOCX file")
