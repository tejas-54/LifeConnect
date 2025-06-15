from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime, timedelta, timezone
import json

from models import db, User, OrganMatch, ActivityLog, HealthCard, TransportPlan
from utils import log_activity, create_response, update_metric

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/recent-activity', methods=['GET'])
@jwt_required()
def get_recent_activity():
    """Get recent system activity with filtering - PROTECTED"""
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)  # Convert string to int
        user = db.session.get(User, user_id)
        
        # Get query parameters
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 activities
        severity = request.args.get('severity')  # Filter by severity
        action = request.args.get('action')  # Filter by action type
        
        # Build query
        query = ActivityLog.query
        
        if severity:
            query = query.filter_by(severity=severity)
        
        if action:
            query = query.filter(ActivityLog.action.like(f'%{action}%'))
        
        # For non-regulators, only show their own activities
        if user and user.user_type != 'regulator':
            query = query.filter_by(user_id=user_id)
        
        activities = query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()
        
        activity_data = [
            {
                'id': activity.id,
                'action': activity.action,
                'description': activity.description,
                'timestamp': activity.timestamp.isoformat(),
                'user_id': activity.user_id,
                'severity': activity.severity,
                'ip_address': activity.ip_address,
                'meta_data': json.loads(activity.meta_data) if activity.meta_data else None
            } for activity in activities
        ]
        
        return create_response(True, {
            'activities': activity_data,
            'total_count': len(activity_data),
            'filters_applied': {
                'severity': severity,
                'action': action,
                'limit': limit
            }
        })
    
    except Exception as e:
        return create_response(False, error=f'Failed to get recent activity: {str(e)}', status_code=500)

# Keep other dashboard routes as they were (stats and system-health are public)
@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """Get comprehensive dashboard statistics - PUBLIC"""
    try:
        # Check if user is authenticated (optional)
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id_str = get_jwt_identity()
            user_id = int(user_id_str) if user_id_str else None
        except:
            pass  # No authentication required
        
        # Get basic counts
        total_users = User.query.count()
        total_donors = User.query.filter_by(user_type='donor').count()
        total_hospitals = User.query.filter_by(user_type='hospital').count()
        total_regulators = User.query.filter_by(user_type='regulator').count()
        total_health_cards = HealthCard.query.filter_by(is_active=True).count()
        total_matches = OrganMatch.query.count()
        successful_matches = OrganMatch.query.filter_by(status='completed').count()
        active_transports = TransportPlan.query.filter(
            TransportPlan.status.in_(['planned', 'in_progress'])
        ).count()
        
        # Get recent activity
        recent_activities = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()
        
        # Calculate monthly data for the last 6 months
        monthly_data = []
        for i in range(6):
            month_start = datetime.now(timezone.utc).replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            month_donations = OrganMatch.query.filter(
                OrganMatch.match_timestamp >= month_start,
                OrganMatch.match_timestamp < month_end
            ).count()
            
            monthly_data.append({
                'month': month_start.strftime('%b'),
                'donations': month_donations
            })
        
        monthly_data.reverse()
        
        # Organ distribution analysis
        organ_counts = {}
        matches = OrganMatch.query.all()
        for match in matches:
            organ_type = match.organ_type
            organ_counts[organ_type] = organ_counts.get(organ_type, 0) + 1
        
        organ_distribution = [
            {'name': organ_type.title(), 'value': count}
            for organ_type, count in organ_counts.items()
        ]
        
        # If no data, provide sample data for demo
        if not organ_distribution:
            organ_distribution = [
                {'name': 'Heart', 'value': 30},
                {'name': 'Liver', 'value': 25},
                {'name': 'Kidney', 'value': 35},
                {'name': 'Lung', 'value': 10}
            ]
        
        # Build stats response
        stats_data = {
            'totalUsers': total_users,
            'totalDonors': total_donors,
            'totalHospitals': total_hospitals,
            'totalRegulators': total_regulators,
            'totalHealthCards': total_health_cards,
            'totalMatches': total_matches,
            'successfulMatches': successful_matches,
            'activeTransports': active_transports,
            'monthlyDonations': monthly_data,
            'organDistribution': organ_distribution,
            'recentActivities': [
                {
                    'action': activity.action,
                    'description': activity.description,
                    'timestamp': activity.timestamp.isoformat(),
                    'user_id': activity.user_id,
                    'severity': activity.severity
                } for activity in recent_activities
            ],
            'authenticated': user_id is not None
        }
        
        # Log dashboard access if authenticated
        if user_id:
            user = db.session.get(User, user_id)
            if user:
                log_activity(user_id, 'dashboard_access', f"Dashboard stats accessed by {user.user_type}")
        
        return create_response(True, stats_data)
    
    except Exception as e:
        return create_response(False, error=f'Failed to get dashboard stats: {str(e)}', status_code=500)

@dashboard_bp.route('/system-health', methods=['GET'])
def get_system_health():
    """Get comprehensive system health status - PUBLIC"""
    try:
        # Test component health (these would be real checks in production)
        health_status = {
            'database': True,  # If we reach here, database is working
            'blockchain': True,  # Would test actual blockchain connection
            'ipfs': True,       # Would test IPFS connectivity
            'ai_engine': True,  # Would test AI engine
            'logistics': True   # Would test logistics engine
        }
        
        # Calculate overall health
        healthy_components = sum(health_status.values())
        total_components = len(health_status)
        health_percentage = (healthy_components / total_components) * 100
        
        # Determine overall status
        if health_percentage >= 90:
            overall_status = 'healthy'
        elif health_percentage >= 70:
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'
        
        # Update metrics
        update_metric('system_health_percentage', health_percentage)
        
        return create_response(True, {
            'status': overall_status,
            'health_percentage': health_percentage,
            'components': health_status,
            'last_check': datetime.now(timezone.utc).isoformat(),
            'uptime_hours': 24,  # This would be calculated from actual uptime
            'version': '1.0.0'
        })
    
    except Exception as e:
        return create_response(False, {
            'status': 'error',
            'components': {comp: False for comp in ['database', 'blockchain', 'ipfs', 'ai_engine', 'logistics']},
            'error': str(e)
        }, status_code=500)

@dashboard_bp.route('/demo', methods=['GET'])
def get_demo_data():
    """Get demo data for testing - PUBLIC"""
    return create_response(True, {
        'message': 'LifeConnect Backend Demo Data',
        'sample_endpoints': {
            'health_check': '/api/health',
            'system_health': '/api/dashboard/system-health',
            'dashboard_stats': '/api/dashboard/stats',
            'wallet_login': '/api/auth/wallet-login',
            'test_login': '/api/auth/test-login',
            'blockchain_info': '/api/blockchain/network-info'
        },
        'sample_wallet_login': {
            'url': '/api/auth/wallet-login',
            'method': 'POST',
            'data': {
                'account_index': 0,
                'user_type': 'donor'
            }
        },
        'available_accounts': [
            {
                'index': 0,
                'address': '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266',
                'name': 'Account #0'
            },
            {
                'index': 1,
                'address': '0x70997970C51812dc3A010C7d01b50e0d17dc79C8',
                'name': 'Account #1'
            },
            {
                'index': 2,
                'address': '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC',
                'name': 'Account #2'
            },
            {
                'index': 3,
                'address': '0x90F79bf6EB2c4f870365E785982E1f101E93b906',
                'name': 'Account #3'
            }
        ],
        'sample_health_card': {
            'url': '/api/health-cards/generate',
            'method': 'POST',
            'requires_auth': True,
            'data': {
                'name': 'John Doe',
                'age': 30,
                'bloodType': 'O+',
                'donorStatus': True,
                'organTypes': ['heart', 'liver']
            }
        }
    })
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime, timedelta, timezone
import json

from models import db, User, OrganMatch, ActivityLog, HealthCard, TransportPlan
from utils import log_activity, create_response, update_metric

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/recent-activity', methods=['GET'])
@jwt_required()
def get_recent_activity():
    """Get recent system activity with filtering - PROTECTED"""
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)  # Convert string to int
        user = db.session.get(User, user_id)
        
        # Get query parameters
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 activities
        severity = request.args.get('severity')  # Filter by severity
        action = request.args.get('action')  # Filter by action type
        
        # Build query
        query = ActivityLog.query
        
        if severity:
            query = query.filter_by(severity=severity)
        
        if action:
            query = query.filter(ActivityLog.action.like(f'%{action}%'))
        
        # For non-regulators, only show their own activities
        if user and user.user_type != 'regulator':
            query = query.filter_by(user_id=user_id)
        
        activities = query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()
        
        activity_data = [
            {
                'id': activity.id,
                'action': activity.action,
                'description': activity.description,
                'timestamp': activity.timestamp.isoformat(),
                'user_id': activity.user_id,
                'severity': activity.severity,
                'ip_address': activity.ip_address,
                'meta_data': json.loads(activity.meta_data) if activity.meta_data else None
            } for activity in activities
        ]
        
        return create_response(True, {
            'activities': activity_data,
            'total_count': len(activity_data),
            'filters_applied': {
                'severity': severity,
                'action': action,
                'limit': limit
            }
        })
    
    except Exception as e:
        return create_response(False, error=f'Failed to get recent activity: {str(e)}', status_code=500)

# Keep other dashboard routes as they were (stats and system-health are public)
@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """Get comprehensive dashboard statistics - PUBLIC"""
    try:
        # Check if user is authenticated (optional)
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id_str = get_jwt_identity()
            user_id = int(user_id_str) if user_id_str else None
        except:
            pass  # No authentication required
        
        # Get basic counts
        total_users = User.query.count()
        total_donors = User.query.filter_by(user_type='donor').count()
        total_hospitals = User.query.filter_by(user_type='hospital').count()
        total_regulators = User.query.filter_by(user_type='regulator').count()
        total_health_cards = HealthCard.query.filter_by(is_active=True).count()
        total_matches = OrganMatch.query.count()
        successful_matches = OrganMatch.query.filter_by(status='completed').count()
        active_transports = TransportPlan.query.filter(
            TransportPlan.status.in_(['planned', 'in_progress'])
        ).count()
        
        # Get recent activity
        recent_activities = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()
        
        # Calculate monthly data for the last 6 months
        monthly_data = []
        for i in range(6):
            month_start = datetime.now(timezone.utc).replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            month_donations = OrganMatch.query.filter(
                OrganMatch.match_timestamp >= month_start,
                OrganMatch.match_timestamp < month_end
            ).count()
            
            monthly_data.append({
                'month': month_start.strftime('%b'),
                'donations': month_donations
            })
        
        monthly_data.reverse()
        
        # Organ distribution analysis
        organ_counts = {}
        matches = OrganMatch.query.all()
        for match in matches:
            organ_type = match.organ_type
            organ_counts[organ_type] = organ_counts.get(organ_type, 0) + 1
        
        organ_distribution = [
            {'name': organ_type.title(), 'value': count}
            for organ_type, count in organ_counts.items()
        ]
        
        # If no data, provide sample data for demo
        if not organ_distribution:
            organ_distribution = [
                {'name': 'Heart', 'value': 30},
                {'name': 'Liver', 'value': 25},
                {'name': 'Kidney', 'value': 35},
                {'name': 'Lung', 'value': 10}
            ]
        
        # Build stats response
        stats_data = {
            'totalUsers': total_users,
            'totalDonors': total_donors,
            'totalHospitals': total_hospitals,
            'totalRegulators': total_regulators,
            'totalHealthCards': total_health_cards,
            'totalMatches': total_matches,
            'successfulMatches': successful_matches,
            'activeTransports': active_transports,
            'monthlyDonations': monthly_data,
            'organDistribution': organ_distribution,
            'recentActivities': [
                {
                    'action': activity.action,
                    'description': activity.description,
                    'timestamp': activity.timestamp.isoformat(),
                    'user_id': activity.user_id,
                    'severity': activity.severity
                } for activity in recent_activities
            ],
            'authenticated': user_id is not None
        }
        
        # Log dashboard access if authenticated
        if user_id:
            user = db.session.get(User, user_id)
            if user:
                log_activity(user_id, 'dashboard_access', f"Dashboard stats accessed by {user.user_type}")
        
        return create_response(True, stats_data)
    
    except Exception as e:
        return create_response(False, error=f'Failed to get dashboard stats: {str(e)}', status_code=500)

@dashboard_bp.route('/system-health', methods=['GET'])
def get_system_health():
    """Get comprehensive system health status - PUBLIC"""
    try:
        # Test component health (these would be real checks in production)
        health_status = {
            'database': True,  # If we reach here, database is working
            'blockchain': True,  # Would test actual blockchain connection
            'ipfs': True,       # Would test IPFS connectivity
            'ai_engine': True,  # Would test AI engine
            'logistics': True   # Would test logistics engine
        }
        
        # Calculate overall health
        healthy_components = sum(health_status.values())
        total_components = len(health_status)
        health_percentage = (healthy_components / total_components) * 100
        
        # Determine overall status
        if health_percentage >= 90:
            overall_status = 'healthy'
        elif health_percentage >= 70:
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'
        
        # Update metrics
        update_metric('system_health_percentage', health_percentage)
        
        return create_response(True, {
            'status': overall_status,
            'health_percentage': health_percentage,
            'components': health_status,
            'last_check': datetime.now(timezone.utc).isoformat(),
            'uptime_hours': 24,  # This would be calculated from actual uptime
            'version': '1.0.0'
        })
    
    except Exception as e:
        return create_response(False, {
            'status': 'error',
            'components': {comp: False for comp in ['database', 'blockchain', 'ipfs', 'ai_engine', 'logistics']},
            'error': str(e)
        }, status_code=500)

@dashboard_bp.route('/demo', methods=['GET'])
def get_demo_data():
    """Get demo data for testing - PUBLIC"""
    return create_response(True, {
        'message': 'LifeConnect Backend Demo Data',
        'sample_endpoints': {
            'health_check': '/api/health',
            'system_health': '/api/dashboard/system-health',
            'dashboard_stats': '/api/dashboard/stats',
            'wallet_login': '/api/auth/wallet-login',
            'test_login': '/api/auth/test-login',
            'blockchain_info': '/api/blockchain/network-info'
        },
        'sample_wallet_login': {
            'url': '/api/auth/wallet-login',
            'method': 'POST',
            'data': {
                'account_index': 0,
                'user_type': 'donor'
            }
        },
        'available_accounts': [
            {
                'index': 0,
                'address': '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266',
                'name': 'Account #0'
            },
            {
                'index': 1,
                'address': '0x70997970C51812dc3A010C7d01b50e0d17dc79C8',
                'name': 'Account #1'
            },
            {
                'index': 2,
                'address': '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC',
                'name': 'Account #2'
            },
            {
                'index': 3,
                'address': '0x90F79bf6EB2c4f870365E785982E1f101E93b906',
                'name': 'Account #3'
            }
        ],
        'sample_health_card': {
            'url': '/api/health-cards/generate',
            'method': 'POST',
            'requires_auth': True,
            'data': {
                'name': 'John Doe',
                'age': 30,
                'bloodType': 'O+',
                'donorStatus': True,
                'organTypes': ['heart', 'liver']
            }
        }
    })
