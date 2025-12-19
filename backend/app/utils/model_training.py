"""
Model Training Utilities for Fine-tuning
"""
import os
import json
import torch
from typing import Dict, List, Optional, Any
from transformers import (
    AutoTokenizer, 
    AutoModelForQuestionAnswering,
    AutoModelForSequenceClassification,
    AutoModelForSeq2SeqLM,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding
)
from datasets import Dataset
from app.utils.logger import get_logger

logger = get_logger()


class ModelTrainer:
    """Utility class for training/fine-tuning models"""
    
    def __init__(self, model_type: str, base_model_name: Optional[str] = None):
        """
        Initialize model trainer
        
        Args:
            model_type: Type of model (grammar, qa, reformulation)
            base_model_name: Optional base model name to use
        """
        self.model_type = model_type
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Default models for each type
        self.default_models = {
            "qa": "etalab-ia/camembert-base-squadFR-fquad-piaf",
            "grammar": "dbmdz/bert-base-french-europeana-cased",
            "reformulation": "dbmdz/bert-base-french-europeana-cased"
        }
        
        self.base_model_name = base_model_name or self.default_models.get(
            model_type, 
            "dbmdz/bert-base-french-europeana-cased"
        )
        
        self.tokenizer = None
        self.model = None
    
    def _load_base_model(self):
        """Load the base model and tokenizer"""
        try:
            logger.info(f"Loading base model: {self.base_model_name}")
            
            if self.model_type == "qa":
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.base_model_name,
                    use_fast=False
                )
                self.model = AutoModelForQuestionAnswering.from_pretrained(
                    self.base_model_name
                )
            elif self.model_type == "grammar":
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.base_model_name,
                    use_fast=False
                )
                # For grammar, we use sequence classification
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    self.base_model_name,
                    num_labels=2  # correct/incorrect
                )
            else:  # reformulation
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.base_model_name,
                    use_fast=False
                )
                self.model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.base_model_name
                )
            
            self.model.to(self.device)
            logger.info(f"Base model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Error loading base model: {e}", exc_info=e)
            raise
    
    def prepare_training_data(self, training_data: Dict[str, Any]) -> Dataset:
        """
        Prepare training data in the format required by the model
        
        Args:
            training_data: Dictionary with 'examples' list
            
        Returns:
            Hugging Face Dataset
        """
        examples = training_data.get("examples", [])
        
        if not examples:
            raise ValueError("No training examples provided")
        
        # Format data based on model type
        if self.model_type == "qa":
            formatted_data = self._format_qa_data(examples)
        elif self.model_type == "grammar":
            formatted_data = self._format_grammar_data(examples)
        else:  # reformulation
            formatted_data = self._format_reformulation_data(examples)
        
        # Create Hugging Face Dataset
        dataset = Dataset.from_list(formatted_data)
        
        return dataset
    
    def _format_qa_data(self, examples: List[Dict]) -> List[Dict]:
        """Format data for QA model training"""
        formatted = []
        for ex in examples:
            if "question" in ex and "context" in ex and "answer" in ex:
                formatted.append({
                    "question": ex["question"],
                    "context": ex["context"],
                    "answers": {
                        "text": [ex["answer"]],
                        "answer_start": [ex.get("answer_start", 0)]
                    }
                })
        return formatted
    
    def _format_grammar_data(self, examples: List[Dict]) -> List[Dict]:
        """Format data for grammar model training"""
        formatted = []
        for ex in examples:
            if "text" in ex and "label" in ex:
                formatted.append({
                    "text": ex["text"],
                    "label": 1 if ex["label"] == "correct" else 0
                })
        return formatted
    
    def _format_reformulation_data(self, examples: List[Dict]) -> List[Dict]:
        """Format data for reformulation model training"""
        formatted = []
        for ex in examples:
            if "original" in ex and "reformulated" in ex:
                formatted.append({
                    "input_text": ex["original"],
                    "target_text": ex["reformulated"]
                })
        return formatted
    
    def tokenize_data(self, dataset: Dataset) -> Dataset:
        """Tokenize the dataset"""
        if not self.tokenizer:
            self._load_base_model()
        
        def tokenize_function(examples):
            if self.model_type == "qa":
                return self.tokenizer(
                    examples["question"],
                    examples["context"],
                    truncation=True,
                    padding="max_length",
                    max_length=512
                )
            elif self.model_type == "grammar":
                return self.tokenizer(
                    examples["text"],
                    truncation=True,
                    padding="max_length",
                    max_length=256
                )
            else:  # reformulation
                inputs = self.tokenizer(
                    examples["input_text"],
                    truncation=True,
                    padding="max_length",
                    max_length=256
                )
                targets = self.tokenizer(
                    examples["target_text"],
                    truncation=True,
                    padding="max_length",
                    max_length=256
                )
                inputs["labels"] = targets["input_ids"]
                return inputs
        
        return dataset.map(tokenize_function, batched=True)
    
    def train(
        self,
        training_data: Dict[str, Any],
        output_dir: str,
        num_epochs: int = 3,
        batch_size: int = 8,
        learning_rate: float = 2e-5,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Train/fine-tune the model
        
        Args:
            training_data: Training data dictionary
            output_dir: Directory to save the trained model
            num_epochs: Number of training epochs
            batch_size: Training batch size
            learning_rate: Learning rate
            progress_callback: Optional callback function(progress: int) for updates
            
        Returns:
            Dictionary with training results
        """
        try:
            # Load base model
            if not self.model:
                self._load_base_model()
            
            # Prepare data
            if progress_callback:
                progress_callback(10)
            
            dataset = self.prepare_training_data(training_data)
            tokenized_dataset = self.tokenize_data(dataset)
            
            if progress_callback:
                progress_callback(20)
            
            # Split dataset (80% train, 20% validation)
            train_size = int(0.8 * len(tokenized_dataset))
            train_dataset = tokenized_dataset.select(range(train_size))
            eval_dataset = tokenized_dataset.select(range(train_size, len(tokenized_dataset)))
            
            # Training arguments
            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=num_epochs,
                per_device_train_batch_size=batch_size,
                per_device_eval_batch_size=batch_size,
                learning_rate=learning_rate,
                weight_decay=0.01,
                logging_dir=f"{output_dir}/logs",
                logging_steps=10,
                eval_strategy="epoch",
                save_strategy="epoch",
                load_best_model_at_end=True,
                metric_for_best_model="loss",
                greater_is_better=False,
            )
            
            # Data collator
            data_collator = DataCollatorWithPadding(tokenizer=self.tokenizer)
            
            # Create trainer
            trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=eval_dataset,
                data_collator=data_collator,
            )
            
            if progress_callback:
                progress_callback(30)
            
            # Train
            logger.info(f"Starting training for {self.model_type} model")
            train_result = trainer.train()
            
            if progress_callback:
                progress_callback(80)
            
            # Save model
            trainer.save_model()
            self.tokenizer.save_pretrained(output_dir)
            
            if progress_callback:
                progress_callback(90)
            
            # Evaluate
            eval_result = trainer.evaluate()
            
            if progress_callback:
                progress_callback(100)
            
            logger.info(f"Training completed. Final loss: {train_result.training_loss}")
            
            return {
                "status": "completed",
                "training_loss": train_result.training_loss,
                "eval_loss": eval_result.get("eval_loss", 0),
                "model_path": output_dir,
                "num_samples": len(dataset)
            }
            
        except Exception as e:
            logger.error(f"Error during training: {e}", exc_info=e)
            raise


def train_model(
    model_type: str,
    training_data: Dict[str, Any],
    output_dir: str,
    base_model_name: Optional[str] = None,
    num_epochs: int = 3,
    batch_size: int = 8,
    learning_rate: float = 2e-5,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Convenience function to train a model
    
    Args:
        model_type: Type of model (grammar, qa, reformulation)
        training_data: Training data dictionary
        output_dir: Directory to save the trained model
        base_model_name: Optional base model name
        num_epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Learning rate
        progress_callback: Optional progress callback
        
    Returns:
        Training results dictionary
    """
    trainer = ModelTrainer(model_type, base_model_name)
    return trainer.train(
        training_data=training_data,
        output_dir=output_dir,
        num_epochs=num_epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        progress_callback=progress_callback
    )

