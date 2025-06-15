from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from datetime import datetime, timedelta, timezone

from models import db, User, TransportPlan
from utils import log_activity, create_response

logistics_bp = Blueprint('logistics', __name__)

@logistics_bp.route('/create-transport-plan', methods=['POST'])
@jwt_required()
def create_transport_plan():
    """Create comprehensive transport plan"""
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)  # Convert string to int
        
        if not request.is_json:
            return create_response(False, error='Content-Type must be application/json', status_code=400)
        
        data = request.get_json()
        if not data:
            return create_response(False, error='No JSON data provided', status_code=400)
        
        organ_data = data.get('organData', {})
        pickup_location = data.get('pickupLocation', {})
        delivery_location = data.get('deliveryLocation', {})
        
        # Use logistics engine from component service
        logistics_engine = logistics_bp.component_service.logistics_engine
        
        transport_plan = logistics_engine.create_transport_plan(
            organ_data,
            pickup_location.get('name', 'Unknown Pickup'),
            delivery_location.get('name', 'Unknown Delivery')
        )
        
        transport_id = f"TRANSPORT_{int(datetime.now(timezone.utc).timestamp())}_{user_id}"
        
        transport_db = TransportPlan(
            transport_id=transport_id,
            organ_type=organ_data.get('organType', 'unknown'),
            pickup_location=json.dumps(pickup_location),
            delivery_location=json.dumps(delivery_location),
            vehicle_type=transport_plan.get('vehicle', {}).get('type', 'ambulance'),
            route_data=json.dumps(transport_plan.get('route', {})),
            estimated_duration=transport_plan.get('route', {}).get('duration_minutes', 60),
            estimated_distance=transport_plan.get('route', {}).get('distance_km', 10)
        )
        db.session.add(transport_db)
        db.session.commit()
        
        log_activity(user_id, 'transport_plan_created', f"Transport plan created for {organ_data.get('organType', 'unknown')} organ")
        
        # Notify via WebSocket (import here to avoid circular imports)
        try:
            from app import socketio
            socketio.emit('notification', {
                'type': 'transport_created',
                'title': 'Transport Plan Created',
                'message': f'Transport plan for {organ_data.get("organType", "organ")} has been created',
                'data': {'transport_id': transport_id},
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, room=f"user_{user_id}")
        except ImportError:
            pass  # WebSocket not available
        
        return create_response(True, {
            'transport_id': transport_id,
            'transport_plan': transport_plan,
            'estimated_duration_minutes': transport_db.estimated_duration,
            'estimated_distance_km': transport_db.estimated_distance,
            'vehicle_type': transport_db.vehicle_type,
            'status': 'planned'
        })
    
    except Exception as e:
        return create_response(False, error=f'Transport plan creation failed: {str(e)}', status_code=500)

@logistics_bp.route('/active-transports', methods=['GET'])
@jwt_required()
def get_active_transports():
    """Get all active transport plans"""
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)  # Convert string to int
        user = db.session.get(User, user_id)
        
        if user and user.user_type == 'regulator':
            transports = TransportPlan.query.filter(TransportPlan.status.in_(['planned', 'in_progress'])).all()
        else:
            transports = TransportPlan.query.filter(TransportPlan.status.in_(['planned', 'in_progress'])).limit(10).all()
        
        transport_data = []
        for transport in transports:
            route_data = json.loads(transport.route_data) if transport.route_data else {}
            pickup_data = json.loads(transport.pickup_location) if transport.pickup_location else {}
            delivery_data = json.loads(transport.delivery_location) if transport.delivery_location else {}
            
            transport_info = {
                'transport_id': transport.transport_id,
                'organ_type': transport.organ_type,
                'vehicle_type': transport.vehicle_type,
                'status': transport.status,
                'pickup_location': pickup_data,
                'delivery_location': delivery_data,
                'estimated_duration': transport.estimated_duration,
                'estimated_distance': transport.estimated_distance,
                'created_at': transport.created_at.isoformat(),
                'route_progress': 0,
                'current_temperature': '4°C',
                'estimated_arrival': (datetime.now(timezone.utc) + timedelta(minutes=transport.estimated_duration)).isoformat(),
                'alerts': []
            }
            
            if transport.status == 'in_progress' and transport.started_at:
                elapsed_minutes = (datetime.now(timezone.utc) - transport.started_at).total_seconds() / 60
                transport_info['route_progress'] = min(95, int((elapsed_minutes / transport.estimated_duration) * 100))
            
            transport_data.append(transport_info)
        
        return create_response(True, transport_data)
    
    except Exception as e:
        return create_response(False, error=f'Failed to get active transports: {str(e)}', status_code=500)

@logistics_bp.route('/track-transport/<transport_id>', methods=['GET'])
@jwt_required()
def track_transport(transport_id):
    """Track specific transport"""
    try:
        transport = TransportPlan.query.filter_by(transport_id=transport_id).first()
        
        if not transport:
            return create_response(False, error='Transport not found', status_code=404)
        
        if transport.status == 'in_progress' and transport.started_at:
            elapsed_minutes = (datetime.now(timezone.utc) - transport.started_at).total_seconds() / 60
            progress = min(95, int((elapsed_minutes / transport.estimated_duration) * 100))
        else:
            progress = 0
        
        tracking_data = {
            'transport_id': transport.transport_id,
            'status': transport.status,
            'progress': progress,
            'current_location': {'lat': 40.7128, 'lng': -74.0060},  # Mock GPS data
            'temperature': '4°C',
            'humidity': '65%',
            'last_update': datetime.now(timezone.utc).isoformat(),
            'estimated_arrival': (transport.created_at + timedelta(minutes=transport.estimated_duration)).isoformat(),
            'route_data': json.loads(transport.route_data) if transport.route_data else {}
        }
        
        return create_response(True, tracking_data)
    
    except Exception as e:
        return create_response(False, error=f'Transport tracking failed: {str(e)}', status_code=500)
