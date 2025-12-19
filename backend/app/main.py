from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uvicorn
from typing import List, Optional
from contextlib import asynccontextmanager
import asyncio
import os
from dotenv import load_dotenv

from app.database import get_db, init_db
from app.routers import grammar, qa, reformulation, chat, documents, auth, statistics, feedback, api_keys, collaboration, finetuning, learning, plagiarism, suggestions
from app.models import User
from app.utils.logger import get_logger
from app.middleware.performance_middleware import PerformanceMiddleware
from app.utils.error_handler import global_exception_handler, AppException
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

load_dotenv()

# Configurer Java AVANT toute autre initialisation pour prévenir les logs
try:
    from app.utils.java_log_prevention import ensure_java_log_prevention
    ensure_java_log_prevention()
except Exception as e:
    print(f"Warning: Could not configure Java log prevention: {e}")

# Initialiser le logger
logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    logger.info("Starting application", extra_data={"event": "application_startup"})
    
    try:
        init_db()
        logger.info("Database initialized", extra_data={"event": "database_init"})
    except Exception as e:
        logger.error("Failed to initialize database", exc_info=e)
        raise
    
    # Clean Java crash logs on startup - clean in backend directory
    try:
        from app.utils.log_cleaner import clean_java_crash_logs
        import os
        
        # Get the backend directory (where main.py is located)
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Clean logs in backend directory
        deleted = clean_java_crash_logs(backend_dir)
        if deleted:
            logger.info(
                f"Cleaned {len(deleted)} Java crash log file(s) on startup",
                extra_data={"event": "log_cleanup", "files_deleted": len(deleted), "directory": backend_dir}
            )
        
        # Also clean in parent directory (project root) if logs exist there
        parent_dir = os.path.dirname(backend_dir)
        deleted_parent = clean_java_crash_logs(parent_dir)
        if deleted_parent:
            logger.info(
                f"Cleaned {len(deleted_parent)} Java crash log file(s) from parent directory",
                extra_data={"event": "log_cleanup", "files_deleted": len(deleted_parent), "directory": parent_dir}
            )
    except Exception as e:
        logger.warning("Could not clean logs on startup", exc_info=e)
    
    logger.info("Application started successfully", extra_data={"event": "application_ready"})
    
    yield
    
    # Shutdown
    try:
        logger.info("Shutting down application", extra_data={"event": "application_shutdown"})
        
        # Close database connections gracefully
        try:
            from app.database import engine
            if engine:
                engine.dispose()
                logger.info("Database connections closed", extra_data={"event": "database_shutdown"})
        except Exception as e:
            logger.warning(f"Error closing database connections: {e}")
        
        logger.info("Application shutdown complete", extra_data={"event": "application_shutdown_complete"})
    except asyncio.CancelledError:
        # Expected during shutdown (Ctrl+C), don't log as error
        pass
    except Exception as e:
        # Don't raise exceptions during shutdown - just log
        try:
            logger.warning(f"Error during shutdown: {e}", exc_info=e)
        except:
            # If even logging fails, just print
            print(f"Error during shutdown: {e}")


app = FastAPI(
    title="French Academic AI Chatbot",
    description="A comprehensive French Academic AI Chatbot with grammar correction, QA, and text reformulation",
    version="1.0.0",
    lifespan=lifespan
)

# Handler global pour les exceptions
from fastapi import HTTPException
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, global_exception_handler)
app.add_exception_handler(StarletteHTTPException, global_exception_handler)
app.add_exception_handler(RequestValidationError, global_exception_handler)
app.add_exception_handler(AppException, global_exception_handler)

# Middleware de performance (doit être ajouté avant CORS pour capturer toutes les requêtes)
app.add_middleware(PerformanceMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(grammar.router, prefix="/api/grammar", tags=["Grammar Correction"])
app.include_router(qa.router, prefix="/api/qa", tags=["Question Answering"])
app.include_router(reformulation.router, prefix="/api/reformulation", tags=["Text Reformulation"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["Statistics"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(api_keys.router, prefix="/api/keys", tags=["API Keys"])
app.include_router(collaboration.router, prefix="/api/collaboration", tags=["Collaboration"])
app.include_router(finetuning.router, prefix="/api/finetuning", tags=["Fine-tuning"])
app.include_router(learning.router, prefix="/api/learning", tags=["Interactive Learning"])
app.include_router(plagiarism.router, prefix="/api/plagiarism", tags=["Plagiarism Detection"])
app.include_router(suggestions.router, prefix="/api/suggestions", tags=["AI Suggestions"])

@app.get("/")
async def root():
    return {"message": "French Academic AI Chatbot API", "status": "running"}

@app.get("/api/health")
async def health_check():
    """Health check basique"""
    return {"status": "healthy", "service": "French Academic AI Chatbot"}

@app.get("/api/health/detailed")
async def detailed_health_check():
    """Health check détaillé avec tous les composants"""
    from app.utils.health_check import get_comprehensive_health
    return get_comprehensive_health()

@app.get("/api/health/ready")
async def readiness_check():
    """Readiness check pour Kubernetes"""
    from app.utils.health_check import check_database, check_models
    db_status = check_database()
    models_status = check_models()
    
    if db_status.get("status") == "healthy" and models_status.get("status") in ["healthy", "degraded"]:
        return {"status": "ready"}
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Service not ready")

@app.get("/api/health/live")
async def liveness_check():
    """Liveness check pour Kubernetes"""
    return {"status": "alive"}

@app.get("/api/ollama/status")
async def ollama_status():
    """Check Ollama service status and available models"""
    try:
        from app.services.ollama_service import OllamaService
        service = OllamaService()
        # Recheck connection
        is_available = service.is_available(recheck=True)
        
        # Model recommendations by mode with descriptions
        model_recommendations = {
            "general": {
                "fast": "mistral:7b-instruct-q4_0",
                "balanced": "mistral:7b-instruct",
                "quality": "llama3.1:8b",
                "best": "mistral:7b-instruct",
                "description": "Meilleur pour les conversations générales et le dialogue"
            },
            "qa": {
                "fast": "mistral:7b-instruct-q4_0",
                "balanced": "llama3.1:8b",
                "quality": "mistral-nemo:12b",
                "best": "llama3.1:8b",
                "description": "Meilleur pour répondre aux questions académiques"
            },
            "reformulation": {
                "fast": "mistral:7b-instruct-q4_0",
                "balanced": "mistral:7b-instruct",
                "quality": "mistral-nemo:12b",
                "best": "mistral:7b-instruct",
                "description": "Meilleur pour reformuler et améliorer les textes"
            },
            "grammar": {
                "fast": "mistral:7b-instruct-q4_0",
                "balanced": "mistral:7b-instruct",
                "quality": "llama3.1:8b",
                "best": "mistral:7b-instruct",
                "description": "Meilleur pour la correction grammaticale et orthographique"
            },
            "summarization": {
                "fast": "mistral:7b-instruct-q4_0",
                "balanced": "mistral:7b-instruct",
                "quality": "llama3.1:8b",
                "best": "mistral:7b-instruct",
                "description": "Meilleur pour résumer des textes et extraire les points clés"
            },
            "ollama": {
                "fast": "mistral:7b-instruct-q4_0",
                "balanced": "mistral:7b-instruct",
                "quality": "llama3.1:8b",
                "best": "mistral:7b-instruct",
                "description": "Mode Ollama pour toutes les opérations"
            }
        }
        
        # Get available models with metadata
        available_models = service.get_available_models()
        models_with_info = []
        
        # Model metadata
        model_info = {
            "mistral:7b-instruct-q4_0": {"name": "Mistral 7B Instruct (Q4)", "size": "~4GB", "speed": "Very Fast", "quality": "Good"},
            "mistral:7b-instruct": {"name": "Mistral 7B Instruct", "size": "~4.1GB", "speed": "Fast", "quality": "Very Good"},
            "llama3.2:3b": {"name": "Llama 3.2 3B", "size": "~2GB", "speed": "Extremely Fast", "quality": "Good"},
            "llama3.1:8b": {"name": "Llama 3.1 8B", "size": "~4.7GB", "speed": "Fast", "quality": "Very Good"},
            "mistral-nemo:12b": {"name": "Mistral Nemo 12B", "size": "~7GB", "speed": "Medium", "quality": "Excellent"},
            "llama3.1:70b-q4_0": {"name": "Llama 3.1 70B (Q4)", "size": "~40GB", "speed": "Slow", "quality": "Excellent"},
            "mistral": {"name": "Mistral (Default)", "size": "~4GB", "speed": "Fast", "quality": "Good"}
        }
        
        for model in available_models:
            info = model_info.get(model, {"name": model, "size": "Unknown", "speed": "Unknown", "quality": "Unknown"})
            models_with_info.append({
                "id": model,
                "name": info["name"],
                "size": info["size"],
                "speed": info["speed"],
                "quality": info["quality"]
            })
        
        # Test connection details
        connection_info = {
            "available": is_available,
            "models": models_with_info,
            "available_model_ids": available_models,
            "default_model": service.default_model,
            "url": service.ollama_url,
            "recommendations": model_recommendations
        }
        
        if not is_available:
            connection_info["help"] = [
                "1. Install Ollama from https://ollama.ai/download",
                "2. Start Ollama: Run 'ollama serve' in terminal",
                "3. Install Mistral: Run 'ollama pull mistral'",
                "4. Verify: Run 'ollama list' to see installed models",
                f"5. Check if Ollama is running at {service.ollama_url}"
            ]
            connection_info["troubleshooting"] = {
                "check_ollama_running": "Run 'ollama list' in terminal - if it works, Ollama is running",
                "check_port": f"Verify port 11434 is not blocked. Try: curl {service.ollama_url}/api/tags",
                "check_firewall": "Ensure firewall allows connections to localhost:11434",
                "alternative_urls": ["http://localhost:11434", "http://127.0.0.1:11434"]
            }
        else:
            connection_info["status"] = "ready"
            if service.default_model not in service.get_available_models():
                connection_info["warning"] = f"Default model '{service.default_model}' not found. Available: {service.get_available_models()}"
                connection_info["help"] = f"Run 'ollama pull {service.default_model}' to install the default model"
        
        return connection_info
    except Exception as e:
        import traceback
        return {
            "available": False,
            "error": str(e),
            "models": [],
            "url": "http://localhost:11434",
            "help": [
                "Install Ollama from https://ollama.ai/download",
                "Run 'ollama serve' to start the service",
                "Run 'ollama pull mistral' to install Mistral model"
            ]
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

