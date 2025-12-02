"""Authentication API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.models import User, Organization
from app.auth.schemas import UserCreate, UserLogin, Token, UserResponse
from app.auth.jwt import create_access_token
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user and organization.
    
    Creates a new organization and user account with hashed password.
    Returns a JWT token for immediate authentication.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create organization
    organization = Organization(name=user_data.organization_name)
    db.add(organization)
    db.flush()  # Get organization ID without committing
    
    # Create user with hashed password
    hashed_password = User.hash_password(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        organization_id=organization.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate JWT token
    access_token = create_access_token(
        data={"sub": str(user.id), "org_id": str(user.organization_id)}
    )
    
    return Token(access_token=access_token)


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    
    Validates email and password, returns JWT token on success.
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not user.verify_password(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT token
    access_token = create_access_token(
        data={"sub": str(user.id), "org_id": str(user.organization_id)}
    )
    
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Returns user details for the authenticated user.
    """
    return current_user
