"""
Health checks avancés pour le monitoring
"""
from typing import Dict, Any, Optional
from datetime import datetime
import os
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
from app.utils.logger import get_logger
from app.database import SessionLocal
from app.models import User, ChatSession, Message
from app.utils.redis_cache import cache
from app.celery_app import celery_app

logger = get_logger()


def check_database() -> Dict[str, Any]:
    """
    Vérifie la santé de la base de données
    
    Returns:
        Statut de la base de données
    """
    try:
        db = SessionLocal()
        try:
            # Test de connexion
            db.execute("SELECT 1")
            
            # Statistiques
            user_count = db.query(User).count()
            session_count = db.query(ChatSession).count()
            message_count = db.query(Message).count()
            
            return {
                "status": "healthy",
                "connected": True,
                "stats": {
                    "users": user_count,
                    "sessions": session_count,
                    "messages": message_count
                }
            }
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=e)
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


def check_redis() -> Dict[str, Any]:
    """
    Vérifie la santé de Redis
    
    Returns:
        Statut de Redis
    """
    try:
        stats = cache.get_stats()
        if cache.use_redis:
            return {
                "status": "healthy",
                "connected": True,
                "stats": stats
            }
        else:
            return {
                "status": "degraded",
                "connected": False,
                "fallback": "memory_cache",
                "stats": stats
            }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}", exc_info=e)
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


def check_celery() -> Dict[str, Any]:
    """
    Vérifie la santé de Celery
    
    Returns:
        Statut de Celery
    """
    try:
        # Vérifier la connexion au broker
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            return {
                "status": "healthy",
                "connected": True,
                "active_workers": len(active_workers),
                "workers": list(active_workers.keys())
            }
        else:
            return {
                "status": "degraded",
                "connected": True,
                "active_workers": 0,
                "message": "No active workers"
            }
    except Exception as e:
        logger.error(f"Celery health check failed: {e}", exc_info=e)
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


def check_disk_space() -> Dict[str, Any]:
    """
    Vérifie l'espace disque disponible
    
    Returns:
        Statut de l'espace disque
    """
    if not PSUTIL_AVAILABLE:
        return {"status": "unknown", "error": "psutil not available"}
    
    try:
        disk = psutil.disk_usage('/')
        free_gb = disk.free / (1024 ** 3)
        total_gb = disk.total / (1024 ** 3)
        used_percent = (disk.used / disk.total) * 100
        
        status = "healthy"
        if used_percent > 90:
            status = "critical"
        elif used_percent > 80:
            status = "warning"
        
        return {
            "status": status,
            "free_gb": round(free_gb, 2),
            "total_gb": round(total_gb, 2),
            "used_percent": round(used_percent, 2)
        }
    except Exception as e:
        logger.error(f"Disk space check failed: {e}", exc_info=e)
        return {
            "status": "unknown",
            "error": str(e)
        }


def check_memory() -> Dict[str, Any]:
    """
    Vérifie l'utilisation de la mémoire
    
    Returns:
        Statut de la mémoire
    """
    if not PSUTIL_AVAILABLE:
        return {"status": "unknown", "error": "psutil not available"}
    
    try:
        memory = psutil.virtual_memory()
        used_percent = memory.percent
        available_gb = memory.available / (1024 ** 3)
        total_gb = memory.total / (1024 ** 3)
        
        status = "healthy"
        if used_percent > 90:
            status = "critical"
        elif used_percent > 80:
            status = "warning"
        
        return {
            "status": status,
            "used_percent": round(used_percent, 2),
            "available_gb": round(available_gb, 2),
            "total_gb": round(total_gb, 2)
        }
    except Exception as e:
        logger.error(f"Memory check failed: {e}", exc_info=e)
        return {
            "status": "unknown",
            "error": str(e)
        }


def check_models() -> Dict[str, Any]:
    """
    Vérifie l'état des modèles ML
    
    Returns:
        Statut des modèles
    """
    models_status = {}
    
    # Vérifier GrammarService
    try:
        from app.services.grammar_service import GrammarService
        grammar_service = GrammarService()
        models_status["grammar"] = {
            "status": "ready" if grammar_service.tool else "not_loaded",
            "available": grammar_service.tool is not None
        }
    except Exception as e:
        models_status["grammar"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Vérifier QAService
    try:
        from app.services.qa_service import QAService
        qa_service = QAService()
        models_status["qa"] = {
            "status": "ready" if qa_service.qa_pipeline else "not_loaded",
            "available": qa_service.qa_pipeline is not None
        }
    except Exception as e:
        models_status["qa"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Vérifier ReformulationService
    try:
        from app.services.reformulation_service import ReformulationService
        reformulation_service = ReformulationService()
        models_status["reformulation"] = {
            "status": "ready" if reformulation_service.reformulation_pipeline else "not_loaded",
            "available": reformulation_service.reformulation_pipeline is not None
        }
    except Exception as e:
        models_status["reformulation"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Déterminer le statut global
    all_ready = all(m.get("available", False) for m in models_status.values())
    
    return {
        "status": "healthy" if all_ready else "degraded",
        "models": models_status
    }


def get_comprehensive_health() -> Dict[str, Any]:
    """
    Récupère un health check complet de tous les composants
    
    Returns:
        Rapport de santé complet
    """
    checks = {
        "timestamp": datetime.utcnow().isoformat(),
        "database": check_database(),
        "redis": check_redis(),
        "celery": check_celery(),
        "disk_space": check_disk_space(),
        "memory": check_memory(),
        "models": check_models()
    }
    
    # Déterminer le statut global
    statuses = [check.get("status", "unknown") for check in checks.values() if isinstance(check, dict)]
    
    if "unhealthy" in statuses or "critical" in statuses:
        overall_status = "unhealthy"
    elif "degraded" in statuses or "warning" in statuses:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    checks["overall_status"] = overall_status
    
    return checks

