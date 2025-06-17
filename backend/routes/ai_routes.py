from fastapi import APIRouter, Depends, HTTPException
import json
from datetime import datetime, timezone

# from models import db, OrganMatch # SQLAlchemy, will be replaced with MongoDB interactions
# from utils import log_activity, create_response # Flask specific, will be replaced
# Imports from backend.app
from backend.app import (
    db,  # MongoDB database instance
    User, # User Pydantic model
    verify_token,
    call_external_service,
    AI_ENGINE_URL,
    logger
)

router = APIRouter(prefix="/ai", tags=["AI Engine"])

@router.post('/find-matches')
async def find_organ_matches(
    data: dict,
    current_user_email: str = Depends(verify_token)
):
    """
    Find organ matches using AI.
    Request body should be a JSON object with 'organData' and optional 'recipients'.
    """
    try:
        user_doc = await db.users.find_one({"email": current_user_email})
        if not user_doc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found or not authorized")

        # Use user_doc["_id"] or a string version of it if you need user_id as an integer/string
        # For simplicity, let's assume logging/internal ops can use email or stringified ObjectId
        user_identifier_for_log = str(user_doc["_id"]) if user_doc.get("_id") else current_user_email
        logger.info(f"User {user_identifier_for_log} performing find-matches.")

        if not data:
            raise HTTPException(status_code=400, detail="No JSON data provided")

        organ_data = data.get('organData', {})
        recipients = data.get('recipients', [])

        # Simulate loading sample data if no recipients provided
        if not recipients:
            # This section would ideally call a service or use AI_ENGINE_URL
            # For now, using placeholder logic
            # _, recipients = call_external_service(f"{AI_ENGINE_URL}/load_sample_data", method="GET")
            pass # Assuming recipients might be empty if not provided

        donor = {
            'organType': organ_data.get('requiredOrgan', organ_data.get('organType', 'heart')),
            'bloodType': organ_data.get('bloodType', 'O+'),
            'age': organ_data.get('age', 30),
            'location': organ_data.get('location', 'Unknown')
        }

        # Simulate AI matching call
        # In a real setup, this would be:
        # response = await call_external_service(
        #     f"{AI_ENGINE_URL}/find_best_matches",
        #     method="POST",
        #     json_data={'donor': donor, 'recipients': recipients, 'top_n': 10}
        # )
        # matches = response.get("matches", [])
        matches = [ # Placeholder matches
            {"recipient": {"id": 1, "name": "Test Recipient 1"}, "match_score": 95, "age": 35, "bloodType": "O+"},
            {"recipient": {"id": 2, "name": "Test Recipient 2"}, "match_score": 92, "age": 28, "bloodType": "A-"},
        ]

        # Database interaction (e.g., saving matches) is removed as per plan for MongoDB migration.
        # log_activity would be replaced by logger.info (e.g., logger.info(f"AI matching for user {user_id}..."))
        # logger.info(f"User {user_identifier_for_log} performed AI matching for {donor['organType']}, found {len(matches)} matches.")

        high_quality_matches = [m for m in matches if m.get('match_score', 0) >= 90]

        return {
            'matches': matches,
            'total_matches': len(matches),
            'high_quality_matches': len(high_quality_matches),
            'search_criteria': donor,
            'ai_engine_version': 'Gemini-1.5-Flash-FastAPI' # Updated version string
        }

    except HTTPException:
        raise # Re-raise HTTPException directly
    except Exception as e:
        # logger.error(f"AI matching failed for user {user_identifier_for_log}: {str(e)}")
        raise HTTPException(status_code=500, detail=f'AI matching failed: {str(e)}')

@router.post('/analyze-compatibility')
async def analyze_compatibility(
    data: dict,
    current_user_email: str = Depends(verify_token)
):
    """Detailed compatibility analysis between donor and recipient"""
    try:
        user_doc = await db.users.find_one({"email": current_user_email})
        if not user_doc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found or not authorized")

        user_identifier_for_log = str(user_doc["_id"]) if user_doc.get("_id") else current_user_email
        logger.info(f"User {user_identifier_for_log} performing analyze-compatibility.")

        if not data:
            raise HTTPException(status_code=400, detail="No JSON data provided")

        donor_data = data.get('donorData', {})
        recipient_data = data.get('recipientData', {})

        # Simulate AI compatibility score call
        # In a real setup, this would be:
        # response = await call_external_service(
        #     f"{AI_ENGINE_URL}/get_compatibility_score",
        #     method="POST",
        #     json_data={'donor': donor_data, 'recipient': recipient_data}
        # )
        # compatibility_score = response.get("score", 85) # Default if not found
        compatibility_score = 85 # Placeholder score

        factors = [
            {
                'factor': 'Blood Type Compatibility',
                'score': 100 if donor_data.get('bloodType') == recipient_data.get('bloodType') else 85,
                'weight': 0.3,
                'description': 'Blood type matching between donor and recipient'
            },
            {
                'factor': 'Age Compatibility',
                'score': max(60, 100 - abs(donor_data.get('age', 30) - recipient_data.get('age', 30)) * 2),
                'weight': 0.2,
                'description': 'Age difference impact on transplant success'
            },
            {
                'factor': 'HLA Tissue Matching',
                'score': 80 + (compatibility_score - 80) * 0.5,  # Simulated HLA matching
                'weight': 0.4,
                'description': 'Human Leukocyte Antigen tissue compatibility'
            },
            {
                'factor': 'Geographic Distance',
                'score': 90,  # This would be calculated based on actual locations
                'weight': 0.1,
                'description': 'Distance between donor and recipient locations'
            }
        ]

        weighted_score = sum(factor['score'] * factor['weight'] for factor in factors)

        # log_activity would be replaced by logger.info
        # logger.info(f"User {user_identifier_for_log} performed compatibility analysis for donor {donor_data.get('id', 'N/A')} and recipient {recipient_data.get('id', 'N/A')}: {weighted_score:.1f}%")

        return {
            'compatibility_score': round(weighted_score, 1),
            'factors': factors,
            'recommendation': 'Highly Compatible' if weighted_score >= 85 else 'Compatible' if weighted_score >= 70 else 'Low Compatibility',
            'analysis_timestamp': datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise # Re-raise HTTPException directly
    except Exception as e:
        # logger.error(f"Compatibility analysis failed for user {user_identifier_for_log}: {str(e)}")
        raise HTTPException(status_code=500, detail=f'Compatibility analysis failed: {str(e)}')

# End of file
