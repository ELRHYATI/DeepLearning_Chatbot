"""
Unit tests for Error Handler utilities
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.utils.error_handler import (
    AppException,
    ErrorCode,
    ERROR_MESSAGES,
    global_exception_handler,
    _get_error_code_from_status,
    create_error_response,
    retry,
    async_retry
)


@pytest.mark.unit
class TestErrorHandler:
    """Test suite for Error Handler"""
    
    def test_error_code_constants(self):
        """Test that ErrorCode constants are defined"""
        assert ErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"
        assert ErrorCode.NOT_FOUND == "NOT_FOUND"
        assert ErrorCode.UNAUTHORIZED == "UNAUTHORIZED"
        assert ErrorCode.INVALID_CREDENTIALS == "INVALID_CREDENTIALS"
    
    def test_error_messages_exist(self):
        """Test that error messages exist for all error codes"""
        assert ErrorCode.INTERNAL_ERROR in ERROR_MESSAGES
        assert ErrorCode.NOT_FOUND in ERROR_MESSAGES
        assert ErrorCode.UNAUTHORIZED in ERROR_MESSAGES
    
    def test_app_exception_creation(self):
        """Test creating AppException"""
        exc = AppException(
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            detail="Custom message"
        )
        
        assert exc.error_code == ErrorCode.NOT_FOUND
        assert exc.status_code == 404
        assert exc.detail == "Custom message"
    
    def test_app_exception_default_message(self):
        """Test AppException uses default message when detail not provided"""
        exc = AppException(
            error_code=ErrorCode.NOT_FOUND,
            status_code=404
        )
        
        assert exc.detail == ERROR_MESSAGES[ErrorCode.NOT_FOUND]
    
    def test_get_error_code_from_status(self):
        """Test _get_error_code_from_status function"""
        assert _get_error_code_from_status(400) == ErrorCode.BAD_REQUEST
        assert _get_error_code_from_status(401) == ErrorCode.UNAUTHORIZED
        assert _get_error_code_from_status(403) == ErrorCode.FORBIDDEN
        assert _get_error_code_from_status(404) == ErrorCode.NOT_FOUND
        assert _get_error_code_from_status(422) == ErrorCode.VALIDATION_ERROR
        assert _get_error_code_from_status(500) == ErrorCode.INTERNAL_ERROR
    
    def test_create_error_response(self):
        """Test create_error_response helper"""
        exc = create_error_response(
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            detail="Resource not found"
        )
        
        assert isinstance(exc, AppException)
        assert exc.error_code == ErrorCode.NOT_FOUND
        assert exc.status_code == 404
    
    @pytest.mark.asyncio
    async def test_global_exception_handler_app_exception(self):
        """Test global exception handler with AppException"""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        
        exc = AppException(
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            detail="Not found"
        )
        
        response = await global_exception_handler(request, exc)
        
        assert response.status_code == 404
        content = response.body.decode()
        assert "error" in content
        assert "error_code" in content
    
    @pytest.mark.asyncio
    async def test_global_exception_handler_http_exception(self):
        """Test global exception handler with HTTPException"""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        
        exc = HTTPException(status_code=404, detail="Not found")
        
        response = await global_exception_handler(request, exc)
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_global_exception_handler_validation_error(self):
        """Test global exception handler with RequestValidationError"""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "POST"
        request.client.host = "127.0.0.1"
        
        # Create a mock validation error
        errors = [{
            "loc": ("body", "field"),
            "msg": "Field required",
            "type": "value_error.missing"
        }]
        exc = RequestValidationError(errors=errors)
        
        response = await global_exception_handler(request, exc)
        
        assert response.status_code == 422
        content = response.body.decode()
        assert "validation_errors" in content
    
    @pytest.mark.asyncio
    async def test_global_exception_handler_generic_exception(self):
        """Test global exception handler with generic Exception"""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        
        exc = Exception("Generic error")
        
        response = await global_exception_handler(request, exc)
        
        assert response.status_code == 500
    
    def test_retry_decorator_success(self):
        """Test retry decorator with successful call"""
        @retry(max_attempts=3)
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    def test_retry_decorator_failure(self):
        """Test retry decorator with failing function"""
        call_count = [0]
        
        @retry(max_attempts=3, delay=0.01)
        def failing_function():
            call_count[0] += 1
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        assert call_count[0] == 3  # Should retry 3 times
    
    def test_retry_decorator_success_after_retry(self):
        """Test retry decorator that succeeds after retries"""
        call_count = [0]
        
        @retry(max_attempts=3, delay=0.01)
        def eventually_successful():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Temporary error")
            return "success"
        
        result = eventually_successful()
        assert result == "success"
        assert call_count[0] == 2
    
    @pytest.mark.asyncio
    async def test_async_retry_decorator_success(self):
        """Test async retry decorator with successful call"""
        @async_retry(max_attempts=3)
        async def successful_async_function():
            return "success"
        
        result = await successful_async_function()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_async_retry_decorator_failure(self):
        """Test async retry decorator with failing function"""
        call_count = [0]
        
        @async_retry(max_attempts=3, delay=0.01)
        async def failing_async_function():
            call_count[0] += 1
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await failing_async_function()
        
        assert call_count[0] == 3

