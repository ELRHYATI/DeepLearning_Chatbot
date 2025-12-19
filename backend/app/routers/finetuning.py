"""
Router pour le fine-tuning personnalisé
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import User, FineTuningJob
from app.routers.auth import get_current_user
from app.schemas import FineTuningJobCreate, FineTuningJobResponse
from app.utils.logger import get_logger
from datetime import datetime
import json
import os

logger = get_logger()

router = APIRouter()


def train_model_async(job_id: int, user_id: int, model_type: str, training_data: dict, db: Session):
    """
    Fonction asynchrone pour entraîner le modèle
    
    Args:
        job_id: ID du job de fine-tuning
        user_id: ID de l'utilisateur
        model_type: Type de modèle à entraîner
        training_data: Données d'entraînement
        db: Session de base de données
    """
    try:
        # Mettre à jour le statut
        job = db.query(FineTuningJob).filter(FineTuningJob.id == job_id).first()
        if not job:
            return
        
        job.status = "training"
        job.progress = 10
        db.commit()
        
        logger.info(
            f"Starting fine-tuning job {job_id}",
            extra_data={"job_id": job_id, "user_id": user_id, "model_type": model_type}
        )
        
        # Progress callback function
        def update_progress(progress: int):
            job.progress = progress
            db.commit()
        
        # Prepare model path
        model_path = f"./fine_tuned_models/{user_id}/{job_id}/{model_type}"
        os.makedirs(model_path, exist_ok=True)
        
        # Import training utility
        from app.utils.model_training import train_model
        
        # Train the model
        training_result = train_model(
            model_type=model_type,
            training_data=training_data,
            output_dir=model_path,
            num_epochs=3,  # Can be made configurable
            batch_size=8,
            learning_rate=2e-5,
            progress_callback=update_progress
        )
        
        # Sauvegarder les métadonnées
        metadata = {
            "job_id": job_id,
            "user_id": user_id,
            "model_type": model_type,
            "training_data_size": len(training_data.get("examples", [])),
            "training_loss": training_result.get("training_loss", 0),
            "eval_loss": training_result.get("eval_loss", 0),
            "created_at": datetime.utcnow().isoformat()
        }
        
        with open(f"{model_path}/metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Mettre à jour le job
        job.status = "completed"
        job.progress = 100
        job.model_path = model_path
        job.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(
            f"Fine-tuning job {job_id} completed",
            extra_data={"job_id": job_id, "model_path": model_path, "training_loss": training_result.get("training_loss")}
        )
    
    except Exception as e:
        logger.error(f"Error in fine-tuning job {job_id}: {e}", exc_info=e)
        job = db.query(FineTuningJob).filter(FineTuningJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()


@router.post("/", response_model=FineTuningJobResponse)
async def create_finetuning_job(
    job_data: FineTuningJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée un nouveau job de fine-tuning
    
    Args:
        job_data: Données du job (nom, type de modèle, données d'entraînement)
        background_tasks: Tâches en arrière-plan
        db: Session de base de données
        current_user: Utilisateur actuel
    
    Returns:
        Job de fine-tuning créé
    """
    # Valider le type de modèle
    if job_data.model_type not in ["grammar", "qa", "reformulation"]:
        raise HTTPException(status_code=400, detail="Type de modèle invalide")
    
    # Valider les données d'entraînement
    if not job_data.training_data or "examples" not in job_data.training_data:
        raise HTTPException(status_code=400, detail="Données d'entraînement invalides")
    
    # Créer le job
    new_job = FineTuningJob(
        user_id=current_user.id,
        job_name=job_data.job_name,
        model_type=job_data.model_type,
        training_data=json.dumps(job_data.training_data),
        status="pending",
        progress=0
    )
    
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    # Démarrer l'entraînement en arrière-plan
    background_tasks.add_task(
        train_model_async,
        new_job.id,
        current_user.id,
        job_data.model_type,
        job_data.training_data,
        db
    )
    
    logger.info(
        f"Fine-tuning job created: {new_job.id}",
        extra_data={"job_id": new_job.id, "user_id": current_user.id, "model_type": job_data.model_type}
    )
    
    return FineTuningJobResponse(
        id=new_job.id,
        job_name=new_job.job_name,
        model_type=new_job.model_type,
        status=new_job.status,
        progress=new_job.progress,
        created_at=new_job.created_at,
        completed_at=new_job.completed_at,
        error_message=new_job.error_message
    )


@router.get("/", response_model=List[FineTuningJobResponse])
async def list_finetuning_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste tous les jobs de fine-tuning de l'utilisateur
    
    Args:
        db: Session de base de données
        current_user: Utilisateur actuel
    
    Returns:
        Liste des jobs de fine-tuning
    """
    jobs = db.query(FineTuningJob).filter(
        FineTuningJob.user_id == current_user.id
    ).order_by(FineTuningJob.created_at.desc()).all()
    
    return [
        FineTuningJobResponse(
            id=job.id,
            job_name=job.job_name,
            model_type=job.model_type,
            status=job.status,
            progress=job.progress,
            created_at=job.created_at,
            completed_at=job.completed_at,
            error_message=job.error_message
        )
        for job in jobs
    ]


@router.get("/{job_id}", response_model=FineTuningJobResponse)
async def get_finetuning_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère un job de fine-tuning spécifique
    
    Args:
        job_id: ID du job
        db: Session de base de données
        current_user: Utilisateur actuel
    
    Returns:
        Job de fine-tuning
    """
    job = db.query(FineTuningJob).filter(
        FineTuningJob.id == job_id,
        FineTuningJob.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job de fine-tuning non trouvé")
    
    return FineTuningJobResponse(
        id=job.id,
        job_name=job.job_name,
        model_type=job.model_type,
        status=job.status,
        progress=job.progress,
        created_at=job.created_at,
        completed_at=job.completed_at,
        error_message=job.error_message
    )


@router.delete("/{job_id}")
async def delete_finetuning_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprime un job de fine-tuning
    
    Args:
        job_id: ID du job
        db: Session de base de données
        current_user: Utilisateur actuel
    
    Returns:
        Message de confirmation
    """
    job = db.query(FineTuningJob).filter(
        FineTuningJob.id == job_id,
        FineTuningJob.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job de fine-tuning non trouvé")
    
    # Supprimer le modèle si existant
    if job.model_path and os.path.exists(job.model_path):
        import shutil
        shutil.rmtree(job.model_path)
    
    db.delete(job)
    db.commit()
    
    logger.info(
        f"Fine-tuning job deleted: {job_id}",
        extra_data={"job_id": job_id, "user_id": current_user.id}
    )
    
    return {"message": "Job de fine-tuning supprimé avec succès"}

