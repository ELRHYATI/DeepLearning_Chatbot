"""
Script rapide pour exécuter la migration de la base de données
Exécutez ce script pour ajouter les colonnes manquantes à votre base de données existante
"""
import sys
import os

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from migrate_add_sharing import migrate_database

if __name__ == "__main__":
    # Chercher la base de données dans le répertoire backend
    db_path = "academic_chatbot.db"
    
    if not os.path.exists(db_path):
        print(f"⚠ Base de données '{db_path}' introuvable dans le répertoire backend.")
        print("La base de données sera créée automatiquement au prochain démarrage du serveur.")
    else:
        print(f"🔄 Migration de la base de données: {db_path}")
        print("=" * 50)
        migrate_database(db_path)
        print("\n✅ Migration terminée! Vous pouvez maintenant redémarrer le serveur.")

