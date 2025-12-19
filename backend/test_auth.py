"""
Script pour tester l'authentification
Teste l'inscription, la connexion et la validation des tokens
"""
import httpx
import json

BASE_URL = "http://localhost:8000/api/auth"

def test_register():
    """Test de l'inscription"""
    print("\n" + "="*60)
    print("TEST 1: Inscription")
    print("="*60)
    
    # Données de test
    test_user = {
        "username": "test_user_" + str(hash("test") % 10000),
        "email": f"test_{hash('test') % 10000}@example.com",
        "password": "testpassword123"
    }
    
    try:
        with httpx.Client() as client:
            response = client.post(f"{BASE_URL}/register", json=test_user)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Inscription réussie!")
            print(f"   User ID: {data.get('id')}")
            print(f"   Username: {data.get('username')}")
            print(f"   Email: {data.get('email')}")
            return test_user, data
        else:
            error = response.json()
            print(f"❌ Erreur d'inscription: {error.get('detail', 'Erreur inconnue')}")
            if "déjà" in error.get('detail', ''):
                print("   → L'utilisateur existe déjà, on va tester la connexion")
                return test_user, None
            return None, None
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Le backend n'est pas démarré!")
        print("   → Démarrez le backend avec: python -m uvicorn app.main:app --reload")
        return None, None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None, None

def test_login(user_data):
    """Test de la connexion"""
    print("\n" + "="*60)
    print("TEST 2: Connexion")
    print("="*60)
    
    if not user_data:
        print("⚠️  Pas de données utilisateur, test avec des credentials par défaut")
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
    
    try:
        with httpx.Client() as client:
            response = client.post(f"{BASE_URL}/login", json=user_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Connexion réussie!")
            print(f"   Token type: {data.get('token_type')}")
            print(f"   Token: {data.get('access_token')[:50]}...")
            print(f"   User: {data.get('user', {}).get('username')}")
            return data.get('access_token')
        else:
            error = response.json()
            print(f"❌ Erreur de connexion: {error.get('detail', 'Erreur inconnue')}")
            return None
    except (httpx.ConnectError, httpx.NetworkError):
        print("❌ Erreur: Le backend n'est pas démarré!")
        return None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def test_me(token):
    """Test de récupération des infos utilisateur"""
    print("\n" + "="*60)
    print("TEST 3: Récupération des infos utilisateur (avec token)")
    print("="*60)
    
    if not token:
        print("⚠️  Pas de token, test impossible")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        with httpx.Client() as client:
            response = client.get(f"{BASE_URL}/me", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Récupération réussie!")
            print(f"   User ID: {data.get('id')}")
            print(f"   Username: {data.get('username')}")
            print(f"   Email: {data.get('email')}")
        else:
            error = response.json()
            print(f"❌ Erreur: {error.get('detail', 'Erreur inconnue')}")
    except (httpx.ConnectError, httpx.NetworkError):
        print("❌ Erreur: Le backend n'est pas démarré!")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_google_oauth():
    """Test de l'URL Google OAuth"""
    print("\n" + "="*60)
    print("TEST 4: Google OAuth (URL)")
    print("="*60)
    
    try:
        with httpx.Client() as client:
            response = client.get(f"{BASE_URL}/google/url")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ URL Google OAuth générée!")
            print(f"   URL: {data.get('auth_url')[:80]}...")
        else:
            error = response.json()
            print(f"⚠️  Google OAuth non configuré: {error.get('detail', 'Erreur inconnue')}")
            print("   → C'est normal si vous n'avez pas configuré GOOGLE_CLIENT_ID")
    except (httpx.ConnectError, httpx.NetworkError):
        print("❌ Erreur: Le backend n'est pas démarré!")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_github_oauth():
    """Test de l'URL GitHub OAuth"""
    print("\n" + "="*60)
    print("TEST 5: GitHub OAuth (URL)")
    print("="*60)
    
    try:
        with httpx.Client() as client:
            response = client.get(f"{BASE_URL}/github/url")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ URL GitHub OAuth générée!")
            print(f"   URL: {data.get('auth_url')[:80]}...")
        else:
            error = response.json()
            print(f"⚠️  GitHub OAuth non configuré: {error.get('detail', 'Erreur inconnue')}")
            print("   → C'est normal si vous n'avez pas configuré GITHUB_CLIENT_ID")
    except (httpx.ConnectError, httpx.NetworkError):
        print("❌ Erreur: Le backend n'est pas démarré!")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    print("\n" + "="*60)
    print("🧪 TESTS D'AUTHENTIFICATION")
    print("="*60)
    print("\n⚠️  Assurez-vous que le backend est démarré sur http://localhost:8000")
    print("   Commande: python -m uvicorn app.main:app --reload\n")
    
    input("Appuyez sur Entrée pour commencer les tests...")
    
    # Test 1: Inscription
    user_data, user_info = test_register()
    
    # Test 2: Connexion
    token = test_login(user_data)
    
    # Test 3: Récupération des infos
    test_me(token)
    
    # Test 4: Google OAuth
    test_google_oauth()
    
    # Test 5: GitHub OAuth
    test_github_oauth()
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*60)
    if token:
        print("✅ Authentification classique: FONCTIONNE")
    else:
        print("❌ Authentification classique: ÉCHEC")
    
    print("\n💡 Prochaines étapes:")
    print("   1. Testez dans le frontend: http://localhost:5173/login")
    print("   2. Créez un compte avec email + mot de passe")
    print("   3. Connectez-vous et testez les fonctionnalités")
    print("   4. (Optionnel) Configurez OAuth pour Google/GitHub")

if __name__ == "__main__":
    main()

