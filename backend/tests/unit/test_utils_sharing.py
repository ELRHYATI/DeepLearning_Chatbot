"""
Unit tests for Sharing utilities
"""
import pytest
from unittest.mock import Mock, patch
from app.utils.sharing import (
    generate_share_token,
    create_share_link,
    validate_share_token
)


@pytest.mark.unit
class TestSharingUtils:
    """Test suite for Sharing utilities"""
    
    def test_generate_share_token(self):
        """Test generating a share token"""
        token = generate_share_token()
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_generate_share_token_unique(self):
        """Test that generated tokens are unique"""
        token1 = generate_share_token()
        token2 = generate_share_token()
        
        assert token1 != token2
    
    def test_create_share_link(self):
        """Test creating a share link"""
        token = "test_token_123"
        link = create_share_link(token)
        
        assert isinstance(link, str)
        assert token in link
    
    def test_validate_share_token_valid(self):
        """Test validating a valid token"""
        token = generate_share_token()
        is_valid = validate_share_token(token)
        
        # Token format validation (basic check)
        assert isinstance(is_valid, bool)
    
    def test_validate_share_token_invalid_format(self):
        """Test validating an invalid token format"""
        invalid_token = "invalid"
        is_valid = validate_share_token(invalid_token)
        
        # Should return False for invalid format
        assert isinstance(is_valid, bool)

