"""
Configuration Java pour prévenir la création de logs de crash
"""
import os
import platform
import subprocess
from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger()


def configure_java_environment():
    """
    Configure les variables d'environnement Java pour prévenir la création de logs
    Cette fonction doit être appelée AVANT toute initialisation de processus Java
    """
    java_options = []
    
    # Options pour désactiver les logs de crash
    java_options.extend([
        '-XX:-CreateCoredumpOnCrash',  # Désactiver les core dumps
        '-XX:+DisableAttachMechanism',  # Désactiver le mécanisme d'attachement
        '-Xlog:disable',  # Désactiver tous les logs
    ])
    
    # Rediriger les fichiers d'erreur selon l'OS
    if platform.system() == 'Windows':
        error_file = 'NUL'  # Windows null device
        java_options.append('-XX:ErrorFile=NUL')
    else:
        error_file = '/dev/null'  # Unix null device
        java_options.append('-XX:ErrorFile=/dev/null')
    
    # Options supplémentaires pour réduire les logs
    java_options.extend([
        '-XX:+UnlockDiagnosticVMOptions',
        '-XX:LogFile=/dev/null' if platform.system() != 'Windows' else '-XX:LogFile=NUL',
    ])
    
    java_opts_string = ' '.join(java_options)
    
    # Définir les variables d'environnement
    os.environ['_JAVA_OPTIONS'] = java_opts_string
    os.environ['JAVA_TOOL_OPTIONS'] = java_opts_string
    
    # Pour Windows, aussi définir dans le processus actuel
    if platform.system() == 'Windows':
        try:
            # Utiliser subprocess pour définir les variables système (nécessite admin)
            # Sinon, on se contente des variables d'environnement du processus
            pass
        except Exception:
            pass
    
    logger.debug(
        "Java environment configured to prevent crash logs",
        extra_data={"java_options": java_opts_string}
    )
    
    return java_opts_string


def setup_java_log_redirection():
    """
    Configure la redirection des logs Java vers /dev/null ou NUL
    """
    import platform
    
    if platform.system() == 'Windows':
        # Windows: rediriger vers NUL
        null_device = 'NUL'
    else:
        # Unix/Linux/Mac: rediriger vers /dev/null
        null_device = '/dev/null'
    
    # Créer un fichier de configuration Java si possible
    # Note: Cette approche peut ne pas fonctionner pour tous les cas
    # La meilleure solution est d'utiliser les variables d'environnement
    
    return null_device


def clean_java_logs_periodically(directory: str = ".", interval_seconds: int = 300):
    """
    Nettoie périodiquement les logs Java (à utiliser dans un thread séparé)
    
    Args:
        directory: Répertoire à nettoyer
        interval_seconds: Intervalle entre les nettoyages (défaut: 5 minutes)
    """
    import time
    from app.utils.log_cleaner import clean_java_crash_logs
    
    while True:
        try:
            time.sleep(interval_seconds)
            deleted = clean_java_crash_logs(directory)
            if deleted:
                logger.info(
                    f"Periodic cleanup: removed {len(deleted)} Java crash log(s)",
                    extra_data={"event": "periodic_log_cleanup", "files_deleted": len(deleted)}
                )
        except Exception as e:
            logger.error("Error in periodic log cleanup", exc_info=e)
            time.sleep(interval_seconds)  # Continue même en cas d'erreur


def ensure_java_log_prevention():
    """
    S'assure que la prévention des logs Java est activée
    Appeler cette fonction au démarrage de l'application
    """
    # Configurer l'environnement Java
    configure_java_environment()
    
    # Nettoyer les logs existants
    try:
        from app.utils.log_cleaner import clean_java_crash_logs
        import os
        
        # Nettoyer dans le répertoire backend
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        deleted = clean_java_crash_logs(backend_dir)
        
        if deleted:
            logger.info(
                f"Cleaned {len(deleted)} existing Java crash log(s)",
                extra_data={"event": "startup_log_cleanup", "files_deleted": len(deleted)}
            )
    except Exception as e:
        logger.warning("Could not clean existing Java logs", exc_info=e)

