from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity, verify_jwt_in_request
from datetime import datetime, timezone
import json

from models import db, User
from utils import log_activity, get_user_by_wallet, create_response

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user with wallet address"""
    try:
        # Get JSON data from request
        if not request.is_json:
            return create_response(False, error='Content-Type must be application/json', status_code=400)
        
        data = request.get_json()
        if not data:
            return create_response(False, error='No JSON data provided', status_code=400)
        
        wallet_address = data.get('wallet_address', '').lower().strip()
        user_type = data.get('user_type', 'donor')
        email = data.get('email', '').strip()
        name = data.get('name', '').strip()
        
        # Validate required fields
        if not wallet_address:
            return create_response(False, error='Wallet address is required', status_code=400)
        
        # Validate wallet address format
        if not (wallet_address.startswith('0x') and len(wallet_address) == 42):
            return create_response(False, error='Invalid wallet address format. Must be 42 characters starting with 0x', status_code=400)
        
        # Validate user type
        valid_user_types = ['donor', 'hospital', 'regulator']
        if user_type not in valid_user_types:
            return create_response(False, error=f'Invalid user type. Must be one of: {", ".join(valid_user_types)}', status_code=400)
        
        # Find or create user
        user = get_user_by_wallet(wallet_address)
        if not user:
            # Create new user
            user = User(
                wallet_address=wallet_address,
                user_type=user_type,
                email=email if email else None,
                name=name if name else None
            )
            db.session.add(user)
            db.session.commit()
            log_activity(user.id, 'user_registration', f'New {user_type} registered with wallet {wallet_address}')
        else:
            # Update existing user
            user.last_login = datetime.now(timezone.utc)
            if email and not user.email:
                user.email = email
            if name and not user.name:
                user.name = name
            db.session.commit()
        
        # Create JWT token with STRING subject (FIXED)
        additional_claims = {
            'user_type': user.user_type,
            'wallet_address': user.wallet_address,
            'is_active': user.is_active
        }
        
        access_token = create_access_token(
            identity=str(user.id),  # CONVERT TO STRING
            additional_claims=additional_claims
        )
        
        log_activity(user.id, 'login', f'{user_type} logged in successfully')
        
        return create_response(True, {
            'access_token': access_token,
            'token_type': 'Bearer',
            'user': {
                'id': user.id,
                'wallet_address': user.wallet_address,
                'email': user.email,
                'name': user.name,
                'user_type': user.user_type,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
        })
    
    except Exception as e:
        print(f"Login error: {str(e)}")  # Debug print
        return create_response(False, error=f'Login failed: {str(e)}', status_code=500)

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        user_id_str = get_jwt_identity()
        if not user_id_str:
            return create_response(False, error='Invalid token: no user ID found', status_code=401)
        
        # Convert string back to integer (FIXED)
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            return create_response(False, error='Invalid user ID in token', status_code=401)
        
        user = db.session.get(User, user_id)
        if not user:
            return create_response(False, error='User not found', status_code=404)
        
        return create_response(True, {
            'id': user.id,
            'wallet_address': user.wallet_address,
            'email': user.email,
            'name': user.name,
            'user_type': user.user_type,
            'phone': user.phone,
            'address': user.address,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'is_active': user.is_active,
            'profile_data': json.loads(user.profile_data) if user.profile_data else {}
        })
    
    except Exception as e:
        print(f"Profile error: {str(e)}")  # Debug print
        return create_response(False, error=f'Profile fetch failed: {str(e)}', status_code=500)

@auth_bp.route('/test-login', methods=['POST'])
def test_login():
    """Quick test login for demo purposes - FIXED"""
    try:
        # Create a test user and login
        test_data = {
            'wallet_address': '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266',  # Use Account #0
            'user_type': 'donor',
            'name': 'Demo User',
            'email': 'demo@lifeconnect.com'
        }
        
        wallet_address = test_data['wallet_address'].lower()
        user_type = test_data['user_type']
        email = test_data['email']
        name = test_data['name']
        
        # Find or create user
        user = get_user_by_wallet(wallet_address)
        if not user:
            user = User(
                wallet_address=wallet_address,
                user_type=user_type,
                email=email,
                name=name
            )
            db.session.add(user)
            db.session.commit()
            log_activity(user.id, 'user_registration', f'Test user created: {user_type}')
        else:
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
        
        # Create JWT token with STRING subject (FIXED)
        additional_claims = {
            'user_type': user.user_type,
            'wallet_address': user.wallet_address,
            'is_active': user.is_active
        }
        
        access_token = create_access_token(
            identity=str(user.id),  # CONVERT TO STRING
            additional_claims=additional_claims
        )
        
        log_activity(user.id, 'test_login', 'Test login successful')
        
        return create_response(True, {
            'access_token': access_token,
            'token_type': 'Bearer',
            'user': {
                'id': user.id,
                'wallet_address': user.wallet_address,
                'email': user.email,
                'name': user.name,
                'user_type': user.user_type,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            },
            'message': 'Test login successful - use this token for protected endpoints'
        })
    
    except Exception as e:
        print(f"Test login error: {str(e)}")  # Debug print
        return create_response(False, error=f'Test login failed: {str(e)}', status_code=500)

@auth_bp.route('/validate-token', methods=['GET'])
@jwt_required()
def validate_token():
    """Validate JWT token"""
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)  # Convert string to int
        user = db.session.get(User, user_id)
        
        if not user:
            return create_response(False, error='User not found', status_code=404)
        
        return create_response(True, {
            'valid': True,
            'user_id': user_id,
            'user_type': user.user_type,
            'message': 'Token is valid'
        })
    
    except Exception as e:
        return create_response(False, error=f'Token validation failed: {str(e)}', status_code=401)

@auth_bp.route('/wallet-login', methods=['POST'])
def wallet_login():
    """Login with specific wallet from provided accounts"""
    try:
        data = request.get_json() or {}
        account_index = data.get('account_index', 0)
        user_type = data.get('user_type', 'donor')
        
        # Predefined accounts from your blockchain
        accounts = [
            {
                'address': '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266',
                'name': 'Account #0',
                'email': 'account0@lifeconnect.com'
            },
            {
                'address': '0x70997970C51812dc3A010C7d01b50e0d17dc79C8',
                'name': 'Account #1',
                'email': 'account1@lifeconnect.com'
            },
            {
                'address': '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC',
                'name': 'Account #2',
                'email': 'account2@lifeconnect.com'
            },
            {
                'address': '0x90F79bf6EB2c4f870365E785982E1f101E93b906',
                'name': 'Account #3',
                'email': 'account3@lifeconnect.com'
            }
        ]
        
        if account_index >= len(accounts):
            return create_response(False, error='Invalid account index', status_code=400)
        
        account = accounts[account_index]
        wallet_address = account['address'].lower()
        
        # Find or create user
        user = get_user_by_wallet(wallet_address)
        if not user:
            user = User(
                wallet_address=wallet_address,
                user_type=user_type,
                email=account['email'],
                name=account['name']
            )
            db.session.add(user)
            db.session.commit()
            log_activity(user.id, 'user_registration', f'Wallet user created: {account["name"]}')
        else:
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
        
        # Create JWT token with STRING subject
        additional_claims = {
            'user_type': user.user_type,
            'wallet_address': user.wallet_address,
            'is_active': user.is_active
        }
        
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )
        
        log_activity(user.id, 'wallet_login', f'Wallet login successful for {account["name"]}')
        
        return create_response(True, {
            'access_token': access_token,
            'token_type': 'Bearer',
            'user': {
                'id': user.id,
                'wallet_address': user.wallet_address,
                'email': user.email,
                'name': user.name,
                'user_type': user.user_type,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            },
            'account_info': account
        })
    
    except Exception as e:
        print(f"Wallet login error: {str(e)}")
        return create_response(False, error=f'Wallet login failed: {str(e)}', status_code=500)
