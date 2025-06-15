import os
import sys
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import uvicorn
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
import json
import hashlib
import jwt
from pydantic import BaseModel, EmailStr
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LifeConnect Backend API",
    description="Comprehensive backend for organ donation platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# External service URLs
AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://localhost:8000")
LOGISTICS_ENGINE_URL = os.getenv("LOGISTICS_ENGINE_URL", "http://localhost:8001")
BLOCKCHAIN_RPC_URL = os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
IPFS_API_URL = os.getenv("IPFS_API_URL", "http://127.0.0.1:5001")

# In-memory storage (replace with database in production)
users_db = {}
donors_db = {}
recipients_db = {}
organs_db = {}
tokens_db = {}
transport_db = {}

# Pydantic models
class User(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str
    wallet_address: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class DonorRegistration(BaseModel):
    name: str
    age: int
    blood_type: str
    organ_types: List[str]
    health_card_cid: str
    access_rules: str
    emergency_contact: str
    wallet_address: str

class RecipientRegistration(BaseModel):
    name: str
    age: int
    blood_type: str
    required_organ_type: str
    urgency_score: int
    health_card_cid: str
    wallet_address: str

class OrganRegistration(BaseModel):
    donor_address: str
    organ_type: str
    blood_type: str
    expiry_hours: int
    viability_score: str
    location: str

class MatchRequest(BaseModel):
    recipient_address: str
    organ_types: Optional[List[str]] = None

class TokenRedemption(BaseModel):
    address: str
    amount: float
    reward_type: str

# Utility functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def call_external_service(url: str, method: str = "GET", data: dict = None):
    """Helper function to call external services"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.request(method, url, json=data, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"External service error: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"External service call failed: {e}")
        return None

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "LifeConnect Backend API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "timestamp": datetime.utcnow().isoformat()
    }

# Health check
@app.get("/api/health")
async def health_check():
    # Check external services
    ai_status = await call_external_service(f"{AI_ENGINE_URL}/health")
    logistics_status = await call_external_service(f"{LOGISTICS_ENGINE_URL}/health")
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "operational",
            "ai_engine": "connected" if ai_status else "disconnected",
            "logistics_engine": "connected" if logistics_status else "disconnected",
            "database": "operational"
        }
    }

# Authentication endpoints
@app.post("/api/auth/register")
async def register_user(user: User):
    """Register a new user"""
    try:
        if user.email in users_db:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        hashed_password = hash_password(user.password)
        
        # Store user
        users_db[user.email] = {
            "email": user.email,
            "password": hashed_password,
            "name": user.name,
            "role": user.role,
            "wallet_address": user.wallet_address,
            "phone": user.phone,
            "address": user.address,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        # Create access token
        access_token = create_access_token(data={"sub": user.email})
        
        logger.info(f"User registered: {user.email}")
        
        return {
            "message": "User registered successfully",
            "user": {
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "wallet_address": user.wallet_address
            },
            "token": access_token
        }
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/api/auth/login")
async def login_user(user_login: UserLogin):
    """Login user"""
    try:
        if user_login.email not in users_db:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user = users_db[user_login.email]
        
        if not verify_password(user_login.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user["is_active"]:
            raise HTTPException(status_code=401, detail="Account deactivated")
