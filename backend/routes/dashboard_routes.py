from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import json

from fastapi import Request # Added for try_verify_token

# Assuming these are in backend.app or a shared utility module
from backend.app import (
    db,   # MongoDB instance
    User, # User Pydantic Model
    verify_token,
    logger,
    # users_db is removed
    # For try_verify_token to work like verify_token, it would need:
    # SECRET_KEY, ALGORITHM, jwt module, HTTPBearer, HTTPAuthorizationCredentials
    # but as a placeholder, it's simplified.
)
# Database models are commented out as per plan.
# Direct db access will be replaced by service calls or removed/simulated.
# from models import db, User, OrganMatch, ActivityLog, HealthCard, TransportPlan
# from utils import log_activity, create_response, update_metric # Flask specific

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# --- Pydantic Models for Responses ---
class SystemHealthComponent(BaseModel):
    database: bool
    blockchain: bool
    ipfs: bool
    ai_engine: bool
    logistics: bool

class SystemHealthResponse(BaseModel):
    status: str
    health_percentage: float
    components: SystemHealthComponent
    last_check: datetime
    uptime_hours: int # Assuming this remains a placeholder or configured value
    version: str # Assuming this is a static version string

class DemoEndpointInfo(BaseModel):
    url: str
    method: str
    data: Optional[Dict[str, Any]] = None
    requires_auth: Optional[bool] = None

class DemoAccountInfo(BaseModel):
    index: int
    address: str
    name: str

class DemoResponse(BaseModel):
    message: str
    sample_endpoints: Dict[str, str]
    sample_wallet_login: DemoEndpointInfo
    available_accounts: List[DemoAccountInfo]
    sample_health_card: DemoEndpointInfo

# --- Route Implementations ---

@router.get("/system-health", response_model=SystemHealthResponse)
async def get_system_health():
    """Get comprehensive system health status - PUBLIC"""
    try:
        # Test component health (these would be real checks in production)
        health_status_components = {
            'database': True,  # If we reach here, database is working (simulated)
            'blockchain': True,  # Would test actual blockchain connection
            'ipfs': True,       # Would test IPFS connectivity
            'ai_engine': True,  # Would test AI engine
            'logistics': True   # Would test logistics engine
        }

        healthy_components_count = sum(health_status_components.values())
        total_components_count = len(health_status_components)
        health_percentage = (healthy_components_count / total_components_count) * 100

        overall_status: str
        if health_percentage >= 90:
            overall_status = 'healthy'
        elif health_percentage >= 70:
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'

        # update_metric('system_health_percentage', health_percentage) # Flask specific util, comment out
        logger.info(f"System health check: {overall_status}, {health_percentage}%")

        return SystemHealthResponse(
            status=overall_status,
            health_percentage=health_percentage,
            components=SystemHealthComponent(**health_status_components),
            last_check=datetime.now(timezone.utc),
            uptime_hours=24,  # Placeholder
            version='1.0.0'   # Placeholder
        )

    except Exception as e:
        logger.error(f"Error in get_system_health: {str(e)}")
        # For a public health check, we might want to return a structured error
        # instead of a generic 500 that hides component status.
        # However, following original structure of single error response:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system health: {str(e)}"
        )

@router.get("/demo", response_model=DemoResponse)
async def get_demo_data():
    """Get demo data for testing - PUBLIC"""
    return DemoResponse(
        message='LifeConnect Backend Demo Data (FastAPI Version)',
        sample_endpoints={
            'health_check': '/api/health', # Assuming /api prefix is from app.py main, not router
            'system_health': '/dashboard/system-health', # Corrected to be relative to this router's prefix
            'dashboard_stats': '/dashboard/stats',
            'wallet_login': '/auth/wallet-login', # Assuming auth router uses /auth
            'test_login': '/auth/test-login',     # Assuming auth router uses /auth
            'blockchain_info': '/blockchain/network-info' # Assuming blockchain router
        },
        sample_wallet_login=DemoEndpointInfo(
            url='/auth/wallet-login', # Corrected
            method='POST',
            data={'account_index': 0, 'user_type': 'donor'}
        ),
        available_accounts=[
            DemoAccountInfo(index=0, address='0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266', name='Account #0'),
            DemoAccountInfo(index=1, address='0x70997970C51812dc3A010C7d01b50e0d17dc79C8', name='Account #1'),
            DemoAccountInfo(index=2, address='0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC', name='Account #2'),
            DemoAccountInfo(index=3, address='0x90F79bf6EB2c4f870365E785982E1f101E93b906', name='Account #3')
        ],
        sample_health_card=DemoEndpointInfo(
            url='/health-cards/generate', # Assuming health-cards router prefix
            method='POST',
            requires_auth=True,
            data={'name': 'John Doe', 'age': 30, 'bloodType': 'O+', 'donorStatus': True, 'organTypes': ['heart', 'liver']}
        )
    )

# --- Pydantic Models for Recent Activity ---
class ActivityMetaData(BaseModel):
    # Define fields if structure is known, otherwise Dict[str, Any]
    pass

class ActivityItem(BaseModel):
    id: int # Assuming ActivityLog had an id
    action: str
    description: Optional[str] = None
    timestamp: datetime
    user_id: Optional[int] = None # Or str, depending on what get_jwt_identity provided
    severity: Optional[str] = None
    ip_address: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None # Changed from ActivityMetaData for simplicity

class RecentActivityFilters(BaseModel):
    severity: Optional[str] = None
    action: Optional[str] = None
    limit: int

class RecentActivityResponse(BaseModel):
    activities: List[ActivityItem]
    total_count: int
    filters_applied: RecentActivityFilters

# --- Route Implementation for Recent Activity ---
@router.get("/recent-activity", response_model=RecentActivityResponse)
async def get_recent_activity(
    limit: int = Query(50, ge=1, le=100, description="Max 100 activities"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    action: Optional[str] = Query(None, description="Filter by action type (partial match)"),
    current_user_email: str = Depends(verify_token) # `verify_token` returns email
):
    """Get recent system activity with filtering - PROTECTED"""
    try:
        # In a real app, we'd fetch user details based on current_user_email
        # For now, simulate user object or role for logic branching.
        # user = db.session.get(User, user_id) # Old way

        user_doc = await db.users.find_one({"email": current_user_email})
        if not user_doc:
            # This should ideally not happen if token is valid and comes from a user in DB
            logger.warning(f"User not found in DB for email {current_user_email} (from token) during /recent-activity.")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found or not authorized")

        user_obj = User(**user_doc)
        user_id_for_filtering_str = str(user_obj.id) # Using MongoDB _id as string
        user_role_for_filtering = user_obj.role
        logger.info(f"Recent activity access by: {current_user_email} (Role: {user_role_for_filtering})")

        # Placeholder: Database interaction for querying ActivityLog commented out
        # query = db.activity_log.find(...)
        # if severity: query_filters["severity"] = severity
        # if action: query_filters["action"] = {"$regex": action} # Example for partial match
        # if user_role_for_filtering != 'regulator':
        #     query_filters["user_id_str"] = user_id_for_filtering_str
        # Sort by timestamp, apply limit
        # db_activities = await db.activity_log.find(query_filters).sort("timestamp", -1).limit(limit).to_list(length=limit)
        # activity_data = [...] # Transformation from db_activities to ActivityItem

        # Simulated response
        simulated_activities: List[ActivityItem] = []
        for i in range(min(limit, 3)): # Simulate a few activities
            # In simulation, if user is not regulator, link activity to this user for demo
            activity_user_id_sim = int(user_id_for_filtering_str.replace("a","1").replace("b","2").replace("c","3").replace("d","4").replace("e","5").replace("f","6")[:5], 16) % 1000 if user_id_for_filtering_str and user_role_for_filtering != 'regulator' else (i + 1)

            # Only add activity if it matches filter criteria (simplified simulation)
            if severity and severity != f"sev{i+1}":
                continue
            if action and action not in f"ActionType{i+1} details":
                continue

            simulated_activities.append(ActivityItem(
                id=i+1,
                action=f"ActionType{i+1} details",
                description=f"Simulated activity description {i+1}",
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=i*5),
                user_id=activity_user_id,
                severity=f"sev{i+1}",
                ip_address="127.0.0.1",
                meta_data={"key": f"value{i+1}"}
            ))

        return RecentActivityResponse(
            activities=simulated_activities,
            total_count=len(simulated_activities),
            filters_applied=RecentActivityFilters(severity=severity, action=action, limit=limit)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recent activity for user {current_user_email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Failed to get recent activity: {str(e)}')

# --- Pydantic Models for Stats ---
class MonthlyDonation(BaseModel):
    month: str
    donations: int

class OrganDistributionItem(BaseModel):
    name: str
    value: int

class RecentActivityStatItem(BaseModel): # Simplified from ActivityItem
    action: str
    description: Optional[str] = None
    timestamp: datetime
    user_id: Optional[int] = None # Or str
    severity: Optional[str] = None

class DashboardStatsResponse(BaseModel):
    totalUsers: int
    totalDonors: int
    totalHospitals: int
    totalRegulators: int
    totalHealthCards: int
    totalMatches: int
    successfulMatches: int
    activeTransports: int
    monthlyDonations: List[MonthlyDonation]
    organDistribution: List[OrganDistributionItem]
    recentActivities: List[RecentActivityStatItem]
    authenticated_user_email: Optional[str] = None # Changed from boolean to reflect actual data

# --- Optional Authentication ---
# verify_token raises HTTPException if token is invalid or missing.
# For an optional auth endpoint, we need a different approach.
# We can create a new dependency that tries to verify token but doesn't fail hard.
async def try_verify_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization")
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            try:
                # This is a simplified version of what verify_token in app.py might do.
                # Ideally, verify_token itself would have an optional mode or this logic
                # would be shared. For now, duplicating essential part of logic.
                # SECRET_KEY and ALGORITHM would need to be accessible here, or pass request to verify_token.
                # This is a placeholder for actual optional token verification.
                # For now, if there's a bearer token, we'll just log it and not validate deeply here.
                # payload = jwt.decode(parts[1], SECRET_KEY, algorithms=[ALGORITHM])
                # return payload.get("sub")
                logger.info(f"Optional auth: Token found for /stats: {parts[1][:20]}...") # Log redacted token
                # This should actually call a validation function similar to verify_token but without raising exceptions on missing/invalid token
                # For simulation, let's assume if a token is present, it's for "testoptional@example.com"
                return "testoptional@example.com" # Placeholder for a decoded email if token were valid
            except Exception as e: # Catching generic Exception for placeholder
                logger.warning(f"Optional auth: Invalid token provided for /stats: {e}")
                return None # Invalid token means no authenticated user
    return None # No token provided

# --- Route Implementation for Stats ---
@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user_email: Optional[str] = Depends(try_verify_token) # Optional auth
):
    """Get comprehensive dashboard statistics - PUBLIC (optional auth)"""
    try:
        # Fetch user counts from MongoDB
        total_users = await db.users.count_documents({})
        total_donors = await db.users.count_documents({"role": "donor"})
        total_hospitals = await db.users.count_documents({"role": "hospital"})
        total_regulators = await db.users.count_documents({"role": "regulator"})

        # Placeholder/Simulated values for other stats (would require other collections)
        total_health_cards = 150 # Simulated
        total_matches = 75      # Simulated
        successful_matches = 60 # Simulated
        active_transports = 5   # Simulated

        # Simulated monthly data
        monthly_data = [
            MonthlyDonation(month='Jan', donations=10), MonthlyDonation(month='Feb', donations=15),
            MonthlyDonation(month='Mar', donations=12), MonthlyDonation(month='Apr', donations=18),
            MonthlyDonation(month='May', donations=20), MonthlyDonation(month='Jun', donations=22),
        ]

        # Simulated organ distribution
        organ_distribution = [
            OrganDistributionItem(name='Heart', value=30), OrganDistributionItem(name='Liver', value=25),
            OrganDistributionItem(name='Kidney', value=35), OrganDistributionItem(name='Lung', value=10)
        ]

        # Simulated recent activities (simplified)
        sim_recent_activities = [
            RecentActivityStatItem(action="User Login", timestamp=datetime.now(timezone.utc) - timedelta(hours=1), user_id=1, severity="info"),
            RecentActivityStatItem(action="Data Update", timestamp=datetime.now(timezone.utc) - timedelta(hours=2), user_id=2, severity="info"),
        ]

        if current_user_email:
            logger.info(f"Dashboard stats accessed by authenticated user: {current_user_email}")
            # log_activity(user_id, 'dashboard_access', ...) # Old way

        return DashboardStatsResponse(
            totalUsers=total_users,
            totalDonors=total_donors,
            totalHospitals=total_hospitals,
            totalRegulators=total_regulators,
            totalHealthCards=total_health_cards,
            totalMatches=total_matches,
            successfulMatches=successful_matches,
            activeTransports=active_transports,
            monthlyDonations=monthly_data,
            organDistribution=organ_distribution,
            recentActivities=sim_recent_activities,
            authenticated_user_email=current_user_email
        )

    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Failed to get dashboard stats: {str(e)}')

# All routes in this file should now be refactored.
