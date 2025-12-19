"""
Router for interactive learning from user corrections
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import User, Message, MessageCorrection, ChatSession
from app.routers.auth import get_current_user, get_current_user_optional
from app.schemas import (
    MessageCorrectionCreate,
    MessageCorrectionResponse,
    LearningStatsResponse
)
from app.services.learning_service import LearningService
from app.utils.logger import get_logger
from datetime import datetime

logger = get_logger()

router = APIRouter()
learning_service = LearningService()


@router.post("/corrections", response_model=MessageCorrectionResponse)
async def create_correction(
    correction: MessageCorrectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a correction for an AI message
    
    This allows users to correct AI responses, which will be used
    to improve future responses through machine learning.
    
    Args:
        correction: Correction data (message_id, corrected_content, notes)
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Created correction
    """
    # Verify message exists and belongs to user
    message = db.query(Message).join(ChatSession).filter(
        Message.id == correction.message_id,
        ChatSession.user_id == current_user.id,
        Message.role == "assistant"  # Only correct assistant messages
    ).first()
    
    if not message:
        raise HTTPException(
            status_code=404,
            detail="Message non trouvé ou vous n'avez pas la permission de le corriger"
        )
    
    # Check if correction already exists
    existing_correction = db.query(MessageCorrection).filter(
        MessageCorrection.message_id == correction.message_id,
        MessageCorrection.user_id == current_user.id
    ).first()
    
    if existing_correction:
        # Update existing correction
        existing_correction.corrected_content = correction.corrected_content
        existing_correction.correction_notes = correction.correction_notes
        existing_correction.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_correction)
        
        logger.info(
            f"Correction updated for message {correction.message_id}",
            extra_data={
                "event": "correction_updated",
                "user_id": current_user.id,
                "message_id": correction.message_id
            }
        )
        
        return existing_correction
    
    # Create new correction
    new_correction = MessageCorrection(
        message_id=correction.message_id,
        user_id=current_user.id,
        original_content=message.content,
        corrected_content=correction.corrected_content,
        correction_type=message.module_type or "general",
        correction_notes=correction.correction_notes,
        is_used_for_learning=True
    )
    
    db.add(new_correction)
    db.commit()
    db.refresh(new_correction)
    
    logger.info(
        f"Correction created for message {correction.message_id}",
        extra_data={
            "event": "correction_created",
            "user_id": current_user.id,
            "message_id": correction.message_id,
            "module_type": message.module_type
        }
    )
    
    return new_correction


@router.get("/corrections", response_model=List[MessageCorrectionResponse])
async def get_user_corrections(
    module_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all corrections made by the current user
    
    Args:
        module_type: Optional filter by module type
        limit: Maximum number of corrections to return
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        List of user's corrections
    """
    query = db.query(MessageCorrection).filter(
        MessageCorrection.user_id == current_user.id
    )
    
    if module_type:
        query = query.join(Message).filter(Message.module_type == module_type)
    
    corrections = query.order_by(MessageCorrection.created_at.desc()).limit(limit).all()
    
    return corrections


@router.get("/corrections/{correction_id}", response_model=MessageCorrectionResponse)
async def get_correction(
    correction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific correction by ID
    
    Args:
        correction_id: ID of the correction
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Correction details
    """
    correction = db.query(MessageCorrection).filter(
        MessageCorrection.id == correction_id,
        MessageCorrection.user_id == current_user.id
    ).first()
    
    if not correction:
        raise HTTPException(status_code=404, detail="Correction non trouvée")
    
    return correction


@router.delete("/corrections/{correction_id}")
async def delete_correction(
    correction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a correction
    
    Args:
        correction_id: ID of the correction to delete
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Success message
    """
    correction = db.query(MessageCorrection).filter(
        MessageCorrection.id == correction_id,
        MessageCorrection.user_id == current_user.id
    ).first()
    
    if not correction:
        raise HTTPException(status_code=404, detail="Correction non trouvée")
    
    db.delete(correction)
    db.commit()
    
    logger.info(
        f"Correction deleted: {correction_id}",
        extra_data={
            "event": "correction_deleted",
            "user_id": current_user.id,
            "correction_id": correction_id
        }
    )
    
    return {"message": "Correction supprimée avec succès"}


@router.get("/stats", response_model=LearningStatsResponse)
async def get_learning_stats(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get learning statistics from corrections
    
    Args:
        db: Database session
        current_user: Optional current user (if None, returns global stats)
    
    Returns:
        Learning statistics
    """
    user_id = current_user.id if current_user else None
    stats = learning_service.get_learning_statistics(db, user_id=user_id)
    
    return LearningStatsResponse(**stats)


@router.get("/patterns")
async def get_correction_patterns(
    module_type: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get common correction patterns learned from user corrections
    
    Args:
        module_type: Optional filter by module type
        limit: Maximum number of patterns to return
        db: Database session
        current_user: Optional current user
    
    Returns:
        List of correction patterns
    """
    patterns = learning_service.extract_correction_patterns(
        db,
        module_type=module_type,
        limit=limit
    )
    
    return {
        "patterns": patterns,
        "count": len(patterns)
    }


@router.get("/training-data/{module_type}")
async def get_training_data(
    module_type: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get training data prepared from corrections for fine-tuning
    
    Args:
        module_type: Type of module (grammar, qa, reformulation)
        limit: Maximum number of examples
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Training data ready for fine-tuning
    """
    if module_type not in ['grammar', 'qa', 'reformulation']:
        raise HTTPException(
            status_code=400,
            detail="module_type doit être 'grammar', 'qa' ou 'reformulation'"
        )
    
    training_data = learning_service.prepare_training_data(
        db,
        module_type=module_type,
        limit=limit
    )
    
    return {
        "module_type": module_type,
        "examples": training_data,
        "count": len(training_data)
    }

