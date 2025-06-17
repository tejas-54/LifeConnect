from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import json
import os # For os.path.basename if simulating file paths
import time # For generating unique IDs if needed

# Assuming these are in backend.app or a shared utility module
from backend.app import (
    db,   # MongoDB instance
    User, # User Pydantic Model
    HealthRecord, # New Pydantic model for HealthRecord collection
    verify_token,
    logger,
    IPFS_API_URL,
    call_external_service,
)
# Database models are commented out as per plan.
# Direct db access will be replaced by service calls or removed/simulated.
# from models import db, User, HealthCard
# from utils import log_activity, create_response # Flask specific

router = APIRouter(prefix="/health-cards", tags=["Health Cards"]) # Changed prefix to be more RESTful

# --- Pydantic Models for Health Card Responses ---
class HealthCardData(BaseModel): # Represents the content of card_data
    name: str
    age: int
    bloodType: str
    # Add other fields that are typically inside card_data JSON
    # For example:
    allergies: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    conditions: Optional[List[str]] = None
    emergencyContacts: Optional[List[Dict[str, str]]] = None # e.g. {"name": "Jane", "phone": "123"}
    user_id: Optional[int] = None # Or str, depending on how user ID is handled
    wallet_address: Optional[str] = None
    generated_by: Optional[str] = None
    patientId: Optional[str] = None # Often part of the card data itself

class HealthCardResponseItem(BaseModel):
    id: int # Assuming HealthCard DB model had an id
    patient_id: str
    card_data: HealthCardData # Parsed JSON data
    ipfs_cid: Optional[str] = None
    created_at: datetime
    updated_at: datetime # Assuming HealthCard DB model had updated_at

# In-memory store for health cards (simulation)
health_cards_db_sim: Dict[str, HealthCardResponseItem] = {}


@router.get("/", response_model=List[HealthCardResponseItem]) # Changed from /list to /
async def list_health_cards(
    current_user_email: str = Depends(verify_token)
):
    """List user's health cards"""
    try:
        user_doc = await db.users.find_one({"email": current_user_email})
        if not user_doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in DB")
        user_obj = User(**user_doc) # For easier access to user fields like id

        # Filter health_cards_db_sim by comparing card_data.user_id with user_obj.id (as string)
        # The HealthCardData model stores user_id as Optional[int] or Optional[str].
        # The simulated user_id in generate_health_card_route was an int.
        # MongoDB _id is an ObjectId, user_obj.id is PyObjectId. Let's use str(user_obj.id).
        # For the simulation to work, user_id in HealthCardData should be consistently str or int.
        # The previous mock generator used an int. Let's assume for now that it's an int.
        # If user_obj.id is PyObjectId, we need a consistent int representation for comparison.
        # For simplicity in mock, we'll use the hash again, assuming it was stored that way.
        user_id_for_filtering_simulated = int(str(user_obj.id)[-5:], 16) % 10000 \
            if user_obj.id else hash(current_user_email) % 10000

        user_cards = [
            card for card in health_cards_db_sim.values()
            if card.card_data.user_id == user_id_for_filtering_simulated
        ]

        logger.info(f"User {current_user_email} (ID: {str(user_obj.id)}) listed {len(user_cards)} health cards.")
        return user_cards

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list health cards for user {current_user_email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Failed to list health cards: {str(e)}')

@router.get("/{patient_id}", response_model=HealthCardResponseItem)
async def get_health_card(
    patient_id: str = Path(..., description="The Patient ID of the health card to retrieve"),
    current_user_email: str = Depends(verify_token)
):
    """Get specific health card by Patient ID"""
    try:
        health_card = health_cards_db_sim.get(patient_id)

        if not health_card:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health card not found")

        # Authorization: Check if user owns this card or is authorized (e.g., hospital, regulator)
        user_doc = await db.users.find_one({"email": current_user_email})
        if not user_doc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User details not found, authorization failed.")
        user_obj = User(**user_doc)

        # Assuming health_card.card_data.user_id was stored as an int in the simulation
        user_id_for_filtering_simulated = int(str(user_obj.id)[-5:], 16) % 10000 \
            if user_obj.id else hash(current_user_email) % 10000

        user_role = user_obj.role

        if health_card.card_data.user_id != user_id_for_filtering_simulated and user_role not in ['hospital', 'regulator', 'admin']:
            logger.warning(f"Unauthorized attempt by user {current_user_email} (role: {user_role}) to access health card {patient_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to health card")

        logger.info(f"User {current_user_email} (ID: {str(user_obj.id)}) retrieved health card {patient_id}")
        return health_card

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get health card {patient_id} for user {current_user_email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Failed to get health card: {str(e)}')

# --- Pydantic Models for Generate Health Card ---
class HealthCardCreateRequest(BaseModel):
    name: str = Field(..., example="John Doe")
    age: int = Field(..., example=30)
    bloodType: str = Field(..., example="O+")
    # Include other fields that patient_data might contain from the original Flask route
    allergies: Optional[List[str]] = Field(None, example=["Peanuts", "Pollen"])
    medications: Optional[List[str]] = Field(None, example=["Lisinopril"])
    conditions: Optional[List[str]] = Field(None, example=["Hypertension"])
    emergencyContacts: Optional[List[Dict[str, str]]] = Field(None, example=[{"name": "Jane Doe", "phone": "555-1234"}])
    # other fields from patient_data like donorStatus, organTypes can be added if they are part of the input
    donorStatus: Optional[bool] = Field(None, example=True)
    organTypes: Optional[List[str]] = Field(None, example=["heart", "liver"])


class HealthCardFilesResponse(BaseModel):
    json_file: Optional[str] = Field(None, alias="json") # Using alias for key like in original
    pdf_file: Optional[str] = Field(None, alias="pdf")
    image_file: Optional[str] = Field(None, alias="image")

class HealthCardIpfsResponse(BaseModel):
    cid: Optional[str] = None
    url: Optional[str] = None

class GenerateHealthCardResponse(BaseModel):
    health_card: HealthCardData # The generated card data
    patient_id: str
    files: HealthCardFilesResponse
    ipfs: HealthCardIpfsResponse

# Placeholder for HealthCardGenerator service/component
# In a real FastAPI app, this might be injected via Depends or be a global instance.
class MockHealthCardGenerator:
    async def complete_health_card_workflow(self, patient_data: Dict[str, Any], generate_pdf: bool, generate_image: bool, upload_to_ipfs: bool):
        # Simulate workflow
        logger.info(f"Simulating health card workflow for: {patient_data.get('name')}")

        # Simulate patient ID generation
        patient_id = patient_data.get("patientId", f"PATIENT_{int(time.time())}")
        patient_data_with_id = {**patient_data, "patientId": patient_id}

        # Simulate file paths
        base_name = f"{patient_id}_{int(time.time())}"
        json_path = f"/tmp/{base_name}.json"
        pdf_path = f"/tmp/{base_name}.pdf" if generate_pdf else None
        image_path = f"/tmp/{base_name}.png" if generate_image else None

        # Simulate IPFS upload
        ipfs_result = None
        if upload_to_ipfs:
            # 실제 IPFS 업로드는 call_external_service 사용
            # ipfs_payload = {"file_content": json.dumps(patient_data_with_id)} # Example
            # ipfs_response = await call_external_service(f"{IPFS_API_URL}/api/v0/add", method="POST", data=ipfs_payload)
            # if ipfs_response and ipfs_response.get("Hash"):
            #     ipfs_result = {"cid": ipfs_response["Hash"], "url": f"https://ipfs.io/ipfs/{ipfs_response['Hash']}"}
            # else:
            #     ipfs_result = {"cid": "QmSimulatedCidForHealthCard", "url": "https://ipfs.io/ipfs/QmSimulatedCidForHealthCard"}
            # For now, direct simulation:
            time.sleep(0.1) # Simulate delay
            ipfs_cid = f"QmSimulatedCid_{base_name}"
            ipfs_result = {"cid": ipfs_cid, "url": f"https://ipfs.io/ipfs/{ipfs_cid}"}
            logger.info(f"Simulated IPFS Upload: CID {ipfs_cid}")

        return {
            "health_card": patient_data_with_id, # This is HealthCardData compatible
            "json_path": json_path,
            "pdf_path": pdf_path,
            "image_path": image_path,
            "ipfs_result": ipfs_result
        }

health_card_generator_service = MockHealthCardGenerator() # Global instance for now


@router.post("/generate", response_model=GenerateHealthCardResponse)
async def generate_health_card_route( # Renamed from generate_health_card to avoid conflict with Pydantic model name
    card_request: HealthCardCreateRequest,
    current_user_email: str = Depends(verify_token)
):
    """Generate comprehensive health card"""
    try:
        user_doc = await db.users.find_one({"email": current_user_email})
        if not user_doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in DB")
        user_obj = User(**user_doc)

        # Using a simulated int ID for card_data.user_id as per previous logic in this file's simulation
        simulated_user_id_for_card = int(str(user_obj.id)[-5:], 16) % 10000 \
            if user_obj.id else hash(current_user_email) % 10000

        user_wallet_address = user_obj.wallet_address or "0xUserWalletPlaceholder"
        user_name_or_wallet = user_obj.name or user_wallet_address

        patient_data_dict = card_request.model_dump(exclude_unset=True)
        patient_data_dict.update({
            'user_id': simulated_user_id_for_card, # Store this simulated int ID in card_data
            'wallet_address': user_wallet_address,
            'generated_by': user_name_or_wallet
        })

        # Use the (mocked) health card generator service
        result = await health_card_generator_service.complete_health_card_workflow(
            patient_data_dict,
            generate_pdf=True, # Assuming these are desired features
            generate_image=True,
            upload_to_ipfs=True
        )

        # Simulate saving to in-memory DB
        patient_id = result['health_card'].get('patientId')
        if not patient_id: # Should be generated by workflow
            patient_id = f"PATIENT_{int(time.time())}"
            result['health_card']['patientId'] = patient_id

        # Ensure health_card part of result is compatible with HealthCardData model
        # The mock generator is designed to return compatible data.
        created_card_data = HealthCardData(**result['health_card'])

        # Conceptually create HealthRecord data (would be saved to db.health_records)
        ipfs_cid_from_result = result['ipfs_result']['cid'] if result.get('ipfs_result') else None
        if ipfs_cid_from_result:
            health_record_entry_data = HealthRecord(
                user_email=current_user_email, # Link to the user who owns this card
                record_cid=ipfs_cid_from_result,
                record_type="generated_health_card",
                summary=f"Health card for {card_request.name}, Patient ID: {patient_id}",
                created_by_user_email=current_user_email,
                last_updated=datetime.now(timezone.utc)
                # access_list could be populated based on user's settings or defaults
            )
            # In a real scenario: await db.health_records.insert_one(health_record_entry_data.model_dump(by_alias=True, exclude=["id"]))
            logger.info(f"Conceptual HealthRecord created for CID: {health_record_entry_data.record_cid}")

        new_health_card_db_entry = HealthCardResponseItem(
            id=len(health_cards_db_sim) + 1, # Simulated DB ID
            patient_id=patient_id,
            card_data=created_card_data, # This contains the full health data for the response
            ipfs_cid=ipfs_cid_from_result, # This is the link to the IPFS record
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        health_cards_db_sim[patient_id] = new_health_card_db_entry # Simulate saving the rich item for GET responses

        logger.info(f"User {current_user_email} generated health card for {card_request.name} (Patient ID: {patient_id}), IPFS CID: {ipfs_cid_from_result}")

        return GenerateHealthCardResponse(
            health_card=created_card_data,
            patient_id=patient_id,
            files=HealthCardFilesResponse(
                json=os.path.basename(result['json_path']) if result.get('json_path') else None,
                pdf=os.path.basename(result['pdf_path']) if result.get('pdf_path') else None,
                image=os.path.basename(result['image_path']) if result.get('image_path') else None
            ),
            ipfs=HealthCardIpfsResponse(
                cid=result['ipfs_result']['cid'] if result.get('ipfs_result') else None,
                url=result['ipfs_result']['url'] if result.get('ipfs_result') else None
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health card generation failed for user {current_user_email}: {str(e)}")
        # Log activity was here in Flask, now handled by logger
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Health card generation failed: {str(e)}')

# All routes in this file should now be refactored.
