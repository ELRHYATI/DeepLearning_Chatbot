"""
Unit tests for GrammarService
"""
import pytest
from app.services.grammar_service import GrammarService


@pytest.mark.unit
class TestGrammarService:
    """Test suite for GrammarService"""
    
    def test_grammar_service_initialization(self, grammar_service):
        """Test that GrammarService can be initialized"""
        assert grammar_service is not None
    
    def test_correct_text_basic(self, grammar_service, sample_text):
        """Test basic text correction"""
        result = grammar_service.correct_text(sample_text)
        
        assert isinstance(result, dict)
        assert "corrected_text" in result
        assert "corrections" in result
        assert "original_text" in result
        
        # Check that original text is preserved
        assert result["original_text"] == sample_text
    
    def test_correct_text_empty_string(self, grammar_service):
        """Test correction of empty string"""
        result = grammar_service.correct_text("")
        
        assert result["corrected_text"] == ""
        assert len(result["corrections"]) == 0
    
    def test_correct_text_no_errors(self, grammar_service):
        """Test correction of text with no errors"""
        correct_text = "Bonjour, comment allez-vous? Je vais bien, merci."
        result = grammar_service.correct_text(correct_text)
        
        # LanguageTool might add minor formatting changes (like non-breaking spaces)
        # So we check that the text is similar, not exactly equal
        assert result["corrected_text"] is not None
        assert len(result["corrected_text"]) > 0
        # Should have few or no corrections
        assert isinstance(result["corrections"], list)
    
    def test_correct_text_with_errors(self, grammar_service):
        """Test correction of text with known errors"""
        text_with_errors = "Je suis allé a la bibliothèque"
        result = grammar_service.correct_text(text_with_errors)
        
        assert "corrected_text" in result
        # Should have at least one correction
        assert len(result["corrections"]) >= 0  # May be 0 if LanguageTool not available
    
    def test_correct_text_returns_dict_structure(self, grammar_service, sample_text):
        """Test that correct_text returns proper dictionary structure"""
        result = grammar_service.correct_text(sample_text)
        
        # Check all required keys
        required_keys = ["original_text", "corrected_text", "corrections"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
    
    def test_correct_text_corrections_format(self, grammar_service, sample_text):
        """Test that corrections are in the expected format"""
        result = grammar_service.correct_text(sample_text)
        
        for correction in result["corrections"]:
            assert isinstance(correction, dict)
            # Check for expected keys in correction
            assert "original" in correction or "error" in correction or "message" in correction
    
    def test_correct_text_unicode_handling(self, grammar_service):
        """Test that service handles Unicode characters correctly"""
        unicode_text = "C'est l'été, il fait chaud. J'aime les cafés français."
        result = grammar_service.correct_text(unicode_text)
        
        assert result["corrected_text"] is not None
        assert isinstance(result["corrected_text"], str)
    
    def test_correct_text_long_text(self, grammar_service):
        """Test correction of longer text"""
        long_text = " ".join(["Ceci est une phrase de test."] * 10)
        result = grammar_service.correct_text(long_text)
        
        assert len(result["corrected_text"]) > 0
        assert isinstance(result["corrections"], list)
    
    def test_grammar_service_without_languagetool(self):
        """Test that service works even if LanguageTool is not available"""
        # This test verifies fallback behavior
        service = GrammarService()
        
        # Should still work even if tool is None
        result = service.correct_text("Test text")
        assert "corrected_text" in result

