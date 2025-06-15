from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from datetime import datetime, timezone

from models import db, OrganMatch
from utils import log_activity, create_response

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/find-matches', methods=['POST'])
@jwt_required()
def find_organ_matches():
    """Find organ matches using AI"""
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)  # Convert string to int
        
        if not request.is_json:
            return create_response(False, error='Content-Type must be application/json', status_code=400)
        
        data = request.get_json()
        if not data:
            return create_response(False, error='No JSON data provided', status_code=400)
        
        organ_data = data.get('organData', {})
        recipients = data.get('recipients', [])
        
        # Use sample data if no recipients provided
        if not recipients:
            try:
                ai_engine = ai_bp.component_service.ai_engine
                if hasattr(ai_bp.component_service, 'load_sample_data'):
                    _, recipients = ai_bp.component_service.load_sample_data()
                else:
                    recipients = []
            except:
                recipients = []
        
        # Convert organ_data to donor format for matching
        donor = {
            'organType': organ_data.get('requiredOrgan', organ_data.get('organType', 'heart')),
            'bloodType': organ_data.get('bloodType', 'O+'),
            'age': organ_data.get('age', 30),
            'location': organ_data.get('location', 'Unknown')
        }
        
        # Perform AI matching
        ai_engine = ai_bp.component_service.ai_engine
        matches = ai_engine.find_best_matches(donor, recipients, top_n=10)
        
        # Save matches to database
        for match in matches:
            if match.get('match_score', 0) >= 80:  # Only save high-quality matches
                organ_match = OrganMatch(
                    user_id=user_id,
                    donor_address=donor.get('address', 'unknown'),
                    recipient_address=match.get('recipient', {}).get('address', 'unknown'),
                    organ_type=donor['organType'],
                    compatibility_score=match.get('match_score', 0),
                    ai_analysis=json.dumps(match)
                )
                db.session.add(organ_match)
        
        db.session.commit()
        
        log_activity(user_id, 'ai_matching', f"AI matching performed for {donor['organType']} organ, found {len(matches)} matches")
        
        # Count high-quality matches
        high_quality_matches = [m for m in matches if m.get('match_score', 0) >= 90]
        
        return create_response(True, {
            'matches': matches,
            'total_matches': len(matches),
            'high_quality_matches': len(high_quality_matches),
            'search_criteria': donor,
            'ai_engine_version': 'Gemini-1.5-Flash'
        })
    
    except Exception as e:
        user_id = None
        try:
            user_id_str = get_jwt_identity()
            user_id = int(user_id_str) if user_id_str else None
        except:
            pass
        log_activity(user_id, 'ai_matching_error', f"AI matching failed: {str(e)}", severity='error')
        return create_response(False, error=f'AI matching failed: {str(e)}', status_code=500)

@ai_bp.route('/analyze-compatibility', methods=['POST'])
@jwt_required()
def analyze_compatibility():
    """Detailed compatibility analysis between donor and recipient"""
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)  # Convert string to int
        
        if not request.is_json:
            return create_response(False, error='Content-Type must be application/json', status_code=400)
        
        data = request.get_json()
        if not data:
            return create_response(False, error='No JSON data provided', status_code=400)
        
        donor_data = data.get('donorData', {})
        recipient_data = data.get('recipientData', {})
        
        # Perform detailed compatibility analysis
        ai_engine = ai_bp.component_service.ai_engine
        compatibility_score = ai_engine.get_compatibility_score(donor_data, recipient_data) if hasattr(ai_engine, 'get_compatibility_score') else 85
        
        # Calculate detailed factors
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
        
        # Calculate weighted score
        weighted_score = sum(factor['score'] * factor['weight'] for factor in factors)
        
        log_activity(user_id, 'compatibility_analysis', f"Compatibility analysis performed: {weighted_score:.1f}% compatibility")
        
        return create_response(True, {
            'compatibility_score': round(weighted_score, 1),
            'factors': factors,
            'recommendation': 'Highly Compatible' if weighted_score >= 85 else 'Compatible' if weighted_score >= 70 else 'Low Compatibility',
            'analysis_timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    except Exception as e:
        return create_response(False, error=f'Compatibility analysis failed: {str(e)}', status_code=500)
