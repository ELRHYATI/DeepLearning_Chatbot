"""
Router for AI-powered suggestions while typing
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.models import User
from app.routers.auth import get_current_user_optional
from app.schemas import SuggestionRequest, SuggestionResponse
from app.services.suggestions_service import SuggestionsService
from app.utils.logger import get_logger

logger = get_logger()

router = APIRouter()
suggestions_service = SuggestionsService()


@router.get("/", response_model=List[SuggestionResponse])
async def get_suggestions(
    q: str = Query(..., description="Current text input"),
    cursor_position: int = Query(None, description="Cursor position in text"),
    module_type: str = Query("general", description="Module type (grammar, qa, reformulation, general)"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get AI-powered suggestions while typing
    
    Args:
        q: Current text input
        cursor_position: Cursor position (optional, defaults to end of text)
        module_type: Type of module
        db: Database session
        current_user: Optional current user
    
    Returns:
        List of suggestions
    """
    try:
        # Validate and sanitize input
        if not q or not isinstance(q, str):
            return []
        
        # Normalize text - remove control characters
        q = ''.join(c for c in q if c.isprintable() or c.isspace())
        
        # Default cursor position to end of text if not provided
        if cursor_position is None:
            cursor_position = len(q)
        else:
            # Ensure cursor_position is valid
            cursor_position = max(0, min(cursor_position, len(q)))
        
        # Get suggestions with timeout protection
        suggestions = []
        try:
            suggestions = suggestions_service.get_smart_suggestions(
                text=q,
                cursor_position=cursor_position,
                module_type=module_type,
                db=db
            )
        except Exception as e:
            logger.error(f"Error in get_smart_suggestions: {e}", exc_info=e)
            suggestions = []
        
        # Add semantic suggestions if available (with error handling)
        if current_user and len(q) > 5:
            try:
                semantic_suggestions = suggestions_service.get_semantic_suggestions(
                    text=q,
                    module_type=module_type,
                    db=db
                )
                if semantic_suggestions:
                    suggestions.extend(semantic_suggestions)
            except Exception as e:
                logger.error(f"Error getting semantic suggestions: {e}", exc_info=e)
        
        # Sort by confidence and limit
        try:
            suggestions.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            suggestions = suggestions[:5]
        except Exception as e:
            logger.error(f"Error sorting suggestions: {e}", exc_info=e)
            suggestions = suggestions[:5] if suggestions else []
        
        logger.debug(
            f"Generated {len(suggestions)} suggestions",
            extra_data={
                "event": "suggestions_generated",
                "text_length": len(q),
                "module_type": module_type,
                "suggestions_count": len(suggestions)
            }
        )
        
        return suggestions
    
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}", exc_info=e)
        return []


@router.post("/", response_model=List[SuggestionResponse])
async def get_suggestions_post(
    request: SuggestionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get AI-powered suggestions (POST version)
    
    Args:
        request: Suggestion request with text, cursor position, and module type
        db: Database session
        current_user: Optional current user
    
    Returns:
        List of suggestions
    """
    try:
        cursor_position = request.cursor_position or len(request.text)
        
        suggestions = suggestions_service.get_smart_suggestions(
            text=request.text,
            cursor_position=cursor_position,
            module_type=request.module_type or "general",
            db=db
        )
        
        # Add semantic suggestions if available
        if current_user and len(request.text) > 5:
            semantic_suggestions = suggestions_service.get_semantic_suggestions(
                text=request.text,
                module_type=request.module_type or "general",
                db=db
            )
            suggestions.extend(semantic_suggestions)
        
        # Sort by confidence and limit
        suggestions.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        suggestions = suggestions[:5]
        
        return suggestions
    
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}", exc_info=e)
        return []

