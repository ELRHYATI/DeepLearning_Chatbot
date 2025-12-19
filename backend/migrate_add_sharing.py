"""
Script de migration pour ajouter les champs de partage aux sessions existantes
À exécuter une seule fois pour mettre à jour les bases de données existantes
"""
import sqlite3
import os
from pathlib import Path

def migrate_database(db_path: str = "academic_chatbot.db"):
    """Ajoute les colonnes share_token et is_shared à la table chat_sessions"""
    
    if not os.path.exists(db_path):
        print(f"Base de données {db_path} introuvable. La migration sera effectuée automatiquement au prochain démarrage.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Vérifier si les colonnes existent déjà
        cursor.execute("PRAGMA table_info(chat_sessions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'share_token' in columns and 'is_shared' in columns:
            print("Les colonnes de partage existent déjà. Migration non nécessaire.")
            return
        
        # Ajouter les colonnes
        print("Ajout des colonnes share_token et is_shared...")
        
        if 'share_token' not in columns:
            cursor.execute("ALTER TABLE chat_sessions ADD COLUMN share_token VARCHAR")
            print("[OK] Colonne share_token ajoutee")
        
        if 'is_shared' not in columns:
            cursor.execute("ALTER TABLE chat_sessions ADD COLUMN is_shared BOOLEAN DEFAULT 0")
            print("[OK] Colonne is_shared ajoutee")
        
        # Créer un index unique sur share_token
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_chat_sessions_share_token ON chat_sessions(share_token)")
            print("[OK] Index sur share_token cree")
        except sqlite3.OperationalError as e:
            if "already exists" not in str(e).lower():
                print(f"[WARNING] Erreur lors de la creation de l'index: {e}")
        
        conn.commit()
        print("\n[SUCCESS] Migration terminee avec succes!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Erreur lors de la migration: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    
    db_path = sys.argv[1] if len(sys.argv) > 1 else "academic_chatbot.db"
    
    print(f"Migration de la base de données: {db_path}")
    print("=" * 50)
    
    migrate_database(db_path)

