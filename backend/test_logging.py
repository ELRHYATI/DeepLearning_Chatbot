"""
Script de test pour le système de logging structuré
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.logger import get_logger
import time

def test_logging():
    """Test du système de logging"""
    print("Test du système de logging structuré...")
    
    logger = get_logger()
    
    # Test 1: Log simple
    print("\n1. Test log simple")
    logger.info("Test de log simple")
    
    # Test 2: Log avec données supplémentaires
    print("\n2. Test log avec extra_data")
    logger.info(
        "Test avec données supplémentaires",
        extra_data={
            "event": "test",
            "user_id": 123,
            "action": "test_logging"
        }
    )
    
    # Test 3: Log de requête API
    print("\n3. Test log de requête API")
    logger.log_request(
        method="GET",
        path="/api/test",
        status_code=200,
        duration_ms=45.67,
        user_id=123,
        client_ip="127.0.0.1"
    )
    
    # Test 4: Log de performance de modèle
    print("\n4. Test log de performance de modèle")
    logger.log_model_performance(
        model_name="TestModel",
        operation="test_operation",
        duration_ms=123.45,
        input_size=100,
        output_size=50
    )
    
    # Test 5: Log d'opération de base de données
    print("\n5. Test log d'opération DB")
    logger.log_database_operation(
        operation="SELECT",
        table="users",
        duration_ms=12.34,
        rows_affected=10
    )
    
    # Test 6: Log d'erreur
    print("\n6. Test log d'erreur")
    try:
        raise ValueError("Test d'erreur")
    except Exception as e:
        logger.log_error_with_context(
            error=e,
            context={"test": True}
        )
    
    # Test 7: Test avec décorateur
    print("\n7. Test avec décorateur de performance")
    from app.utils.logger import performance_tracker
    
    @performance_tracker(operation_name="test_function")
    def test_function():
        time.sleep(0.1)
        return "result"
    
    result = test_function()
    print(f"Résultat: {result}")
    
    print("\n✅ Tous les tests sont terminés!")
    print("Vérifiez le répertoire 'logs/' pour voir les fichiers de logs JSON")

if __name__ == "__main__":
    test_logging()

