import json
import logging
from datetime import datetime, timezone
from flask import request, jsonify
from models import db, ActivityLog, SystemMetrics, User

logger = logging.getLogger(__name__)

def get_user_id_from_jwt():
    """Get integer user ID from JWT token (handles string conversion)"""
    from flask_jwt_extended import get_jwt_identity
    try:
        user_id_str = get_jwt_identity()
        if user_id_str:
            return int(user_id_str)
        return None
    except (ValueError, TypeError):
        return None

def log_activity(user_id, action, description, meta_data=None, severity='info'):
    """Log user activity with comprehensive details"""
    try:
        activity = ActivityLog(
            user_id=user_id,
            action=action,
            description=description,
            meta_data=json.dumps(meta_data) if meta_data else None,
            ip_address=request.remote_addr if request else None,
            user_agent=request.user_agent.string if request and request.user_agent else None,
            severity=severity
        )
        db.session.add(activity)
        db.session.commit()
        logger.info(f"Activity logged: {action} - {description}")
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")

def update_metric(metric_name, value, data=None):
    """Update system metrics"""
    try:
        metric = SystemMetrics(
            metric_name=metric_name,
            metric_value=value,
            metric_data=json.dumps(data) if data else None
        )
        db.session.add(metric)
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to update metric: {e}")

def get_user_by_wallet(wallet_address):
    """Get user by wallet address"""
    return User.query.filter_by(wallet_address=wallet_address.lower()).first()

def create_response(success=True, data=None, message=None, error=None, status_code=200):
    """Standardized API response format"""
    response = {
        'success': success,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'data': data,
        'message': message,
        'error': error
    }
    return jsonify(response), status_code
