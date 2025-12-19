"""
Tâches Celery pour le traitement asynchrone
"""
from app.celery_app import celery_app
from app.utils.logger import get_logger
from app.services.document_processor import DocumentProcessor
from app.services.reformulation_service import ReformulationService
from app.services.grammar_service import GrammarService
import os
import json

logger = get_logger()

# Instances des services (initialisées une fois)
document_processor = None
reformulation_service = None
grammar_service = None


def get_document_processor():
    """Lazy loading du document processor"""
    global document_processor
    if document_processor is None:
        document_processor = DocumentProcessor()
    return document_processor


def get_reformulation_service():
    """Lazy loading du reformulation service"""
    global reformulation_service
    if reformulation_service is None:
        reformulation_service = ReformulationService()
    return reformulation_service


def get_grammar_service():
    """Lazy loading du grammar service"""
    global grammar_service
    if grammar_service is None:
        grammar_service = GrammarService()
    return grammar_service


@celery_app.task(bind=True, name="app.tasks.process_document")
def process_document(self, file_path: str, file_type: str, user_id: int, document_id: int):
    """
    Traite un document de manière asynchrone
    
    Args:
        file_path: Chemin vers le fichier
        file_type: Type de fichier (pdf, txt, docx)
        user_id: ID de l'utilisateur
        document_id: ID du document
    
    Returns:
        Résultat du traitement
    """
    try:
        logger.info(
            f"Starting document processing task: {self.request.id}",
            extra_data={"file_path": file_path, "user_id": user_id, "document_id": document_id}
        )
        
        processor = get_document_processor()
        result = processor.process_document(file_path, file_type, preserve_structure=True)
        
        logger.info(
            f"Document processing completed: {self.request.id}",
            extra_data={"document_id": document_id, "corrections_count": result.get("corrections_count", 0)}
        )
        
        return {
            "status": "completed",
            "document_id": document_id,
            "result": result
        }
    except Exception as e:
        logger.error(
            f"Error in document processing task: {self.request.id}",
            exc_info=e,
            extra_data={"file_path": file_path, "user_id": user_id}
        )
        raise


@celery_app.task(bind=True, name="app.tasks.finetune_model")
def finetune_model(self, job_id: int, user_id: int, model_type: str, training_data: dict):
    """
    Fine-tune un modèle de manière asynchrone
    
    Args:
        job_id: ID du job de fine-tuning
        user_id: ID de l'utilisateur
        model_type: Type de modèle (grammar, qa, reformulation)
        training_data: Données d'entraînement
    
    Returns:
        Résultat du fine-tuning
    """
    try:
        logger.info(
            f"Starting fine-tuning task: {self.request.id}",
            extra_data={"job_id": job_id, "user_id": user_id, "model_type": model_type}
        )
        
        # Mettre à jour la progression
        self.update_state(state="PROGRESS", meta={"progress": 10})
        
        # Simuler l'entraînement (à remplacer par un vrai entraînement)
        import time
        
        for progress in [20, 40, 60, 80, 90, 95]:
            time.sleep(2)
            self.update_state(state="PROGRESS", meta={"progress": progress})
        
        # Sauvegarder le modèle
        model_path = f"./fine_tuned_models/{user_id}/{job_id}/{model_type}"
        os.makedirs(model_path, exist_ok=True)
        
        metadata = {
            "job_id": job_id,
            "user_id": user_id,
            "model_type": model_type,
            "training_data_size": len(training_data.get("examples", [])),
        }
        
        with open(f"{model_path}/metadata.json", "w") as f:
            json.dump(metadata, f)
        
        logger.info(
            f"Fine-tuning completed: {self.request.id}",
            extra_data={"job_id": job_id, "model_path": model_path}
        )
        
        return {
            "status": "completed",
            "job_id": job_id,
            "model_path": model_path,
            "progress": 100
        }
    except Exception as e:
        logger.error(
            f"Error in fine-tuning task: {self.request.id}",
            exc_info=e,
            extra_data={"job_id": job_id, "user_id": user_id}
        )
        raise


@celery_app.task(bind=True, name="app.tasks.generate_report")
def generate_report(self, session_id: int, user_id: int, format: str = "pdf"):
    """
    Génère un rapport de session de manière asynchrone
    
    Args:
        session_id: ID de la session
        user_id: ID de l'utilisateur
        format: Format du rapport (pdf, markdown)
    
    Returns:
        Chemin vers le rapport généré
    """
    try:
        logger.info(
            f"Starting report generation task: {self.request.id}",
            extra_data={"session_id": session_id, "user_id": user_id, "format": format}
        )
        
        # Importer ici pour éviter les imports circulaires
        from app.utils.export import export_to_pdf, export_to_markdown
        from app.database import SessionLocal
        from app.models import ChatSession, Message
        
        db = SessionLocal()
        try:
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            ).first()
            
            if not session:
                raise ValueError("Session not found")
            
            messages = db.query(Message).filter(
                Message.session_id == session_id
            ).order_by(Message.created_at).all()
            
            messages_data = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "module_type": msg.module_type,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
            
            if format == "pdf":
                report_bytes = export_to_pdf(session.title, messages_data)
                report_path = f"./reports/{user_id}/{session_id}_report.pdf"
            else:
                report_content = export_to_markdown(session.title, messages_data)
                report_path = f"./reports/{user_id}/{session_id}_report.md"
                os.makedirs(os.path.dirname(report_path), exist_ok=True)
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(report_content)
                return {"status": "completed", "report_path": report_path}
            
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, "wb") as f:
                f.write(report_bytes)
            
            logger.info(
                f"Report generation completed: {self.request.id}",
                extra_data={"session_id": session_id, "report_path": report_path}
            )
            
            return {"status": "completed", "report_path": report_path}
        finally:
            db.close()
    except Exception as e:
        logger.error(
            f"Error in report generation task: {self.request.id}",
            exc_info=e,
            extra_data={"session_id": session_id, "user_id": user_id}
        )
        raise

