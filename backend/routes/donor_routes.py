from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime

from backend.app import (
    db,
    Donor,  # Pydantic model for Donor MongoDB document
    DonorRegistration, # Pydantic model for donor registration request body
    User,   # Pydantic model for User MongoDB document
    verify_token,
    logger
)

router = APIRouter(prefix="/donors", tags=["Donors"])

@router.post("/register", response_model=Donor, status_code=status.HTTP_201_CREATED)
async def register_donor_profile(
    donor_data: DonorRegistration,
    current_user_email: str = Depends(verify_token)
):
    """
    Register a new donor profile.
    The user must already exist and be authenticated.
    This endpoint creates the donor-specific information.
    """
    # Fetch the authenticated user from the users collection
    user_doc = await db.users.find_one({"email": current_user_email})
    if not user_doc:
        # This should not happen if verify_token is effective
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user not found in database."
        )
    user = User(**user_doc)

    # Validate user role (optional, could allow any user to create a donor profile for themselves)
    # For this example, let's assume any authenticated user can register as a donor ONCE.
    # if user.role not in ["donor", "admin"]: # Or more specific logic
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail=f"User role '{user.role}' not authorized to register donor profiles."
    #     )

    # Check if a donor profile for this user_email already exists
    existing_donor = await db.donors.find_one({"user_email": current_user_email})
    if existing_donor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Donor profile already exists for user {current_user_email}"
        )

    # Create Donor Pydantic model instance
    # DonorRegistration fields are expected to be a subset of Donor fields
    # or directly mappable.
    new_donor_data = donor_data.model_dump()
    new_donor = Donor(
        **new_donor_data,
        user_email=current_user_email,
        # registered_at is handled by default_factory in Pydantic model
    )

    # Insert into MongoDB
    try:
        result = await db.donors.insert_one(new_donor.model_dump(by_alias=True, exclude=["id"]))
        created_doc = await db.donors.find_one({"_id": result.inserted_id})
        if not created_doc:
            # This would be an unexpected error if insert_one succeeded
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created donor profile."
            )
        logger.info(f"Donor profile created for user: {current_user_email}, Donor ID: {result.inserted_id}")
        return Donor(**created_doc)
    except Exception as e:
        logger.error(f"Error creating donor profile for {current_user_email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database operation failed: {e}"
        )


@router.get("/", response_model=List[Donor])
async def list_all_donors(
    current_user_email: str = Depends(verify_token),
    skip: int = 0,
    limit: int = 100
):
    """
    List all donor profiles. (Protected - e.g., for admin/regulator use)
    """
    user_doc = await db.users.find_one({"email": current_user_email})
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found.")

    user = User(**user_doc)
    # Example: Only allow 'admin' or 'regulator' to list all donors
    if user.role not in ["admin", "regulator"]:
        logger.warning(f"User {current_user_email} (role: {user.role}) attempted to list all donors.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to list all donor profiles.")

    donors_cursor = db.donors.find({}).skip(skip).limit(limit)
    donors_list = [Donor(**doc) async for doc in donors_cursor]
    logger.info(f"Admin user {current_user_email} listed {len(donors_list)} donors.")
    return donors_list


@router.get("/{user_email}", response_model=Donor)
async def get_donor_profile(
    user_email: str,
    requesting_user_email: str = Depends(verify_token)
):
    """
    Get a specific donor profile by user_email.
    Admins/regulators can access any. Users can access their own.
    """
    requesting_user_doc = await db.users.find_one({"email": requesting_user_email})
    if not requesting_user_doc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requesting user not found.")

    requesting_user = User(**requesting_user_doc)

    # Authorization check
    if requesting_user.role not in ["admin", "regulator"] and requesting_user_email != user_email:
        logger.warning(f"User {requesting_user_email} (role: {requesting_user.role}) unauthorized attempt to access donor profile for {user_email}.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this donor profile."
        )

    donor_doc = await db.donors.find_one({"user_email": user_email})
    if not donor_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donor profile not found for user {user_email}"
        )

    logger.info(f"User {requesting_user_email} accessed donor profile for {user_email}.")
    return Donor(**donor_doc)
