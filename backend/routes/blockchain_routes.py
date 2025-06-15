from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from datetime import datetime

from models import db, BlockchainTransaction, User
from utils import log_activity, create_response

blockchain_bp = Blueprint('blockchain', __name__)

@blockchain_bp.route('/transaction-status/<tx_hash>', methods=['GET'])
@jwt_required()
def get_transaction_status(tx_hash):
    """Get blockchain transaction status"""
    try:
        transaction = BlockchainTransaction.query.filter_by(tx_hash=tx_hash).first()
        
        if not transaction:
            return create_response(False, error='Transaction not found', status_code=404)
        
        return create_response(True, {
            'tx_hash': transaction.tx_hash,
            'status': transaction.status,
            'contract_address': transaction.contract_address,
            'function_name': transaction.function_name,
            'user_address': transaction.user_address,
            'gas_used': transaction.gas_used,
            'gas_price': transaction.gas_price,
            'block_number': transaction.block_number,
            'created_at': transaction.created_at.isoformat(),
            'confirmed_at': transaction.confirmed_at.isoformat() if transaction.confirmed_at else None,
            'tx_data': json.loads(transaction.tx_data) if transaction.tx_data else None
        })
    
    except Exception as e:
        return create_response(False, error=str(e), status_code=500)

@blockchain_bp.route('/submit-transaction', methods=['POST'])
@jwt_required()
def submit_transaction():
    """Submit a new blockchain transaction"""
    try:
        user_id = get_jwt_identity()
        user = db.session.get(User, user_id)
        data = request.json
        
        if not user:
            return create_response(False, error='User not found', status_code=404)
        
        # Extract transaction data
        tx_hash = data.get('tx_hash')
        contract_address = data.get('contract_address')
        function_name = data.get('function_name')
        tx_data = data.get('tx_data', {})
        gas_price = data.get('gas_price')
        
        if not all([tx_hash, contract_address, function_name]):
            return create_response(False, error='Missing required transaction data', status_code=400)
        
        # Check if transaction already exists
        existing_tx = BlockchainTransaction.query.filter_by(tx_hash=tx_hash).first()
        if existing_tx:
            return create_response(False, error='Transaction already exists', status_code=409)
        
        # Create new transaction record
        transaction = BlockchainTransaction(
            tx_hash=tx_hash,
            contract_address=contract_address,
            function_name=function_name,
            user_address=user.wallet_address,
            tx_data=json.dumps(tx_data),
            gas_price=gas_price,
            status='pending'
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        log_activity(user_id, 'blockchain_transaction_submitted', 
                    f"Transaction {tx_hash} submitted for {function_name}")
        
        return create_response(True, {
            'tx_hash': tx_hash,
            'status': 'pending',
            'submitted_at': transaction.created_at.isoformat(),
            'message': 'Transaction submitted successfully'
        })
    
    except Exception as e:
        return create_response(False, error=str(e), status_code=500)

@blockchain_bp.route('/confirm-transaction/<tx_hash>', methods=['POST'])
@jwt_required()
def confirm_transaction(tx_hash):
    """Confirm a blockchain transaction"""
    try:
        user_id = get_jwt_identity()
        data = request.json
        
        transaction = BlockchainTransaction.query.filter_by(tx_hash=tx_hash).first()
        
        if not transaction:
            return create_response(False, error='Transaction not found', status_code=404)
        
        # Update transaction with confirmation data
        transaction.status = data.get('status', 'confirmed')
        transaction.block_number = data.get('block_number')
        transaction.gas_used = data.get('gas_used')
        transaction.confirmed_at = datetime.utcnow()
        
        db.session.commit()
        
        log_activity(user_id, 'blockchain_transaction_confirmed', 
                    f"Transaction {tx_hash} confirmed in block {transaction.block_number}")
        
        # Notify via WebSocket
        try:
            from app import socketio
            socketio.emit('blockchain_update', {
                'type': 'transaction_confirmed',
                'tx_hash': tx_hash,
                'status': transaction.status,
                'block_number': transaction.block_number,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"user_{user_id}")
        except ImportError:
            pass
        
        return create_response(True, {
            'tx_hash': tx_hash,
            'status': transaction.status,
            'block_number': transaction.block_number,
            'gas_used': transaction.gas_used,
            'confirmed_at': transaction.confirmed_at.isoformat()
        })
    
    except Exception as e:
        return create_response(False, error=str(e), status_code=500)

@blockchain_bp.route('/user-transactions', methods=['GET'])
@jwt_required()
def get_user_transactions():
    """Get user's blockchain transactions"""
    try:
        user_id = get_jwt_identity()
        user = db.session.get(User, user_id)
        
        if not user:
            return create_response(False, error='User not found', status_code=404)
        
        # Get query parameters
        limit = min(int(request.args.get('limit', 20)), 100)
        status_filter = request.args.get('status')
        
        # Build query
        query = BlockchainTransaction.query.filter_by(user_address=user.wallet_address)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        transactions = query.order_by(BlockchainTransaction.created_at.desc()).limit(limit).all()
        
        transaction_data = [
            {
                'tx_hash': tx.tx_hash,
                'contract_address': tx.contract_address,
                'function_name': tx.function_name,
                'status': tx.status,
                'gas_used': tx.gas_used,
                'gas_price': tx.gas_price,
                'block_number': tx.block_number,
                'created_at': tx.created_at.isoformat(),
                'confirmed_at': tx.confirmed_at.isoformat() if tx.confirmed_at else None,
                'tx_data': json.loads(tx.tx_data) if tx.tx_data else None
            } for tx in transactions
        ]
        
        return create_response(True, {
            'transactions': transaction_data,
            'total_count': len(transaction_data),
            'user_address': user.wallet_address
        })
    
    except Exception as e:
        return create_response(False, error=str(e), status_code=500)

@blockchain_bp.route('/contract-stats', methods=['GET'])
@jwt_required()
def get_contract_stats():
    """Get blockchain contract statistics"""
    try:
        user_id = get_jwt_identity()
        user = db.session.get(User, user_id)
        
        # Only allow regulators and hospitals to access contract stats
        if user and user.user_type not in ['regulator', 'hospital']:
            return create_response(False, error='Insufficient permissions', status_code=403)
        
        # Get contract interaction statistics
        contract_stats = {}
        
        # Get all unique contracts
        contracts = db.session.query(BlockchainTransaction.contract_address).distinct().all()
        
        for (contract_address,) in contracts:
            contract_transactions = BlockchainTransaction.query.filter_by(contract_address=contract_address).all()
            
            total_transactions = len(contract_transactions)
            confirmed_transactions = len([tx for tx in contract_transactions if tx.status == 'confirmed'])
            failed_transactions = len([tx for tx in contract_transactions if tx.status == 'failed'])
            pending_transactions = len([tx for tx in contract_transactions if tx.status == 'pending'])
            
            # Calculate average gas usage
            gas_used_list = [tx.gas_used for tx in contract_transactions if tx.gas_used]
            avg_gas_used = sum(gas_used_list) / len(gas_used_list) if gas_used_list else 0
            
            # Get function call distribution
            function_calls = {}
            for tx in contract_transactions:
                func_name = tx.function_name
                function_calls[func_name] = function_calls.get(func_name, 0) + 1
            
            contract_stats[contract_address] = {
                'contract_address': contract_address,
                'total_transactions': total_transactions,
                'confirmed_transactions': confirmed_transactions,
                'failed_transactions': failed_transactions,
                'pending_transactions': pending_transactions,
                'success_rate': (confirmed_transactions / total_transactions * 100) if total_transactions > 0 else 0,
                'average_gas_used': round(avg_gas_used, 0),
                'function_calls': function_calls
            }
        
        # Overall blockchain stats
        total_all_transactions = BlockchainTransaction.query.count()
        total_gas_used = db.session.query(db.func.sum(BlockchainTransaction.gas_used)).scalar() or 0
        
        blockchain_stats = {
            'contract_stats': list(contract_stats.values()),
            'overall_stats': {
                'total_transactions': total_all_transactions,
                'total_gas_used': total_gas_used,
                'unique_contracts': len(contracts),
                'unique_users': db.session.query(BlockchainTransaction.user_address).distinct().count()
            },
            'generated_at': datetime.utcnow().isoformat()
        }
        
        log_activity(user_id, 'contract_stats_access', "Blockchain contract stats accessed")
        
        return create_response(True, blockchain_stats)
    
    except Exception as e:
        return create_response(False, error=str(e), status_code=500)

@blockchain_bp.route('/network-info', methods=['GET'])
def get_network_info():
    """Get blockchain network information"""
    try:
        # Mock network information (in production, this would come from actual blockchain)
        network_info = {
            'network_name': 'Hardhat Local Network',
            'chain_id': 31337,
            'rpc_url': 'http://127.0.0.1:8545',
            'block_number': 12345,  # Would be fetched from actual blockchain
            'gas_price_gwei': 20,
            'network_status': 'connected',
            'block_time_seconds': 2,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return create_response(True, network_info)
    
    except Exception as e:
        return create_response(False, error=str(e), status_code=500)

@blockchain_bp.route('/validate-address/<address>', methods=['GET'])
def validate_address(address):
    """Validate blockchain address format"""
    try:
        # Basic Ethereum address validation
        if not address:
            return create_response(False, error='Address is required', status_code=400)
        
        # Check if address starts with 0x and has correct length
        is_valid = (
            address.startswith('0x') and 
            len(address) == 42 and 
            all(c in '0123456789abcdefABCDEF' for c in address[2:])
        )
        
        validation_result = {
            'address': address,
            'is_valid': is_valid,
            'format': 'ethereum',
            'checksum_valid': address == address.lower() or address == address.upper(),  # Simplified checksum validation
            'validated_at': datetime.utcnow().isoformat()
        }
        
        return create_response(True, validation_result)
    
    except Exception as e:
        return create_response(False, error=str(e), status_code=500)
