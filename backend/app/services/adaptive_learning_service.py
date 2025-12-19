"""
Adaptive Learning Service
Adapts model parameters and behavior based on user feedback and preferences
"""
from typing import Dict, Optional, List
from app.services.feedback_service import FeedbackService
from app.utils.logger import get_logger

logger = get_logger()


class AdaptiveLearningService:
    """Service for adaptive learning based on user feedback"""
    
    def __init__(self):
        self.feedback_service = FeedbackService()
        self.adaptation_enabled = True
    
    def adapt_qa_parameters(
        self,
        user_id: str,
        default_params: Dict
    ) -> Dict:
        """
        Adapt QA parameters based on user feedback
        
        Args:
            user_id: User identifier
            default_params: Default QA parameters
            
        Returns:
            Adapted parameters
        """
        if not self.adaptation_enabled:
            return default_params
        
        return self.feedback_service.get_optimal_parameters(
            user_id=user_id,
            task_type='qa',
            default_params=default_params
        )
    
    def adapt_reformulation_parameters(
        self,
        user_id: str,
        style: str,
        default_params: Dict
    ) -> Dict:
        """
        Adapt reformulation parameters based on user feedback
        
        Args:
            user_id: User identifier
            style: Reformulation style
            default_params: Default reformulation parameters
            
        Returns:
            Adapted parameters
        """
        if not self.adaptation_enabled:
            return default_params
        
        # Get base optimal parameters
        optimal = self.feedback_service.get_optimal_parameters(
            user_id=user_id,
            task_type='reformulation',
            default_params=default_params
        )
        
        # Adjust based on style preferences
        prefs = self.feedback_service.get_user_preferences(user_id, 'reformulation')
        style_prefs = prefs.get('style_preferences', {}).get(style, {})
        
        if style_prefs.get('preferred_temperature'):
            optimal['temperature'] = style_prefs['preferred_temperature']
        
        if style_prefs.get('preferred_length'):
            optimal['max_length'] = style_prefs['preferred_length']
        
        return optimal
    
    def adapt_summarization_parameters(
        self,
        user_id: str,
        default_params: Dict
    ) -> Dict:
        """
        Adapt summarization parameters based on user feedback
        
        Args:
            user_id: User identifier
            default_params: Default summarization parameters
            
        Returns:
            Adapted parameters
        """
        if not self.adaptation_enabled:
            return default_params
        
        return self.feedback_service.get_optimal_parameters(
            user_id=user_id,
            task_type='summarization',
            default_params=default_params
        )
    
    def get_user_style_preference(
        self,
        user_id: str,
        task_type: str
    ) -> Optional[str]:
        """
        Get user's preferred style for a task type
        
        Args:
            user_id: User identifier
            task_type: Type of task
            
        Returns:
            Preferred style or None
        """
        prefs = self.feedback_service.get_user_preferences(user_id, task_type)
        style_prefs = prefs.get('style_preferences', {})
        
        # Find most used style with positive feedback
        best_style = None
        best_score = 0.0
        
        for style, style_data in style_prefs.items():
            usage_count = style_data.get('usage_count', 0)
            positive_ratio = style_data.get('positive_count', 0) / max(usage_count, 1)
            score = usage_count * positive_ratio
            
            if score > best_score:
                best_score = score
                best_style = style
        
        return best_style
    
    def should_use_rag(
        self,
        user_id: str
    ) -> bool:
        """
        Determine if RAG should be used based on user feedback
        
        Args:
            user_id: User identifier
            
        Returns:
            True if RAG should be used
        """
        prefs = self.feedback_service.get_user_preferences(user_id)
        task_prefs = prefs.get('task_preferences', {}).get('qa', {})
        
        # If user has positive feedback with RAG, use it
        # If negative feedback without RAG, try RAG
        rag_feedback = task_prefs.get('rag_positive_count', 0)
        no_rag_feedback = task_prefs.get('no_rag_negative_count', 0)
        
        return rag_feedback > no_rag_feedback or no_rag_feedback == 0
    
    def get_learning_recommendations(
        self,
        user_id: str,
        task_type: str
    ) -> List[str]:
        """
        Get learning recommendations for a user
        
        Args:
            user_id: User identifier
            task_type: Type of task
            
        Returns:
            List of recommendations
        """
        insights = self.feedback_service.get_learning_insights(user_id, task_type)
        return insights.get('recommendations', [])
    
    def record_successful_interaction(
        self,
        user_id: str,
        task_type: str,
        metadata: Dict
    ):
        """
        Record a successful interaction (implicit positive feedback)
        
        Args:
            user_id: User identifier
            task_type: Type of task
            metadata: Interaction metadata
        """
        self.feedback_service.record_feedback(
            user_id=user_id,
            task_type=task_type,
            feedback_type='positive',
            rating=4.0,  # Implicit positive
            metadata=metadata
        )
    
    def record_failed_interaction(
        self,
        user_id: str,
        task_type: str,
        metadata: Dict,
        reason: Optional[str] = None
    ):
        """
        Record a failed interaction (implicit negative feedback)
        
        Args:
            user_id: User identifier
            task_type: Type of task
            metadata: Interaction metadata
            reason: Optional reason for failure
        """
        self.feedback_service.record_feedback(
            user_id=user_id,
            task_type=task_type,
            feedback_type='negative',
            rating=2.0,  # Implicit negative
            comment=reason,
            metadata=metadata
        )

