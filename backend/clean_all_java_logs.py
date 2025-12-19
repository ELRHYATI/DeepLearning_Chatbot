"""
Script pour nettoyer tous les logs Java existants
À exécuter manuellement pour nettoyer les logs accumulés
"""
import os
import sys
from pathlib import Path
from app.utils.log_cleaner import clean_java_crash_logs, clean_all_logs

def main():
    # Obtenir le répertoire backend
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(backend_dir)
    
    print(f"Nettoyage des logs Java")
    print("=" * 60)
    print(f"Repertoire backend: {backend_dir}")
    print(f"Repertoire parent: {parent_dir}")
    print("=" * 60)
    
    # Nettoyer les logs Java dans backend
    deleted_java_backend = clean_java_crash_logs(backend_dir)
    
    # Nettoyer les logs Java dans le répertoire parent aussi
    deleted_java_parent = clean_java_crash_logs(parent_dir)
    
    # Combiner les résultats
    deleted_java = deleted_java_backend + deleted_java_parent
    
    # Nettoyer tous les autres logs aussi
    deleted_all_backend = clean_all_logs(backend_dir)
    deleted_all_parent = clean_all_logs(parent_dir)
    deleted_all = deleted_all_backend + deleted_all_parent
    
    # Compter les fichiers supprimés
    total_deleted = len(deleted_java) + len([f for f in deleted_all if f not in deleted_java])
    
    if total_deleted > 0:
        print(f"\n[OK] {total_deleted} fichier(s) de log supprime(s):")
        for file in deleted_java:
            print(f"  - {file}")
        for file in deleted_all:
            if file not in deleted_java:
                print(f"  - {file}")
    else:
        print("\n[OK] Aucun fichier de log trouve a nettoyer.")
    
    print("\n" + "=" * 60)
    print("Nettoyage termine!")

if __name__ == "__main__":
    main()

