"""
Feedback and Continuous Learning Service
Collects user feedback and adapts model parameters based on preferences
"""
from typing import Dict, List, Optional
import json
import os
from datetime import datetime
from collections import defaultdict
import statistics
from app.utils.logger import get_logger

logger = get_logger()


class FeedbackService:
    """Service for collecting feedback and continuous learning"""
    
    def __init__(self):
        self.feedback_file = os.path.join(
            os.path.dirname(__file__),
            'user_feedback.json'
        )
        self.preferences_file = os.path.join(
            os.path.dirname(__file__),
            'user_preferences.json'
        )
        self.feedback_data = defaultdict(list)
        self.user_preferences = {}
        self._load_feedback()
        self._load_preferences()
    
    def _load_feedback(self):
        """Load feedback data from file"""
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.feedback_data = defaultdict(list, data)
                logger.info(f"Loaded {sum(len(v) for v in self.feedback_data.values())} feedback entries")
            except Exception as e:
                logger.warning(f"Could not load feedback file: {e}")
                self.feedback_data = defaultdict(list)
        else:
            self.feedback_data = defaultdict(list)
    
    def _save_feedback(self):
        """Save feedback data to file"""
        try:
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(dict(self.feedback_data), f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Could not save feedback file: {e}")
    
    def _load_preferences(self):
        """Load user preferences from file"""
        if os.path.exists(self.preferences_file):
            try:
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    self.user_preferences = json.load(f)
                logger.info(f"Loaded preferences for {len(self.user_preferences)} users")
            except Exception as e:
                logger.warning(f"Could not load preferences file: {e}")
                self.user_preferences = {}
        else:
            self.user_preferences = {}
    
    def _save_preferences(self):
        """Save user preferences to file"""
        try:
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_preferences, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Could not save preferences file: {e}")
    
    def record_feedback(
        self,
        user_id: str,
        task_type: str,
        feedback_type: str,  # 'positive', 'negative', 'rating'
        rating: Optional[float] = None,  # 1-5 scale
        comment: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Record user feedback
        
        Args:
            user_id: User identifier
            task_type: Type of task ('qa', 'reformulation', 'grammar', 'summarization', 'plan')
            feedback_type: Type of feedback ('positive', 'negative', 'rating')
            rating: Rating score (1-5, optional)
            comment: Optional comment
            metadata: Additional metadata (model used, parameters, etc.)
            
        Returns:
            Dictionary with feedback record
        """
        feedback_entry = {
            'user_id': user_id,
            'task_type': task_type,
            'feedback_type': feedback_type,
            'rating': rating,
            'comment': comment,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Store feedback
        key = f"{user_id}_{task_type}"
        self.feedback_data[key].append(feedback_entry)
        
        # Keep only last 100 feedback entries per user/task
        if len(self.feedback_data[key]) > 100:
            self.feedback_data[key] = self.feedback_data[key][-100:]
        
        # Update user preferences based on feedback
        self._update_preferences_from_feedback(user_id, task_type, feedback_entry)
        
        # Save to file
        self._save_feedback()
        
        logger.info(f"Feedback recorded for user {user_id}, task {task_type}, type {feedback_type}")
        
        return feedback_entry
    
    def _update_preferences_from_feedback(
        self,
        user_id: str,
        task_type: str,
        feedback_entry: Dict
    ):
        """Update user preferences based on feedback"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                'task_preferences': {},
                'model_preferences': {},
                'parameter_preferences': {},
                'style_preferences': {}
            }
        
        # Update task preferences
        if task_type not in self.user_preferences[user_id]['task_preferences']:
            self.user_preferences[user_id]['task_preferences'][task_type] = {
                'total_feedback': 0,
                'positive_count': 0,
                'negative_count': 0,
                'average_rating': 0.0,
                'ratings': []
            }
        
        prefs = self.user_preferences[user_id]['task_preferences'][task_type]
        prefs['total_feedback'] += 1
        
        if feedback_entry['feedback_type'] == 'positive':
            prefs['positive_count'] += 1
        elif feedback_entry['feedback_type'] == 'negative':
            prefs['negative_count'] += 1
        elif feedback_entry['feedback_type'] == 'rating' and feedback_entry.get('rating'):
            prefs['ratings'].append(feedback_entry['rating'])
            if len(prefs['ratings']) > 50:  # Keep last 50 ratings
                prefs['ratings'] = prefs['ratings'][-50:]
            prefs['average_rating'] = statistics.mean(prefs['ratings'])
        
        # Update model preferences if metadata contains model info
        if feedback_entry.get('metadata', {}).get('model'):
            model_name = feedback_entry['metadata']['model']
            if model_name not in self.user_preferences[user_id]['model_preferences']:
                self.user_preferences[user_id]['model_preferences'][model_name] = {
                    'usage_count': 0,
                    'positive_count': 0,
                    'average_rating': 0.0
                }
            
            model_prefs = self.user_preferences[user_id]['model_preferences'][model_name]
            model_prefs['usage_count'] += 1
            
            if feedback_entry['feedback_type'] == 'positive':
                model_prefs['positive_count'] += 1
            elif feedback_entry['feedback_type'] == 'rating' and feedback_entry.get('rating'):
                # Update average rating
                current_avg = model_prefs['average_rating']
                count = model_prefs['usage_count']
                new_rating = feedback_entry['rating']
                model_prefs['average_rating'] = ((current_avg * (count - 1)) + new_rating) / count
        
        # Update parameter preferences
        if feedback_entry.get('metadata', {}).get('generation_params'):
            params = feedback_entry['metadata']['generation_params']
            if task_type not in self.user_preferences[user_id]['parameter_preferences']:
                self.user_preferences[user_id]['parameter_preferences'][task_type] = {
                    'successful_params': [],
                    'failed_params': []
                }
            
            param_prefs = self.user_preferences[user_id]['parameter_preferences'][task_type]
            
            if feedback_entry['feedback_type'] == 'positive' or (feedback_entry.get('rating', 0) >= 4):
                # Successful parameters
                param_prefs['successful_params'].append({
                    'params': params,
                    'rating': feedback_entry.get('rating', 5),
                    'timestamp': feedback_entry['timestamp']
                })
                # Keep only last 20 successful parameter sets
                if len(param_prefs['successful_params']) > 20:
                    param_prefs['successful_params'] = param_prefs['successful_params'][-20:]
            elif feedback_entry['feedback_type'] == 'negative' or (feedback_entry.get('rating', 5) <= 2):
                # Failed parameters
                param_prefs['failed_params'].append({
                    'params': params,
                    'rating': feedback_entry.get('rating', 1),
                    'timestamp': feedback_entry['timestamp']
                })
                # Keep only last 10 failed parameter sets
                if len(param_prefs['failed_params']) > 10:
                    param_prefs['failed_params'] = param_prefs['failed_params'][-10:]
        
        # Save preferences
        self._save_preferences()
    
    def get_user_preferences(
        self,
        user_id: str,
        task_type: Optional[str] = None
    ) -> Dict:
        """
        Get user preferences
        
        Args:
            user_id: User identifier
            task_type: Optional task type to filter preferences
            
        Returns:
            Dictionary with user preferences
        """
        if user_id not in self.user_preferences:
            return {}
        
        prefs = self.user_preferences[user_id]
        
        if task_type:
            return {
                'task_preferences': prefs.get('task_preferences', {}).get(task_type, {}),
                'model_preferences': prefs.get('model_preferences', {}),
                'parameter_preferences': prefs.get('parameter_preferences', {}).get(task_type, {}),
                'style_preferences': prefs.get('style_preferences', {})
            }
        
        return prefs
    
    def get_optimal_parameters(
        self,
        user_id: str,
        task_type: str,
        default_params: Dict
    ) -> Dict:
        """
        Get optimal parameters for a user based on their feedback history
        
        Args:
            user_id: User identifier
            task_type: Type of task
            default_params: Default parameters to use as base
            
        Returns:
            Optimized parameters dictionary
        """
        if user_id not in self.user_preferences:
            return default_params
        
        param_prefs = self.user_preferences[user_id].get('parameter_preferences', {}).get(task_type, {})
        successful_params = param_prefs.get('successful_params', [])
        
        if not successful_params:
            return default_params
        
        # Calculate average of successful parameters
        optimized = default_params.copy()
        
        # Get most recent successful parameters (weighted by rating)
        recent_successful = sorted(
            successful_params,
            key=lambda x: (x.get('rating', 5), x.get('timestamp', '')),
            reverse=True
        )[:5]  # Top 5 most successful
        
        if recent_successful:
            # Average the parameters
            for param_name in default_params.keys():
                if isinstance(default_params[param_name], (int, float)):
                    values = [
                        p['params'].get(param_name, default_params[param_name])
                        for p in recent_successful
                        if param_name in p.get('params', {})
                    ]
                    if values:
                        # Weighted average by rating
                        weights = [p.get('rating', 5) for p in recent_successful[:len(values)]]
                        weighted_sum = sum(v * w for v, w in zip(values, weights))
                        weight_sum = sum(weights)
                        if weight_sum > 0:
                            optimized[param_name] = weighted_sum / weight_sum
        
        return optimized
    
    def get_preferred_model(
        self,
        user_id: str,
        task_type: str,
        available_models: List[str]
    ) -> Optional[str]:
        """
        Get preferred model for a user based on feedback
        
        Args:
            user_id: User identifier
            task_type: Type of task
            available_models: List of available models
            
        Returns:
            Preferred model name or None
        """
        if user_id not in self.user_preferences:
            return None
        
        model_prefs = self.user_preferences[user_id].get('model_preferences', {})
        
        # Find best model for this task type
        best_model = None
        best_score = 0.0
        
        for model_name in available_models:
            if model_name in model_prefs:
                prefs = model_prefs[model_name]
                # Score based on positive count and average rating
                positive_ratio = prefs.get('positive_count', 0) / max(prefs.get('usage_count', 1), 1)
                avg_rating = prefs.get('average_rating', 0.0)
                score = (positive_ratio * 0.5) + (avg_rating / 5.0 * 0.5)
                
                if score > best_score:
                    best_score = score
                    best_model = model_name
        
        return best_model
    
    def get_feedback_statistics(
        self,
        user_id: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> Dict:
        """
        Get feedback statistics
        
        Args:
            user_id: Optional user ID to filter
            task_type: Optional task type to filter
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_feedback': 0,
            'positive_count': 0,
            'negative_count': 0,
            'rating_count': 0,
            'average_rating': 0.0,
            'by_task_type': {},
            'by_feedback_type': defaultdict(int)
        }
        
        for key, feedback_list in self.feedback_data.items():
            user_task_id, task = key.rsplit('_', 1) if '_' in key else (key, '')
            
            # Filter by user_id if provided
            if user_id and not user_task_id.startswith(user_id):
                continue
            
            # Filter by task_type if provided
            if task_type and task != task_type:
                continue
            
            for feedback in feedback_list:
                stats['total_feedback'] += 1
                stats['by_feedback_type'][feedback.get('feedback_type', 'unknown')] += 1
                
                if feedback.get('feedback_type') == 'positive':
                    stats['positive_count'] += 1
                elif feedback.get('feedback_type') == 'negative':
                    stats['negative_count'] += 1
                elif feedback.get('feedback_type') == 'rating':
                    stats['rating_count'] += 1
                    rating = feedback.get('rating', 0)
                    if rating > 0:
                        # Update average rating
                        current_avg = stats['average_rating']
                        count = stats['rating_count']
                        stats['average_rating'] = ((current_avg * (count - 1)) + rating) / count
                
                # By task type
                task_type_fb = feedback.get('task_type', 'unknown')
                if task_type_fb not in stats['by_task_type']:
                    stats['by_task_type'][task_type_fb] = {
                        'count': 0,
                        'positive': 0,
                        'negative': 0
                    }
                stats['by_task_type'][task_type_fb]['count'] += 1
                if feedback.get('feedback_type') == 'positive':
                    stats['by_task_type'][task_type_fb]['positive'] += 1
                elif feedback.get('feedback_type') == 'negative':
                    stats['by_task_type'][task_type_fb]['negative'] += 1
        
        return stats
    
    def get_learning_insights(
        self,
        user_id: str,
        task_type: str
    ) -> Dict:
        """
        Get learning insights for a user and task type
        
        Args:
            user_id: User identifier
            task_type: Type of task
            
        Returns:
            Dictionary with insights
        """
        prefs = self.get_user_preferences(user_id, task_type)
        task_prefs = prefs.get('task_preferences', {})
        
        insights = {
            'total_interactions': task_prefs.get('total_feedback', 0),
            'satisfaction_rate': 0.0,
            'preferred_model': None,
            'recommendations': []
        }
        
        if task_prefs.get('total_feedback', 0) > 0:
            positive = task_prefs.get('positive_count', 0)
            total = task_prefs.get('total_feedback', 1)
            insights['satisfaction_rate'] = positive / total
        
        # Get preferred model
        model_prefs = prefs.get('model_preferences', {})
        if model_prefs:
            best_model = max(
                model_prefs.items(),
                key=lambda x: x[1].get('average_rating', 0) * x[1].get('usage_count', 0)
            )
            insights['preferred_model'] = best_model[0]
        
        # Generate recommendations
        if insights['satisfaction_rate'] < 0.5:
            insights['recommendations'].append(
                "Votre taux de satisfaction est faible. Essayez de reformuler vos questions ou d'uploader des documents pertinents."
            )
        
        if task_prefs.get('average_rating', 0) < 3.0:
            insights['recommendations'].append(
                "Les réponses pourraient être améliorées. Essayez d'être plus spécifique dans vos questions."
            )
        
        return insights

