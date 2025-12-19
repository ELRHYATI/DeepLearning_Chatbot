"""
Script pour créer le fichier .env avec les valeurs par défaut
"""
import os
import secrets

env_path = os.path.join(os.path.dirname(__file__), '.env')

if os.path.exists(env_path):
    print(f"⚠️  Le fichier .env existe déjà: {env_path}")
    response = input("Voulez-vous le remplacer? (o/n): ")
    if response.lower() != 'o':
        print("Annulé.")
        exit(0)

# Générer une SECRET_KEY sécurisée
secret_key = secrets.token_urlsafe(32)

env_content = f"""# Secret Key pour JWT (générée automatiquement)
SECRET_KEY={secret_key}

# Google OAuth Configuration
# Obtenez ces valeurs depuis: https://console.cloud.google.com/
# Laissez vide si vous ne voulez pas utiliser Google OAuth pour l'instant
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/callback/google

# GitHub OAuth Configuration
# Obtenez ces valeurs depuis: https://github.com/settings/developers
# Laissez vide si vous ne voulez pas utiliser GitHub OAuth pour l'instant
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_REDIRECT_URI=http://localhost:5173/auth/callback/github

# Ollama Configuration (optionnel)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_TIMEOUT=60
"""

with open(env_path, 'w', encoding='utf-8') as f:
    f.write(env_content)

print(f"✅ Fichier .env créé avec succès: {env_path}")
print("\n📝 Prochaines étapes:")
print("   1. Pour utiliser Google OAuth, ajoutez GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET")
print("   2. Pour utiliser GitHub OAuth, ajoutez GITHUB_CLIENT_ID et GITHUB_CLIENT_SECRET")
print("   3. Consultez OAUTH_SETUP_GUIDE.md pour les instructions détaillées")
print("\n💡 Note: Le login classique (email + mot de passe) fonctionne sans OAuth!")

