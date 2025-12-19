"""
Configuration Celery pour le traitement asynchrone
"""
import os
from celery import Celery
from app.utils.logger import get_logger

logger = get_logger()

# Configuration Redis pour Celery
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# URL du broker Redis
if REDIS_PASSWORD:
    broker_url = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
else:
    broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Configuration Celery
celery_app = Celery(
    "academic_chatbot",
    broker=broker_url,
    backend=broker_url,
    include=["app.tasks"]
)

# Configuration des tâches
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max par tâche
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Routes de tâches
celery_app.conf.task_routes = {
    "app.tasks.process_document": {"queue": "documents"},
    "app.tasks.finetune_model": {"queue": "training"},
    "app.tasks.generate_report": {"queue": "reports"},
}

logger.info("Celery app configured", extra_data={"broker": broker_url})

