"""
Unit tests for Model Training utilities
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.utils.model_training import ModelTrainer, train_model


@pytest.mark.unit
class TestModelTraining:
    """Test suite for Model Training utilities"""
    
    def test_model_trainer_initialization(self):
        """Test ModelTrainer initialization"""
        trainer = ModelTrainer("qa")
        
        assert trainer.model_type == "qa"
        assert trainer.device in ["cuda", "cpu"]
        assert trainer.base_model_name is not None
    
    def test_model_trainer_default_models(self):
        """Test that default models are set correctly"""
        qa_trainer = ModelTrainer("qa")
        grammar_trainer = ModelTrainer("grammar")
        reformulation_trainer = ModelTrainer("reformulation")
        
        assert "camembert" in qa_trainer.base_model_name.lower() or "bert" in qa_trainer.base_model_name.lower()
        assert grammar_trainer.base_model_name is not None
        assert reformulation_trainer.base_model_name is not None
    
    def test_prepare_training_data_qa(self):
        """Test preparing QA training data"""
        trainer = ModelTrainer("qa")
        training_data = {
            "examples": [
                {
                    "question": "What is AI?",
                    "context": "AI is artificial intelligence",
                    "answer": "artificial intelligence",
                    "answer_start": 0
                }
            ]
        }
        
        dataset = trainer.prepare_training_data(training_data)
        
        assert len(dataset) == 1
        assert "question" in dataset[0]
        assert "context" in dataset[0]
    
    def test_prepare_training_data_grammar(self):
        """Test preparing grammar training data"""
        trainer = ModelTrainer("grammar")
        training_data = {
            "examples": [
                {"text": "Bonjour", "label": "correct"},
                {"text": "Bonjour a", "label": "incorrect"}
            ]
        }
        
        dataset = trainer.prepare_training_data(training_data)
        
        assert len(dataset) == 2
        assert "text" in dataset[0]
        assert "label" in dataset[0]
    
    def test_prepare_training_data_reformulation(self):
        """Test preparing reformulation training data"""
        trainer = ModelTrainer("reformulation")
        training_data = {
            "examples": [
                {
                    "original": "C'est bon",
                    "reformulated": "C'est excellent"
                }
            ]
        }
        
        dataset = trainer.prepare_training_data(training_data)
        
        assert len(dataset) == 1
        assert "input_text" in dataset[0]
        assert "target_text" in dataset[0]
    
    def test_prepare_training_data_empty(self):
        """Test preparing training data with no examples"""
        trainer = ModelTrainer("qa")
        training_data = {"examples": []}
        
        with pytest.raises(ValueError):
            trainer.prepare_training_data(training_data)
    
    @patch('app.utils.model_training.AutoTokenizer')
    @patch('app.utils.model_training.AutoModelForQuestionAnswering')
    def test_load_base_model_qa(self, mock_model, mock_tokenizer):
        """Test loading base model for QA"""
        trainer = ModelTrainer("qa")
        
        mock_tokenizer.from_pretrained.return_value = MagicMock()
        mock_model.from_pretrained.return_value = MagicMock()
        
        trainer._load_base_model()
        
        assert trainer.tokenizer is not None
        assert trainer.model is not None
    
    @patch('app.utils.model_training.ModelTrainer.train')
    @patch('app.utils.model_training.ModelTrainer._load_base_model')
    def test_train_model_function(self, mock_load, mock_train_method):
        """Test train_model convenience function"""
        mock_train_method.return_value = {
            "status": "completed",
            "training_loss": 0.5,
            "eval_loss": 0.6
        }
        
        training_data = {
            "examples": [
                {
                    "question": "Test?",
                    "context": "Test context",
                    "answer": "Test answer",
                    "answer_start": 0
                },
                {
                    "question": "Test2?",
                    "context": "Test context 2",
                    "answer": "Test answer 2",
                    "answer_start": 0
                }
            ]
        }
        result = train_model(
            model_type="qa",
            training_data=training_data,
            output_dir="./test_output",
            num_epochs=1,
            batch_size=2
        )
        
        assert result["status"] == "completed"
        mock_train_method.assert_called_once()

