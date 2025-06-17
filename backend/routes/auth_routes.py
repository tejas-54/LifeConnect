from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel as PydanticBaseModel, EmailStr # Renamed BaseModel to avoid conflict
from datetime import datetime
from typing import Optional # Added Optional

# Import from backend.app (MongoDB instance, Pydantic User model, new password utils)
from backend.app import (
    db,  # MongoDB database instance
    User,
    UserLogin,
    get_password_hash, # New password hashing
    verify_password,   # New password verification
    create_access_token,
    logger
    # users_db import is removed
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

class TokenData(PydanticBaseModel): # Using PydanticBaseModel
    access_token: str
    token_type: str = "bearer"

# Pydantic model for User Profile response (omits hashed_password)
class UserProfile(PydanticBaseModel):
    # id: Optional[str] = None # PyObjectId will be stringified by MongoModel's json_encoders
    # Replicating fields from User model in app.py, excluding hashed_password
    # And ensuring 'id' is correctly handled if it comes from MongoModel's _id
    id: Optional[Any] = None # Using Any to be flexible with PyObjectId stringification from model
    email: EmailStr
    name: str
    role: str
    wallet_address: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime
    is_active: bool

    class Config:
        # orm_mode = True # Pydantic v1
        from_attributes = True # Pydantic v2

# Pydantic model for user creation (receives plain password)
class UserCreate(PydanticBaseModel): # Using PydanticBaseModel
    email: EmailStr
    password: str
    name: str
    role: str
    wallet_address: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

@router.post("/register", response_model=TokenData)
async def register_user(user_create_data: UserCreate): # Changed parameter type
    """
    Register a new user.
    """
    try:
        existing_user = await db.users.find_one({"email": user_create_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        hashed_pass = get_password_hash(user_create_data.password)

        # Create User model instance (which includes default created_at, is_active)
        # Exclude 'password' from user_create_data when creating User Pydantic model
        user_doc_data = user_create_data.model_dump(exclude={"password"})
        user_doc = User(**user_doc_data, hashed_password=hashed_pass)

        # Insert into MongoDB
        # Pydantic v2's model_dump replaces dict() and json()
        await db.users.insert_one(user_doc.model_dump(by_alias=True, exclude=["id"]))

        access_token = create_access_token(data={"sub": user_create_data.email})
        logger.info(f"User registered: {user_create_data.email}")

        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error for {user_create_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=TokenData)
async def login_user(form_data: UserLogin):
    """
    Login user and return access token.
    """
    try:
        user_in_db_doc = await db.users.find_one({"email": form_data.email})

        if not user_in_db_doc or not verify_password(form_data.password, user_in_db_doc["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Convert document to User Pydantic model to use its fields (like is_active)
        user_obj = User(**user_in_db_doc)

        if not user_obj.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account deactivated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(data={"sub": form_data.email})
        logger.info(f"User logged in: {form_data.email}")

        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {form_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/profile", response_model=UserProfile)
async def get_current_user_profile(current_user_email: str = Depends(verify_token)):
    """
    Get current authenticated user's profile.
    """
    user_doc = await db.users.find_one({"email": current_user_email})
    if not user_doc:
        # This should ideally not happen if verify_token works correctly
        # and the token subject (email) always corresponds to an existing user.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # The User model in app.py uses MongoModel which handles _id -> id stringification.
    # We can directly pass the user_doc to UserProfile if fields match.
    # UserProfile is a subset of User model fields.
    return UserProfile(**user_doc)
