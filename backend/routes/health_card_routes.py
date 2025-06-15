from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import os
import time
from datetime import datetime, timezone

from models import db, User, HealthCard
from utils import log_activity, create_response

health_card_bp = Blueprint('health_card', __name__)

@health_card_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_health_card():
    """Generate comprehensive health card"""
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)  # Convert string to int
        user = db.session.get(User, user_id)
        
        if not user:
            return create_response(False, error='User not found', status_code=404)
        
        # Validate JSON data
        if not request.is_json:
            return create_response(False, error='Content-Type must be application/json', status_code=400)
        
        patient_data = request.get_json()
        if not patient_data:
            return create_response(False, error='No JSON data provided', status_code=400)
        
        # Validate required fields
        required_fields = ['name', 'age', 'bloodType']
        for field in required_fields:
            if field not in patient_data:
                return create_response(False, error=f'Missing required field: {field}', status_code=400)
        
        # Add user data to patient data
        patient_data.update({
            'user_id': user_id,
            'wallet_address': user.wallet_address,
            'generated_by': user.name or user.wallet_address
        })
        
        # Generate health card using the health card generator
        health_card_generator = health_card_bp.component_service.health_card_generator
        result = health_card_generator.complete_health_card_workflow(
            patient_data,
            generate_pdf=True,
            generate_image=True,
            upload_to_ipfs=True
        )
        
        # Save to database
        health_card = HealthCard(
            user_id=user_id,
            patient_id=result['health_card'].get('patientId', f"PATIENT_{int(time.time())}"),
            card_data=json.dumps(result['health_card']),
            ipfs_cid=result['ipfs_result']['cid'] if result.get('ipfs_result') else None,
            pdf_path=result.get('pdf_path'),
            image_path=result.get('image_path')
        )
        db.session.add(health_card)
        db.session.commit()
        
        log_activity(user_id, 'health_card_generated', f"Health card generated for {patient_data.get('name', 'Unknown')}")
        
        return create_response(True, {
            'health_card': result['health_card'],
            'patient_id': health_card.patient_id,
            'files': {
                'json': os.path.basename(result['json_path']) if result.get('json_path') else None,
                'pdf': os.path.basename(result['pdf_path']) if result.get('pdf_path') else None,
                'image': os.path.basename(result['image_path']) if result.get('image_path') else None
            },
            'ipfs': {
                'cid': result['ipfs_result']['cid'] if result.get('ipfs_result') else None,
                'url': result['ipfs_result']['url'] if result.get('ipfs_result') else None
            }
        })
    
    except Exception as e:
        print(f"Health card generation error: {str(e)}")  # Debug print
        user_id = None
        try:
            user_id_str = get_jwt_identity()
            user_id = int(user_id_str) if user_id_str else None
        except:
            pass
        log_activity(user_id, 'health_card_error', f"Health card generation failed: {str(e)}", severity='error')
        return create_response(False, error=f'Health card generation failed: {str(e)}', status_code=500)

@health_card_bp.route('/list', methods=['GET'])
@jwt_required()
def list_health_cards():
    """List user's health cards"""
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)  # Convert string to int
        health_cards = HealthCard.query.filter_by(user_id=user_id, is_active=True).order_by(HealthCard.created_at.desc()).all()
        
        cards_data = []
        for card in health_cards:
            card_data = {
                'id': card.id,
                'patient_id': card.patient_id,
                'card_data': json.loads(card.card_data),
                'ipfs_cid': card.ipfs_cid,
                'created_at': card.created_at.isoformat(),
                'updated_at': card.updated_at.isoformat()
            }
            cards_data.append(card_data)
        
        return create_response(True, cards_data)
    
    except Exception as e:
        print(f"List health cards error: {str(e)}")  # Debug print
        return create_response(False, error=f'Failed to list health cards: {str(e)}', status_code=500)

@health_card_bp.route('/<patient_id>', methods=['GET'])
@jwt_required()
def get_health_card(patient_id):
    """Get specific health card"""
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)  # Convert string to int
        health_card = HealthCard.query.filter_by(patient_id=patient_id, is_active=True).first()
        
        if not health_card:
            return create_response(False, error='Health card not found', status_code=404)
        
        # Check if user owns this card or is authorized
        user = db.session.get(User, user_id)
        if health_card.user_id != user_id and user.user_type not in ['hospital', 'regulator']:
            return create_response(False, error='Unauthorized access', status_code=403)
        
        return create_response(True, {
            'id': health_card.id,
            'patient_id': health_card.patient_id,
            'card_data': json.loads(health_card.card_data),
            'ipfs_cid': health_card.ipfs_cid,
            'created_at': health_card.created_at.isoformat(),
            'updated_at': health_card.updated_at.isoformat()
        })
    
    except Exception as e:
        print(f"Get health card error: {str(e)}")  # Debug print
        return create_response(False, error=f'Failed to get health card: {str(e)}', status_code=500)
