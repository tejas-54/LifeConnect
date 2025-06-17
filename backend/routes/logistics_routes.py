from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import json
import time # For generating unique IDs if needed

import asyncio # Ensure asyncio is imported

import asyncio # Ensure asyncio is imported

# Assuming these are in backend.app or a shared utility module
from backend.app import (
    db,   # MongoDB instance
    User, # User Pydantic Model
    Transport, PyObjectId, # New Pydantic model for Transport collection & PyObjectId
    verify_token,
    logger,
    LOGISTICS_ENGINE_URL,
    call_external_service,
)
# Database models are commented out as per plan.
# from models import db, User, TransportPlan
# from utils import log_activity, create_response # Flask specific

router = APIRouter(prefix="/logistics", tags=["Logistics"])

# --- Pydantic Models for Logistics Responses ---
class LocationModel(BaseModel):
    name: str
    # Add other relevant fields like address, lat, lng if available/needed
    lat: Optional[float] = None
    lng: Optional[float] = None

class TransportPlanItem(BaseModel):
    transport_id: str
    organ_type: str
    vehicle_type: Optional[str] = None
    status: str
    pickup_location: LocationModel
    delivery_location: LocationModel
    estimated_duration: int # minutes
    estimated_distance: Optional[float] = None # km
    created_at: datetime
    started_at: Optional[datetime] = None # Added for progress calculation
    route_progress: Optional[int] = Field(None, ge=0, le=100)
    current_temperature: Optional[str] = None # e.g., "4°C"
    estimated_arrival: Optional[datetime] = None
    alerts: List[str] = [] # List of alert messages

class TransportTrackingData(BaseModel):
    transport_id: str
    status: str
    progress: int = Field(..., ge=0, le=100)
    current_location: Dict[str, float] # e.g., {'lat': 40.7128, 'lng': -74.0060}
    temperature: Optional[str] = None
    humidity: Optional[str] = None
    last_update: datetime
    estimated_arrival: datetime
    route_data: Optional[Dict[str, Any]] = None


# Local in-memory simulation for transport plans, as transport_db was removed from app.py
transport_db_sim: Dict[str, Dict[str, Any]] = {}
# TODO: Replace with MongoDB collection access, e.g., transport_collection = db.transports

@router.get("/active-transports", response_model=List[TransportPlanItem])
async def get_active_transports(
    current_user_email: str = Depends(verify_token)
):
    """Get all active transport plans"""
    try:
        user_doc = await db.users.find_one({"email": current_user_email})
        user_role = "user" # Default role
        if user_doc:
            user_obj = User(**user_doc)
            user_role = user_obj.role
        else:
            # This case should ideally be prevented by verify_token if it ensures user exists
            logger.warning(f"User not found in DB for email {current_user_email} during /active-transports. Using default role 'user'.")

        logger.info(f"User {current_user_email} (role: {user_role}) fetching active transports.")

        active_plans: List[TransportPlanItem] = []
        # Simulate filtering from local transport_db_sim
        for transport_id, plan_data_dict in transport_db_sim.items():
            if plan_data_dict.get("status") in ['planned', 'in_progress']:
                # Adapt dict from transport_db_sim to TransportPlanItem
                # This requires transport_db items to have compatible fields or perform careful mapping
                try:
                    # Ensure location data is correctly formatted or provide defaults
                    pickup_loc_data = plan_data_dict.get("pickup_location", {"name": "Unknown Pickup"})
                    if isinstance(pickup_loc_data, str): pickup_loc_data = json.loads(pickup_loc_data)

                    delivery_loc_data = plan_data_dict.get("delivery_location", {"name": "Unknown Delivery"})
                    if isinstance(delivery_loc_data, str): delivery_loc_data = json.loads(delivery_loc_data)

                    plan_item = TransportPlanItem(
                        transport_id=transport_id,
                        organ_type=plan_data_dict.get("organ_type", "unknown"),
                        vehicle_type=plan_data_dict.get("vehicle_type"),
                        status=plan_data_dict.get("status", "unknown"),
                        pickup_location=LocationModel(**pickup_loc_data),
                        delivery_location=LocationModel(**delivery_loc_data),
                        estimated_duration=plan_data_dict.get("estimated_duration", 60),
                        estimated_distance=plan_data_dict.get("estimated_distance"),
                        created_at=datetime.fromisoformat(plan_data_dict.get("created_at")) if plan_data_dict.get("created_at") else datetime.now(timezone.utc),
                        started_at=datetime.fromisoformat(plan_data_dict.get("started_at")) if plan_data_dict.get("started_at") else None,
                        current_temperature=plan_data_dict.get("current_temperature", "4°C"),
                        alerts=plan_data_dict.get("alerts", [])
                    )

                    # Calculate progress and estimated_arrival
                    if plan_item.status == 'in_progress' and plan_item.started_at:
                        elapsed_minutes = (datetime.now(timezone.utc) - plan_item.started_at).total_seconds() / 60
                        if plan_item.estimated_duration > 0:
                             plan_item.route_progress = min(95, int((elapsed_minutes / plan_item.estimated_duration) * 100))
                        else:
                            plan_item.route_progress = 0
                    elif plan_item.status == 'planned':
                        plan_item.route_progress = 0

                    if plan_item.estimated_duration:
                         plan_item.estimated_arrival = (plan_item.started_at or plan_item.created_at) + timedelta(minutes=plan_item.estimated_duration)

                    active_plans.append(plan_item)
                except Exception as e_map:
                    logger.error(f"Error mapping transport_db item {transport_id} to Pydantic model: {e_map}")
                    continue # Skip this item

        # Role-based filtering (original code showed max 10 for non-regulators)
        if user_role != 'regulator' and len(active_plans) > 10:
            active_plans = active_plans[:10]
            logger.info(f"Non-regulator access, limiting to 10 active transports.")

        return active_plans

    except Exception as e:
        logger.error(f"Failed to get active transports for user {current_user_email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Failed to get active transports: {str(e)}')

@router.get("/track-transport/{transport_id}", response_model=Optional[TransportTrackingData])
async def track_transport(
    transport_id: str = Path(..., description="The ID of the transport to track"),
    current_user_email: str = Depends(verify_token) # Assuming tracking is authenticated
):
    """Track specific transport"""
    try:
        # Simulate fetching from local transport_db_sim
        plan_data_dict = transport_db_sim.get(transport_id)

        if not plan_data_dict:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transport not found")

        logger.info(f"User {current_user_email} tracking transport {transport_id}.")

        status = plan_data_dict.get("status", "unknown")
        created_at = datetime.fromisoformat(plan_data_dict.get("created_at")) if plan_data_dict.get("created_at") else datetime.now(timezone.utc)
        started_at = datetime.fromisoformat(plan_data_dict.get("started_at")) if plan_data_dict.get("started_at") else None
        estimated_duration = plan_data_dict.get("estimated_duration", 60) # minutes

        progress = 0
        if status == 'in_progress' and started_at:
            elapsed_minutes = (datetime.now(timezone.utc) - started_at).total_seconds() / 60
            if estimated_duration > 0:
                progress = min(95, int((elapsed_minutes / estimated_duration) * 100))

        # Simulated route_data if not present or not JSON
        route_data_sim = {"points": [], "summary": "Simulated route"}
        try:
            route_data_from_db = plan_data_dict.get("route_data")
            if isinstance(route_data_from_db, str):
                route_data_sim = json.loads(route_data_from_db)
            elif isinstance(route_data_from_db, dict):
                route_data_sim = route_data_from_db
        except json.JSONDecodeError:
            logger.warning(f"Could not parse route_data for transport {transport_id}")


        return TransportTrackingData(
            transport_id=transport_id,
            status=status,
            progress=progress,
            current_location={'lat': 40.7128, 'lng': -74.0060},  # Mock GPS data
            temperature=plan_data_dict.get("current_temperature", "4°C"), # Mock
            humidity='65%', # Mock
            last_update=datetime.now(timezone.utc),
            estimated_arrival=(started_at or created_at) + timedelta(minutes=estimated_duration),
            route_data=route_data_sim
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transport tracking failed for {transport_id} by user {current_user_email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Transport tracking failed: {str(e)}')

import asyncio # Added for asyncio.sleep

# --- Pydantic Models for Create Transport Plan ---
class OrganDataRequest(BaseModel):
    organType: str = Field(..., example="heart")
    # Add any other relevant organ details needed by logistics
    weight_kg: Optional[float] = Field(None, example=0.3)

class LocationRequest(BaseModel): # Reusing LocationModel without lat/lng for input simplicity
    name: str = Field(..., example="City General Hospital")
    address: Optional[str] = Field(None, example="123 Main St, Anytown, USA")
    # If lat/lng are inputs, add them here. Original implies name is primary input for engine.

class CreateTransportPlanRequest(BaseModel):
    organData: OrganDataRequest
    pickupLocation: LocationRequest
    deliveryLocation: LocationRequest

class VehicleInfoResponse(BaseModel):
    type: str
    id: Optional[str] = None
    driver: Optional[str] = None

class RouteInfoResponse(BaseModel):
    # Define based on what logistics_engine.create_transport_plan actually returns for 'route'
    # Or what the external LOGISTICS_ENGINE_URL/create-plan would return
    duration_minutes: int
    distance_km: float
    path_polyline: Optional[str] = None # Example: encoded polyline
    waypoints: Optional[List[Dict[str, Any]]] = None

class CreateTransportPlanResponse(BaseModel):
    transport_id: str
    # transport_plan: Dict[str, Any] # The raw plan from logistics engine
    estimated_duration_minutes: int
    estimated_distance_km: float
    vehicle_type: str
    status: str = "planned"
    # Optionally include parts of the plan if needed, e.g., route details
    route: Optional[RouteInfoResponse] = None
    pickup_location: LocationModel # Echo back resolved/used locations
    delivery_location: LocationModel


@router.post("/create-transport-plan", response_model=CreateTransportPlanResponse)
async def create_transport_plan(
    plan_request: CreateTransportPlanRequest,
    current_user_email: str = Depends(verify_token)
):
    """Create comprehensive transport plan"""
    try:
        user_doc = await db.users.find_one({"email": current_user_email})
        simulated_user_id_str = "unknown_user"
        if user_doc:
            user_obj = User(**user_doc)
            simulated_user_id_str = str(user_obj.id) if user_obj.id else current_user_email
        else:
            logger.warning(f"User not found in DB for email {current_user_email} during /create-transport-plan. Using placeholder ID.")
            # Fallback if user somehow not in DB, though verify_token should prevent this.
            # simulated_user_id generation for transport_id needs a string.
            simulated_user_id_str = current_user_email # Or some other placeholder

        # Call external logistics engine
        # The request to the logistics engine needs to match its expected API.
        # Assuming it takes organ info, and pickup/delivery names/addresses.
        logistics_payload = {
            "organ_details": plan_request.organData.model_dump(),
            "pickup": plan_request.pickupLocation.model_dump(),
            "delivery": plan_request.deliveryLocation.model_dump()
        }

        # external_plan_response = await call_external_service(
        #     f"{LOGISTICS_ENGINE_URL}/create-plan", # Assuming an endpoint like /create-plan
        #     method="POST",
        #     data=logistics_payload
        # )
        # Simulate external call for now
        await asyncio.sleep(0.1) # Simulate network delay
        external_plan_response = {
            "vehicle": {"type": "drone_ambulance", "id": "DRONE007", "driver": "AI Pilot"},
            "route": {"duration_minutes": 120, "distance_km": 55.5, "summary": "Highway A1 -> B2"},
            "status": "plan_generated_successfully",
            "pickup_details_resolved": {**plan_request.pickupLocation.model_dump(), "lat": 34.0522, "lng": -118.2437},
            "delivery_details_resolved": {**plan_request.deliveryLocation.model_dump(), "lat": 36.1699, "lng": -115.1398}
        }


        if not external_plan_response or external_plan_response.get("status") != "plan_generated_successfully":
            logger.error(f"Logistics engine failed to create a plan. Payload: {logistics_payload}, Response: {external_plan_response}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logistics engine could not generate a plan.")

        transport_id = f"TRN_{int(time.time())}_{simulated_user_id_str.replace('@','_').replace('.','_')}" # Ensure ID is valid string

        # Store in our local in-memory transport_db_sim
        route_data_from_engine = external_plan_response.get('route', {})
        vehicle_data_from_engine = external_plan_response.get('vehicle', {})

        resolved_pickup_loc = external_plan_response.get("pickup_details_resolved", plan_request.pickupLocation.model_dump())
        resolved_delivery_loc = external_plan_response.get("delivery_details_resolved", plan_request.deliveryLocation.model_dump())

        # Simulate an organ_id (in a real scenario, this would come from an Organ document)
        simulated_organ_id = PyObjectId() # Generate a new ObjectId for placeholder

        # Data for transport_db_sim - this should be what TransportPlanItem and TransportTrackingData can be derived from
        # It doesn't need to be a direct Transport model instance if these response models need richer/different data.
        # However, we should try to make it somewhat compatible or show the mapping.
        created_at_dt = datetime.now(timezone.utc)
        transport_db_entry_for_sim = {
            "transport_id": transport_id, # This is the key for the dict, also part of the value for consistency
            "organ_type": plan_request.organData.organType, # Keep for TransportPlanItem
            "organ_id_str": str(simulated_organ_id), # Store string version of PyObjectId for JSON friendliness if needed by sim
            "pickup_location": json.dumps(resolved_pickup_loc),
            "delivery_location": json.dumps(resolved_delivery_loc),
            "vehicle_type": vehicle_data_from_engine.get('type', 'ambulance'),
            "route_data": json.dumps(route_data_from_engine),
            "estimated_duration": route_data_from_engine.get('duration_minutes', 60),
            "estimated_distance": route_data_from_engine.get('distance_km', 10),
            "status": "planned",
            "created_at": created_at_dt.isoformat(),
            "updated_at": created_at_dt.isoformat(), # Add for consistency with MongoModel
            "user_id_creator": simulated_user_id_str,
            "current_temperature": "4°C",
            "alerts": [],
            "logistics_plan_cid": f"QmSimulatedLogisticsPlanCID_{transport_id}", # Example
            "departure_time": None, # Not yet departed
            "arrival_time": None, # Not yet arrived
        }
        transport_db_sim[transport_id] = transport_db_entry_for_sim

        # Conceptually create a Transport Pydantic model instance (as if saving to MongoDB)
        conceptual_transport_doc = Transport(
            id=PyObjectId(transport_id.split("_")[1] + transport_id.split("_")[2]), # Create a valid ObjectId for id
            organ_id=simulated_organ_id,
            status=transport_db_entry_for_sim["status"],
            estimated_arrival= (created_at_dt + timedelta(minutes=transport_db_entry_for_sim["estimated_duration"])) if transport_db_entry_for_sim.get("estimated_duration") else None,
            logistics_plan_cid=transport_db_entry_for_sim["logistics_plan_cid"],
            vehicle_id=vehicle_data_from_engine.get('id'),
            updated_at=created_at_dt
            # other fields like current_location, departure/arrival times would be updated later
        )
        logger.info(f"Conceptual Transport document created for MongoDB: {conceptual_transport_doc.model_dump(by_alias=True)}")
        logger.info(f"User {current_user_email} created transport plan {transport_id} for {plan_request.organData.organType} organ.")

        # WebSocket emit logic commented out

        return CreateTransportPlanResponse(
            transport_id=transport_id,
            estimated_duration_minutes=transport_db_entry_for_sim["estimated_duration"],
            estimated_distance_km=transport_db_entry_for_sim["estimated_distance"],
            vehicle_type=transport_db_entry_for_sim["vehicle_type"],
            status=transport_db_entry_for_sim["status"],
            route=RouteInfoResponse(**route_data_from_engine) if route_data_from_engine else None,
            pickup_location=LocationModel(**resolved_pickup_loc),
            delivery_location=LocationModel(**resolved_delivery_loc)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transport plan creation failed for user {current_user_email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Transport plan creation failed: {str(e)}')

# All routes in this file should now be refactored.
