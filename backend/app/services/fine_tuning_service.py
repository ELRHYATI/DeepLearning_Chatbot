"""
Service for fine-tuning models on academic data
Supports fine-tuning for summarization, reformulation, and QA
"""
import os
import json
from typing import Dict, List, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from app.models import MessageCorrection, Message
from app.utils.logger import get_logger
from app.services.learning_service import LearningService

logger = get_logger()


class FineTuningService:
    """Service for fine-tuning models on academic data"""
    
    def __init__(self):
        self.learning_service = LearningService()
        self.fine_tuned_models_dir = Path("fine_tuned_models")
        self.fine_tuned_models_dir.mkdir(exist_ok=True)
    
    def prepare_fine_tuning_data(
        self,
        db: Session,
        module_type: str,
        min_examples: int = 50,
        max_examples: int = 1000
    ) -> Dict:
        """
        Prepare fine-tuning dataset from user corrections
        
        Args:
            db: Database session
            module_type: Type of module (summarization, reformulation, qa, grammar)
            min_examples: Minimum examples required
            max_examples: Maximum examples to use
        
        Returns:
            Dictionary with dataset info and path
        """
        # Get training data from learning service
        training_data = self.learning_service.prepare_training_data(
            db, module_type, limit=max_examples
        )
        
        if len(training_data) < min_examples:
            return {
                "success": False,
                "error": f"Not enough training data. Need at least {min_examples}, got {len(training_data)}",
                "count": len(training_data)
            }
        
        # Format data according to module type
        formatted_data = []
        
        if module_type == "summarization":
            for item in training_data:
                formatted_data.append({
                    "text": item.get("input", ""),
                    "summary": item.get("output", "")
                })
        elif module_type == "reformulation":
            for item in training_data:
                formatted_data.append({
                    "original": item.get("input", ""),
                    "reformulated": item.get("output", "")
                })
        elif module_type == "qa":
            for item in training_data:
                formatted_data.append({
                    "question": item.get("question", ""),
                    "context": item.get("context", ""),
                    "answer": item.get("answer", "")
                })
        elif module_type == "grammar":
            for item in training_data:
                formatted_data.append({
                    "original": item.get("input", ""),
                    "corrected": item.get("output", "")
                })
        
        # Save dataset
        dataset_path = self.fine_tuned_models_dir / f"{module_type}_dataset.json"
        with open(dataset_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, ensure_ascii=False, indent=2)
        
        # Split into train/validation (80/20)
        split_idx = int(len(formatted_data) * 0.8)
        train_data = formatted_data[:split_idx]
        val_data = formatted_data[split_idx:]
        
        train_path = self.fine_tuned_models_dir / f"{module_type}_train.json"
        val_path = self.fine_tuned_models_dir / f"{module_type}_val.json"
        
        with open(train_path, 'w', encoding='utf-8') as f:
            json.dump(train_data, f, ensure_ascii=False, indent=2)
        
        with open(val_path, 'w', encoding='utf-8') as f:
            json.dump(val_data, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "count": len(formatted_data),
            "train_count": len(train_data),
            "val_count": len(val_data),
            "dataset_path": str(dataset_path),
            "train_path": str(train_path),
            "val_path": str(val_path)
        }
    
    def generate_fine_tuning_script(
        self,
        module_type: str,
        base_model: str,
        output_dir: str,
        train_path: str,
        val_path: str,
        epochs: int = 3,
        batch_size: int = 8,
        learning_rate: float = 5e-5
    ) -> str:
        """
        Generate fine-tuning script for a model
        
        Args:
            module_type: Type of module
            base_model: Base model to fine-tune
            output_dir: Output directory for fine-tuned model
            train_path: Path to training data
            val_path: Path to validation data
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
        
        Returns:
            Path to generated script
        """
        script_path = self.fine_tuned_models_dir / f"fine_tune_{module_type}.py"
        
        if module_type == "summarization":
            script_content = f'''"""
Fine-tuning script for {module_type}
Generated automatically
"""
from transformers import (
    AutoTokenizer, AutoModelForSeq2SeqLM,
    Seq2SeqTrainingArguments, Seq2SeqTrainer,
    DataCollatorForSeq2Seq
)
from datasets import load_dataset
import json

# Load data
def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

train_data = load_data("{train_path}")
val_data = load_data("{val_path}")

# Load model and tokenizer
model_name = "{base_model}"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Prepare dataset
def preprocess_function(examples):
    inputs = [f"Résume: {{ex['text']}}" for ex in examples]
    targets = [ex['summary'] for ex in examples]
    
    model_inputs = tokenizer(inputs, max_length=512, truncation=True, padding=True)
    labels = tokenizer(targets, max_length=128, truncation=True, padding=True)
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

# Training arguments
training_args = Seq2SeqTrainingArguments(
    output_dir="{output_dir}",
    num_train_epochs={epochs},
    per_device_train_batch_size={batch_size},
    per_device_eval_batch_size={batch_size},
    learning_rate={learning_rate},
    warmup_steps=100,
    weight_decay=0.01,
    logging_dir="{output_dir}/logs",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
)

# Trainer
trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=train_data,
    eval_dataset=val_data,
    tokenizer=tokenizer,
    data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model),
)

# Train
trainer.train()
trainer.save_model()
'''
        elif module_type == "reformulation":
            script_content = f'''"""
Fine-tuning script for {module_type}
Generated automatically
"""
from transformers import (
    AutoTokenizer, AutoModelForSeq2SeqLM,
    Seq2SeqTrainingArguments, Seq2SeqTrainer,
    DataCollatorForSeq2Seq
)
import json

# Load data
def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

train_data = load_data("{train_path}")
val_data = load_data("{val_path}")

# Load model and tokenizer
model_name = "{base_model}"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Prepare dataset
def preprocess_function(examples):
    inputs = [f"Réécris: {{ex['original']}}" for ex in examples]
    targets = [ex['reformulated'] for ex in examples]
    
    model_inputs = tokenizer(inputs, max_length=512, truncation=True, padding=True)
    labels = tokenizer(targets, max_length=512, truncation=True, padding=True)
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

# Training arguments
training_args = Seq2SeqTrainingArguments(
    output_dir="{output_dir}",
    num_train_epochs={epochs},
    per_device_train_batch_size={batch_size},
    per_device_eval_batch_size={batch_size},
    learning_rate={learning_rate},
    warmup_steps=100,
    weight_decay=0.01,
    logging_dir="{output_dir}/logs",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
)

# Trainer
trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=train_data,
    eval_dataset=val_data,
    tokenizer=tokenizer,
    data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model),
)

# Train
trainer.train()
trainer.save_model()
'''
        else:
            script_content = f"# Fine-tuning script for {module_type} - Not yet implemented"
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return str(script_path)
    
    def get_fine_tuning_status(self, module_type: str) -> Dict:
        """Get status of fine-tuning for a module"""
        model_path = self.fine_tuned_models_dir / f"{module_type}_model"
        dataset_path = self.fine_tuned_models_dir / f"{module_type}_dataset.json"
        
        return {
            "has_dataset": dataset_path.exists(),
            "has_model": model_path.exists(),
            "dataset_path": str(dataset_path) if dataset_path.exists() else None,
            "model_path": str(model_path) if model_path.exists() else None
        }

