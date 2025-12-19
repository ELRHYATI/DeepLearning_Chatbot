from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, Token, GoogleToken
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import httpx
from app.utils.error_handler import AppException, ErrorCode
from app.utils.logger import get_logger

logger = get_logger()

router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Google OAuth settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5173/auth/callback/google")

# GitHub OAuth settings
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:5173/auth/callback/github")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    try:
        logger.info("Registration attempt", extra_data={"email": user_data.email})
        
        # Check if user exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise AppException(
                error_code=ErrorCode.BAD_REQUEST,
                status_code=400,
                detail="Cet email est déjà enregistré."
            )
        
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise AppException(
                error_code=ErrorCode.BAD_REQUEST,
                status_code=400,
                detail="Ce nom d'utilisateur est déjà pris."
            )
        
        # Create user
        try:
            hashed_password = get_password_hash(user_data.password)
        except Exception as hash_error:
            logger.error("Password hashing error", exc_info=hash_error)
            raise AppException(
                error_code=ErrorCode.INTERNAL_ERROR,
                status_code=500,
                detail="Erreur lors du hachage du mot de passe."
            )
        
        try:
            user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("User created successfully", extra_data={"user_id": user.id})
        except Exception as db_error:
            db.rollback()
            logger.error("Database error during registration", exc_info=db_error)
            raise AppException(
                error_code=ErrorCode.DATABASE_ERROR,
                status_code=500,
                detail="Erreur lors de la création de l'utilisateur en base de données."
            )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at
        )
    except AppException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Registration error", exc_info=e)
        raise AppException(
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=500,
            detail="Erreur lors de l'inscription. Veuillez réessayer."
        )

@router.post("/login", response_model=Token)
async def login(user_data: UserCreate, db: Session = Depends(get_db)):
    """Login and get access token."""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise AppException(
            error_code=ErrorCode.INVALID_CREDENTIALS,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect."
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    logger.info("User logged in", extra_data={"user_id": user.id, "email": user.email})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at
        )
    )

@router.get("/google/url")
async def get_google_auth_url():
    """Get Google OAuth authorization URL."""
    if not GOOGLE_CLIENT_ID or GOOGLE_CLIENT_ID == "":
        logger.warning("Google OAuth not configured: GOOGLE_CLIENT_ID is missing")
        raise AppException(
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            status_code=500,
            detail="L'authentification Google n'est pas configurée. Veuillez configurer GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET dans le fichier .env"
        )
    
    from urllib.parse import urlencode
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return {"auth_url": auth_url}

@router.post("/google/callback", response_model=Token)
async def google_callback(request: GoogleToken, db: Session = Depends(get_db)):
    code = request.token
    """Handle Google OAuth callback."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise AppException(
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            status_code=500,
            detail="L'authentification Google n'est pas configurée."
        )
    
    try:
        # Exchange code for token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code"
                }
            )
            token_data = token_response.json()
            
            if "access_token" not in token_data:
                raise AppException(
                    error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
                    status_code=400,
                    detail="Impossible d'obtenir le token d'accès depuis Google."
                )
            
            # Get user info from Google
            user_info_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            user_info = user_info_response.json()
            
            email = user_info.get("email")
            name = user_info.get("name", email.split("@")[0]) if email else "user"
            
            if not email:
                raise AppException(
                    error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
                    status_code=400,
                    detail="Aucun email reçu depuis Google."
                )
            
            # Find or create user
            user = db.query(User).filter(User.email == email).first()
            if not user:
                # Create new user
                user = User(
                    username=name,
                    email=email,
                    hashed_password=""  # No password for OAuth users
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info("User created via Google OAuth", extra_data={"user_id": user.id})
            
            # Create JWT token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.email}, expires_delta=access_token_expires
            )
            
            return Token(
                access_token=access_token,
                token_type="bearer",
                user=UserResponse(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    created_at=user.created_at
                )
            )
    except AppException:
        raise
    except Exception as e:
        logger.error("OAuth error", exc_info=e)
        raise AppException(
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            status_code=400,
            detail="Erreur lors de l'authentification Google. Veuillez réessayer."
        )

@router.get("/github/url")
async def get_github_auth_url():
    """Get GitHub OAuth authorization URL."""
    if not GITHUB_CLIENT_ID or GITHUB_CLIENT_ID == "":
        logger.warning("GitHub OAuth not configured: GITHUB_CLIENT_ID is missing")
        raise AppException(
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            status_code=500,
            detail="L'authentification GitHub n'est pas configurée. Veuillez configurer GITHUB_CLIENT_ID et GITHUB_CLIENT_SECRET dans le fichier .env"
        )
    
    from urllib.parse import urlencode
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": "user:email",
        "state": "github_oauth_state"  # In production, use a random state for security
    }
    auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    return {"auth_url": auth_url}

@router.post("/github/callback", response_model=Token)
async def github_callback(request: GoogleToken, db: Session = Depends(get_db)):
    code = request.token
    """Handle GitHub OAuth callback."""
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise AppException(
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            status_code=500,
            detail="L'authentification GitHub n'est pas configurée."
        )
    
    try:
        # Exchange code for token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": GITHUB_REDIRECT_URI
                },
                headers={"Accept": "application/json"}
            )
            token_data = token_response.json()
            
            if "access_token" not in token_data:
                raise AppException(
                    error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
                    status_code=400,
                    detail="Impossible d'obtenir le token d'accès depuis GitHub."
                )
            
            access_token = token_data["access_token"]
            
            # Get user info from GitHub
            user_info_response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {access_token}"}
            )
            user_info = user_info_response.json()
            
            # Get user email (may need to fetch from emails endpoint)
            email = user_info.get("email")
            if not email:
                # Try to get email from emails endpoint
                emails_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"token {access_token}"}
                )
                emails = emails_response.json()
                if emails and len(emails) > 0:
                    # Get primary email or first email
                    primary_email = next((e for e in emails if e.get("primary")), emails[0])
                    email = primary_email.get("email")
            
            username = user_info.get("login", user_info.get("name", "user"))
            name = user_info.get("name", username)
            
            if not email:
                raise AppException(
                    error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
                    status_code=400,
                    detail="Aucun email reçu depuis GitHub. Veuillez vérifier que votre email GitHub est public ou autoriser l'accès à l'email."
                )
            
            # Find or create user
            user = db.query(User).filter(User.email == email).first()
            if not user:
                # Check if username is taken, if so append number
                base_username = username
                counter = 1
                while db.query(User).filter(User.username == username).first():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Create new user
                user = User(
                    username=username,
                    email=email,
                    hashed_password=""  # No password for OAuth users
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info("User created via GitHub OAuth", extra_data={"user_id": user.id})
            
            # Create JWT token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            jwt_token = create_access_token(
                data={"sub": user.email}, expires_delta=access_token_expires
            )
            
            return Token(
                access_token=jwt_token,
                token_type="bearer",
                user=UserResponse(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    created_at=user.created_at
                )
            )
    except AppException:
        raise
    except Exception as e:
        logger.error("GitHub OAuth error", exc_info=e)
        raise AppException(
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            status_code=400,
            detail="Erreur lors de l'authentification GitHub. Veuillez réessayer."
        )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    Used as a dependency in other routers.
    
    Returns:
        User: The authenticated user object
        
    Raises:
        AppException: If token is invalid or user not found
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise AppException(
                error_code=ErrorCode.TOKEN_INVALID,
                status_code=401,
                detail="Token d'authentification invalide."
            )
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise AppException(
                error_code=ErrorCode.NOT_FOUND,
                status_code=404,
                detail="Utilisateur introuvable."
            )
        
        return user
    except JWTError:
        raise AppException(
            error_code=ErrorCode.TOKEN_INVALID,
            status_code=401,
            detail="Token d'authentification invalide ou expiré."
        )


# Optional authentication for endpoints that can work without auth
security_optional = HTTPBearer(auto_error=False)

def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current authenticated user from JWT token, or return None if not authenticated.
    Used for endpoints that can work with or without authentication.
    
    Returns:
        User: The authenticated user object, or None if not authenticated
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return None
        
        user = db.query(User).filter(User.email == email).first()
        return user
    except (JWTError, Exception):
        return None

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at
    )
