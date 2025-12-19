"""
Script pour vérifier la configuration OAuth
Utilisez ce script pour diagnostiquer les problèmes de configuration OAuth
"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

print("=" * 60)
print("Vérification de la Configuration OAuth")
print("=" * 60)

# Vérifier si .env existe
env_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(env_path):
    print("\n❌ ERREUR: Le fichier .env n'existe pas!")
    print(f"   Créez le fichier: {env_path}")
    print("   Vous pouvez copier .env.example et le renommer en .env")
    exit(1)
else:
    print(f"\n✅ Fichier .env trouvé: {env_path}")

# Vérifier Google OAuth
print("\n" + "-" * 60)
print("Configuration Google OAuth:")
print("-" * 60)

google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5173/auth/callback/google")

if google_client_id:
    print(f"✅ GOOGLE_CLIENT_ID: {google_client_id[:20]}...")
else:
    print("❌ GOOGLE_CLIENT_ID: NON CONFIGURÉ")
    print("   → Ajoutez GOOGLE_CLIENT_ID dans .env")

if google_client_secret:
    print(f"✅ GOOGLE_CLIENT_SECRET: {google_client_secret[:10]}...")
else:
    print("❌ GOOGLE_CLIENT_SECRET: NON CONFIGURÉ")
    print("   → Ajoutez GOOGLE_CLIENT_SECRET dans .env")

print(f"📍 GOOGLE_REDIRECT_URI: {google_redirect_uri}")

if google_client_id and google_client_secret:
    print("\n✅ Google OAuth est configuré!")
else:
    print("\n❌ Google OAuth n'est PAS configuré")
    print("   Consultez OAUTH_SETUP_GUIDE.md pour les instructions")

# Vérifier GitHub OAuth
print("\n" + "-" * 60)
print("Configuration GitHub OAuth:")
print("-" * 60)

github_client_id = os.getenv("GITHUB_CLIENT_ID", "")
github_client_secret = os.getenv("GITHUB_CLIENT_SECRET", "")
github_redirect_uri = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:5173/auth/callback/github")

if github_client_id:
    print(f"✅ GITHUB_CLIENT_ID: {github_client_id[:20]}...")
else:
    print("❌ GITHUB_CLIENT_ID: NON CONFIGURÉ")
    print("   → Ajoutez GITHUB_CLIENT_ID dans .env (optionnel)")

if github_client_secret:
    print(f"✅ GITHUB_CLIENT_SECRET: {github_client_secret[:10]}...")
else:
    print("❌ GITHUB_CLIENT_SECRET: NON CONFIGURÉ")
    print("   → Ajoutez GITHUB_CLIENT_SECRET dans .env (optionnel)")

print(f"📍 GITHUB_REDIRECT_URI: {github_redirect_uri}")

if github_client_id and github_client_secret:
    print("\n✅ GitHub OAuth est configuré!")
else:
    print("\n⚠️  GitHub OAuth n'est pas configuré (optionnel)")

# Vérifier SECRET_KEY
print("\n" + "-" * 60)
print("Configuration Générale:")
print("-" * 60)

secret_key = os.getenv("SECRET_KEY", "")
if secret_key and secret_key != "your-secret-key-change-in-production":
    print(f"✅ SECRET_KEY: Configuré")
else:
    print("⚠️  SECRET_KEY: Utilise la valeur par défaut (non sécurisé pour production)")
    print("   → Générez une nouvelle clé avec: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")

# Résumé
print("\n" + "=" * 60)
print("Résumé:")
print("=" * 60)

if google_client_id and google_client_secret:
    print("✅ Google OAuth: PRÊT")
else:
    print("❌ Google OAuth: NON CONFIGURÉ")

if github_client_id and github_client_secret:
    print("✅ GitHub OAuth: PRÊT")
else:
    print("⚠️  GitHub OAuth: NON CONFIGURÉ (optionnel)")

print("\n💡 Pour configurer OAuth, consultez:")
print("   - OAUTH_SETUP_GUIDE.md (guide complet)")
print("   - OAUTH_QUICK_START.md (guide rapide)")
print("   - OAUTH_TROUBLESHOOTING.md (dépannage)")

