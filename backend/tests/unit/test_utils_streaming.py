"""
Unit tests for Streaming utilities
"""
import pytest
from unittest.mock import Mock, patch
from app.utils.streaming import (
    stream_text_progressive,
    create_streaming_response,
    format_sse_event,
    stream_text_chunks,
    stream_response
)


@pytest.mark.unit
class TestStreamingUtils:
    """Test suite for Streaming utilities"""
    
    def test_format_sse_event(self):
        """Test formatting SSE event"""
        event = format_sse_event({"data": "value"}, event="test")
        
        assert isinstance(event, str)
        assert "event: test" in event
        assert "data:" in event
    
    def test_format_sse_event_without_event_type(self):
        """Test formatting SSE event without event type"""
        event = format_sse_event({"data": "value"})
        
        assert isinstance(event, str)
        assert "data:" in event
    
    @pytest.mark.asyncio
    async def test_stream_text_progressive(self):
        """Test progressive text streaming"""
        text = "This is a test"
        chunks = []
        
        async for chunk in stream_text_progressive(text, words_per_chunk=2):
            chunks.append(chunk)
            assert isinstance(chunk, dict)
            assert "content" in chunk
        
        assert len(chunks) > 0
    
    @pytest.mark.asyncio
    async def test_stream_text_chunks(self):
        """Test streaming text chunks"""
        text = "This is a test"
        chunks = []
        
        async for chunk in stream_text_chunks(text, chunk_size=5):
            chunks.append(chunk)
            assert isinstance(chunk, str)
        
        assert len(chunks) > 0
    
    @pytest.mark.asyncio
    async def test_stream_response(self):
        """Test stream_response function"""
        async def generator():
            yield {"type": "chunk", "content": "test"}
        
        chunks = []
        async for chunk in stream_response(generator(), initial_message="Start"):
            chunks.append(chunk)
            assert isinstance(chunk, str)
        
        assert len(chunks) > 0
    
    def test_create_streaming_response(self):
        """Test creating streaming response"""
        async def generator():
            yield "chunk1"
            yield "chunk2"
        
        response = create_streaming_response(generator())
        
        assert response is not None
        assert response.media_type == "text/event-stream"

