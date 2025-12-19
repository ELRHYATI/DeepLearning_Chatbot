"""
Système de logging structuré avec JSON, rotation des logs et tracking des performances
"""
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional, Dict, Any
import traceback
from functools import wraps
import time


class JSONFormatter(logging.Formatter):
    """Formatter personnalisé pour les logs JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Formate un log en JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Ajouter les données supplémentaires si présentes
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        # Ajouter l'exception si présente
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info) if record.exc_info else None
            }
        
        # Ajouter les données de performance si présentes
        if hasattr(record, "performance"):
            log_data["performance"] = record.performance
        
        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger:
    """Logger structuré avec rotation et tracking des performances"""
    
    def __init__(
        self,
        name: str = "academic_chatbot",
        log_dir: str = "logs",
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5,
        when: str = "midnight",
        interval: int = 1,
        level: int = logging.INFO
    ):
        """
        Initialise le logger structuré
        
        Args:
            name: Nom du logger
            log_dir: Répertoire pour les logs
            max_bytes: Taille maximale d'un fichier de log avant rotation (en bytes)
            backup_count: Nombre de fichiers de backup à conserver
            when: Moment de rotation pour TimedRotatingFileHandler ('midnight', 'H', 'D', etc.)
            interval: Intervalle de rotation
            level: Niveau de logging
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Créer le logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Éviter les handlers dupliqués
        if self.logger.handlers:
            return
        
        # Handler pour les logs JSON avec rotation par taille
        json_log_file = self.log_dir / f"{name}.json.log"
        json_handler = RotatingFileHandler(
            json_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        json_handler.setFormatter(JSONFormatter())
        json_handler.setLevel(level)
        self.logger.addHandler(json_handler)
        
        # Handler pour les logs JSON avec rotation par temps (quotidienne)
        json_timed_log_file = self.log_dir / f"{name}.json"
        json_timed_handler = TimedRotatingFileHandler(
            json_timed_log_file,
            when=when,
            interval=interval,
            backupCount=backup_count,
            encoding='utf-8'
        )
        json_timed_handler.setFormatter(JSONFormatter())
        json_timed_handler.setLevel(level)
        self.logger.addHandler(json_timed_handler)
        
        # Handler pour la console (format lisible)
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(level)
        self.logger.addHandler(console_handler)
    
    def _log_with_extra(
        self,
        level: int,
        message: str,
        extra_data: Optional[Dict[str, Any]] = None,
        performance: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None
    ):
        """Méthode interne pour logger avec données supplémentaires"""
        extra = {}
        if extra_data:
            extra["extra_data"] = extra_data
        if performance:
            extra["performance"] = performance
        
        self.logger.log(level, message, extra=extra, exc_info=exc_info)
    
    def debug(self, message: str, **kwargs):
        """Log niveau DEBUG"""
        self._log_with_extra(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log niveau INFO"""
        self._log_with_extra(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log niveau WARNING"""
        self._log_with_extra(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """Log niveau ERROR"""
        self._log_with_extra(logging.ERROR, message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """Log niveau CRITICAL"""
        self._log_with_extra(logging.CRITICAL, message, exc_info=exc_info, **kwargs)
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[int] = None,
        client_ip: Optional[str] = None,
        **kwargs
    ):
        """Log une requête API avec métriques de performance"""
        self.info(
            f"{method} {path} - {status_code}",
            extra_data={
                "event": "api_request",
                "method": method,
                "path": path,
                "status_code": status_code,
                "user_id": user_id,
                "client_ip": client_ip,
                **kwargs
            },
            performance={
                "duration_ms": round(duration_ms, 2),
                "duration_s": round(duration_ms / 1000, 3)
            }
        )
    
    def log_model_performance(
        self,
        model_name: str,
        operation: str,
        duration_ms: float,
        input_size: Optional[int] = None,
        output_size: Optional[int] = None,
        **kwargs
    ):
        """Log les performances d'un modèle ML"""
        self.info(
            f"Model {model_name} - {operation}",
            extra_data={
                "event": "model_performance",
                "model_name": model_name,
                "operation": operation,
                "input_size": input_size,
                "output_size": output_size,
                **kwargs
            },
            performance={
                "duration_ms": round(duration_ms, 2),
                "duration_s": round(duration_ms / 1000, 3),
                "throughput": round(input_size / (duration_ms / 1000), 2) if input_size and duration_ms > 0 else None
            }
        )
    
    def log_database_operation(
        self,
        operation: str,
        table: str,
        duration_ms: float,
        rows_affected: Optional[int] = None,
        **kwargs
    ):
        """Log une opération de base de données"""
        self.info(
            f"Database {operation} on {table}",
            extra_data={
                "event": "database_operation",
                "operation": operation,
                "table": table,
                "rows_affected": rows_affected,
                **kwargs
            },
            performance={
                "duration_ms": round(duration_ms, 2),
                "duration_s": round(duration_ms / 1000, 3)
            }
        )
    
    def log_error_with_context(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log une erreur avec contexte"""
        self.error(
            f"Error: {str(error)}",
            exc_info=error,
            extra_data={
                "event": "error",
                "error_type": type(error).__name__,
                "context": context or {},
                **kwargs
            }
        )


# Instance globale du logger
_logger_instance: Optional[StructuredLogger] = None


def get_logger(name: str = "academic_chatbot", **kwargs) -> StructuredLogger:
    """Obtient ou crée l'instance globale du logger"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = StructuredLogger(name=name, **kwargs)
    return _logger_instance


def performance_tracker(operation_name: str = None):
    """Décorateur pour tracker les performances d'une fonction"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            logger = get_logger()
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_model_performance(
                    model_name=op_name,
                    operation="execute",
                    duration_ms=duration_ms
                )
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.log_error_with_context(
                    error=e,
                    context={
                        "operation": op_name,
                        "duration_ms": duration_ms
                    }
                )
                raise
        
        return wrapper
    return decorator


def async_performance_tracker(operation_name: str = None):
    """Décorateur pour tracker les performances d'une fonction async"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            logger = get_logger()
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_model_performance(
                    model_name=op_name,
                    operation="execute",
                    duration_ms=duration_ms
                )
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.log_error_with_context(
                    error=e,
                    context={
                        "operation": op_name,
                        "duration_ms": duration_ms
                    }
                )
                raise
        
        return wrapper
    return decorator

