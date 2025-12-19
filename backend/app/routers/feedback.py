"""
Feedback Router
Handles user feedback collection and learning insights
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import User
from app.services.feedback_service import FeedbackService
from app.services.adaptive_learning_service import AdaptiveLearningService
from app.routers.auth import get_current_user, get_current_user_optional
from app.utils.logger import get_logger

logger = get_logger()

router = APIRouter()
feedback_service = FeedbackService()
adaptive_learning = AdaptiveLearningService()


class FeedbackCreate(BaseModel):
    task_type: str = Field(..., description="Type of task: qa, reformulation, grammar, summarization, plan")
    feedback_type: str = Field(..., description="Type of feedback: positive, negative, rating")
    rating: Optional[float] = Field(None, ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = Field(None, description="Optional comment")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class FeedbackResponse(BaseModel):
    success: bool
    message: str
    feedback_id: Optional[str] = None


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit user feedback for a task
    
    Args:
        feedback_data: Feedback information
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Feedback response
    """
    try:
        feedback_entry = feedback_service.record_feedback(
            user_id=str(current_user.id),
            task_type=feedback_data.task_type,
            feedback_type=feedback_data.feedback_type,
            rating=feedback_data.rating,
            comment=feedback_data.comment,
            metadata=feedback_data.metadata
        )
        
        logger.info(f"Feedback recorded for user {current_user.id}, task {feedback_data.task_type}")
        
        return FeedbackResponse(
            success=True,
            message="Feedback enregistré avec succès",
            feedback_id=str(feedback_entry.get('timestamp', ''))
        )
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement du feedback: {str(e)}")


@router.get("/feedback/preferences")
async def get_user_preferences(
    task_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user preferences based on feedback history
    
    Args:
        task_type: Optional task type to filter preferences
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User preferences
    """
    try:
        prefs = feedback_service.get_user_preferences(
            user_id=str(current_user.id),
            task_type=task_type
        )
        
        return {
            "success": True,
            "preferences": prefs
        }
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des préférences: {str(e)}")


@router.get("/feedback/insights")
async def get_learning_insights(
    task_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get learning insights and recommendations for a user
    
    Args:
        task_type: Type of task
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Learning insights and recommendations
    """
    try:
        insights = feedback_service.get_learning_insights(
            user_id=str(current_user.id),
            task_type=task_type
        )
        
        recommendations = adaptive_learning.get_learning_recommendations(
            user_id=str(current_user.id),
            task_type=task_type
        )
        
        insights['recommendations'] = recommendations
        
        return {
            "success": True,
            "insights": insights
        }
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des insights: {str(e)}")


@router.get("/feedback/statistics")
async def get_feedback_statistics(
    task_type: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get feedback statistics
    
    Args:
        task_type: Optional task type to filter
        current_user: Current authenticated user (optional, for user-specific stats)
        db: Database session
        
    Returns:
        Feedback statistics
    """
    try:
        user_id = str(current_user.id) if current_user else None
        stats = feedback_service.get_feedback_statistics(
            user_id=user_id,
            task_type=task_type
        )
        
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des statistiques: {str(e)}")
