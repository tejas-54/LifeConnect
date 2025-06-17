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
from pydantic import BaseModel, EmailStr, Field # Added Field
import asyncio
from bson import ObjectId
import motor.motor_asyncio
from passlib.context import CryptContext # For password hashing
from datetime import datetime # Ensure datetime is imported for User model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Main application (will be mounted under /api)
main_app = FastAPI(
    title="LifeConnect Backend API",
    description="Comprehensive backend for organ donation platform",
    version="1.0.0",
    docs_url="/docs", # Docs will be at /api/docs
    redoc_url="/redoc" # Redoc will be at /api/redoc
)

# Root application - this is what uvicorn will run
app = FastAPI(
    title="LifeConnect Root API",
    description="Root application, main API is mounted under /api"
)

# CORS middleware (applied to main_app, which will be under /api)
main_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
# Import AI router
from backend.routes.ai_routes import router as ai_router
# Import Auth router
from backend.routes.auth_routes import router as auth_router
# Import Blockchain router
from backend.routes.blockchain_routes import router as blockchain_router
# Import Dashboard router
from backend.routes.dashboard_routes import router as dashboard_router
# Import Health Card router
from backend.routes.health_card_routes import router as health_card_router
# Import Logistics router
from backend.routes.logistics_routes import router as logistics_router
# Import Donor router
from backend.routes.donor_routes import router as donor_router

# Include AI router
main_app.include_router(ai_router)
# Include Auth router
main_app.include_router(auth_router)
# Include Blockchain router
main_app.include_router(blockchain_router)
# Include Dashboard router
main_app.include_router(dashboard_router)
# Include Health Card router
main_app.include_router(health_card_router)
# Include Logistics router
main_app.include_router(logistics_router)
# Include Donor router
main_app.include_router(donor_router)

# Mount the main_app under /api in the root app
app.mount("/api", main_app)

# --- MongoDB Setup ---
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017/lifeconnect")
client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URL)
db = client.lifeconnect # Database instance, can be imported by other modules

# --- Password Hashing Setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- Base MongoDB Model ---
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _: Any): # field_schema changed to _
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema: Any): # core_schema changed to field_schema
        field_schema.update(type="string")

class MongoModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    class Config:
        populate_by_name = True # allow_population_by_field_name changed
        json_encoders = {ObjectId: str}

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

# In-memory storage has been removed. Data will be handled by MongoDB collections.


class User(MongoModel): # Inherits from MongoModel
    email: EmailStr = Field(unique=True)
    hashed_password: str
    name: str
    role: str
    wallet_address: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

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

# --- New Pydantic Models for MongoDB Collections ---

class Donor(MongoModel):
    user_email: EmailStr # Link to the User model
    name: str
    age: int
    blood_type: str
    organ_types: List[str]
    health_card_cid: Optional[str] = None # IPFS CID for detailed health card
    access_rules: Optional[str] = None # Rules for data access/sharing
    emergency_contact: Optional[str] = None
    wallet_address: str # Blockchain wallet address
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    # Additional fields as needed
    availability_status: str = "available" # e.g., available, in_process, matched

class Recipient(MongoModel):
    user_email: EmailStr # Link to the User model
    name: str
    age: int
    blood_type: str
    required_organ_type: str
    urgency_score: int # Clinical urgency score
    health_card_cid: Optional[str] = None # IPFS CID for detailed health card
    wallet_address: str # Blockchain wallet address
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    # Additional fields
    match_status: str = "pending" # e.g., pending, matched, transplant_completed

class Organ(MongoModel):
    donor_user_email: EmailStr # Link to the Donor (User)
    donor_wallet_address: str # Denormalized for easier query, or use donor_id (PyObjectId)
    organ_type: str
    blood_type: str # Denormalized from donor for filtering
    expiry_hours: Optional[int] = None # Estimated hours organ remains viable
    viability_score: Optional[str] = None # Could be simple (Good, Fair) or complex score
    location: Optional[str] = None # Current location of the organ (e.g., hospital name or coordinates)
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "available" # e.g., available, reserved, in_transit, transplanted, expired
    transport_id: Optional[PyObjectId] = None # Link to Transport record if in transit

class HealthRecord(MongoModel): # For storing IPFS CIDs of detailed health records
    user_email: EmailStr # Link to the User whose health record this is
    record_cid: str # IPFS CID of the detailed health record document
    record_type: str = "general" # e.g., general, pre_transplant_evaluation, post_op
    summary: Optional[str] = None # Brief summary or title of the record
    created_by_user_email: Optional[EmailStr] = None # Who uploaded/created this record link
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    access_list: List[EmailStr] = [] # List of user_emails who can access this

class Transport(MongoModel):
    organ_id: PyObjectId # Link to the Organ being transported
    transport_request_id: Optional[str] = None # External ID from logistics engine if any
    status: str = "pending" # e.g., pending, scheduled, in_transit, delivered, delayed, failed
    current_location: Optional[Dict[str, Any]] = None # e.g., {"lat": 12.34, "lon": 56.78, "timestamp": ...}
    estimated_arrival: Optional[datetime] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    logistics_plan_cid: Optional[str] = None # IPFS CID of the detailed logistics/route plan
    vehicle_id: Optional[str] = None
    notes: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class LifeTokenEvent(MongoModel):
    user_email: EmailStr # User receiving or spending tokens
    event_type: str # e.g., "registration_bonus", "health_checkup_redemption", "organ_donation_pledge"
    token_amount: float # Positive for earning, negative for spending
    transaction_date: datetime = Field(default_factory=datetime.utcnow)
    related_entity_id: Optional[PyObjectId] = None # e.g., organ_id, health_record_id
    notes: Optional[str] = None

# --- MongoDB Collection References (optional here, can be used directly as db.collection_name in routes) ---
# These are more for documentation or if you want to pass collection objects around.
# For direct use in routes, `db.users`, `db.donors` etc. is common with Motor.
user_collection = db.users # Already used in auth_routes
donor_collection = db.donors
recipient_collection = db.recipients
organ_collection = db.organs
health_record_collection = db.health_records
transport_collection = db.transports
life_token_event_collection = db.life_token_events


# Utility functions
# Old hash_password and verify_password (SHA256 based) are removed.
# New ones (get_password_hash, verify_password using bcrypt) are defined above.

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

# Root endpoint for the main_app (now at /api/)
@main_app.get("/")
async def main_app_root():
    return {
        "message": "LifeConnect Backend API (Mounted at /api)",
        "version": "1.0.0",
        "status": "operational",
        "docs_at": "/api/docs",
        "redoc_at": "/api/redoc",
        "timestamp": datetime.utcnow().isoformat()
    }

# Health check for main_app (now at /api/health)
# Note: The original @app.get("/api/health") implies it was not meant to be under /api prefix twice.
# If it was meant to be /api/health, then it should be on main_app and will be served at /api/health
# If it was meant to be /health at the root, it should be on `app`.
# Given its name and previous path, it seems like a health check for the API itself.
@main_app.get("/health") # Will be served at /api/health
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

# Authentication endpoints have been moved to backend.routes.auth_routes
# The old @app.post("/api/auth/register") and @app.post("/api/auth/login") are now removed.
