from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

import asyncio # Was missing from previous merge, ensure it's here if used (not in this snippet but good practice)

# Assuming these are in backend.app or a shared utility module
from backend.app import (
    db,   # MongoDB instance
    User, # User Pydantic Model
    verify_token,
    call_external_service,
    BLOCKCHAIN_RPC_URL,
    IPFS_API_URL,
    logger
)
# Database models (BlockchainTransaction, User SQLModel) are commented out as per plan.
# Direct db access will be replaced by service calls or removed.
# from models import db, BlockchainTransaction, User
# from utils import log_activity, create_response # Flask specific

router = APIRouter(prefix="/blockchain", tags=["Blockchain"])

# Placeholder for data models that might be needed for request/response
# For example, if we define a Pydantic model for Transaction
class TransactionResponse(BaseModel):
    tx_hash: str
    status: str
    contract_address: Optional[str] = None
    function_name: Optional[str] = None
    user_address: Optional[str] = None
    gas_used: Optional[int] = None
    gas_price: Optional[int] = None
    block_number: Optional[int] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    tx_data: Optional[Dict[str, Any]] = None


@router.get("/transaction-status/{tx_hash}", response_model=Optional[TransactionResponse])
async def get_transaction_status(
    tx_hash: str = Path(..., title="Transaction Hash", description="The hash of the blockchain transaction"),
    current_user_email: str = Depends(verify_token)
):
    """Get blockchain transaction status"""
    try:
        user_doc = await db.users.find_one({"email": current_user_email})
        if not user_doc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found or not authorized")
        user_obj = User(**user_doc) # To easily access fields like wallet_address

        logger.info(f"User {current_user_email} fetching status for tx {tx_hash}")

        # Simulating no direct DB access as per plan, this part would be removed/changed.
        # Placeholder response:
        if tx_hash == "0x123abc": # Example
            return TransactionResponse(
                tx_hash=tx_hash,
                status="confirmed",
                contract_address="0xContractAddress",
                function_name="someFunction",
                user_address=user_obj.wallet_address or "0xUserWalletPlaceholder",
                gas_used=21000,
                gas_price=50,
                block_number=1234567,
                created_at=datetime.utcnow(),
                confirmed_at=datetime.utcnow(),
                tx_data={"param1": "value1"}
            )
        elif tx_hash == "0xpending":
             return TransactionResponse(
                tx_hash=tx_hash,
                status="pending",
                created_at=datetime.utcnow()
            )
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transaction status for {tx_hash}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


class NetworkInfoResponse(BaseModel):
    network_name: str
    chain_id: int
    rpc_url: str
    block_number: Optional[int] = None
    gas_price_gwei: Optional[int] = None
    network_status: str
    block_time_seconds: Optional[int] = None
    last_updated: datetime

@router.get("/network-info", response_model=NetworkInfoResponse)
async def get_network_info():
    """Get blockchain network information"""
    try:
        # This could call an actual RPC endpoint like eth_chainId, eth_blockNumber, eth_gasPrice
        # For now, using mock data as in the original, but could use call_external_service
        # e.g. block_number = await call_external_service(BLOCKCHAIN_RPC_URL, method="POST", data={"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1})

        # Mock network information
        return NetworkInfoResponse(
            network_name='Hardhat Local Network (FastAPI)',
            chain_id=31337,
            rpc_url=BLOCKCHAIN_RPC_URL, # Use from backend.app
            block_number=12345, # Placeholder, ideally fetched
            gas_price_gwei=20,   # Placeholder
            network_status='connected',
            block_time_seconds=2, # Placeholder
            last_updated=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error fetching network info: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


class AddressValidationResponse(BaseModel):
    address: str
    is_valid: bool
    format: str
    checksum_valid: Optional[bool] = None # Checksum validation can be complex
    validated_at: datetime

@router.get("/validate-address/{address}", response_model=AddressValidationResponse)
async def validate_address(
    address: str = Path(..., title="Blockchain Address", description="The address to validate")
):
    """Validate blockchain address format (Basic Ethereum validation)"""
    try:
        if not address:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Address is required")

        is_valid = (
            address.startswith('0x') and
            len(address) == 42 and
            all(c in '0123456789abcdefABCDEF' for c in address[2:])
        )

        # Simplified checksum or assume not validated for this basic check
        checksum_valid = None
        # A full checksum validation (EIP-55) is more involved.
        # For now, we'll skip it or do a very basic check.
        if is_valid:
            # Basic check: if it has mixed case, it might be checksummed.
            # This is not a real validation, just a hint.
            has_lower = any('a' <= char <= 'f' for char in address[2:])
            has_upper = any('A' <= char <= 'F' for char in address[2:])
            if has_lower and has_upper:
                checksum_valid = True # Placeholder: a proper library should be used for real validation
            elif not has_lower and not has_upper: # all digits or all same case
                 checksum_valid = True # or False, depending on policy for non-checksummed
            else: # only one case of letters
                 checksum_valid = True


        return AddressValidationResponse(
            address=address,
            is_valid=is_valid,
            format='ethereum',
            checksum_valid=checksum_valid,
            validated_at=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error validating address {address}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Pydantic Models for POST requests
class SubmitTransactionRequest(BaseModel):
    tx_hash: str
    contract_address: str
    function_name: str
    tx_data: Optional[Dict[str, Any]] = {}
    gas_price: Optional[int] = None

class SubmitTransactionResponse(BaseModel):
    tx_hash: str
    status: str
    submitted_at: datetime
    message: str

class ConfirmTransactionRequest(BaseModel):
    status: str = "confirmed"
    block_number: Optional[int] = None
    gas_used: Optional[int] = None

class ConfirmTransactionResponse(BaseModel):
    tx_hash: str
    status: str
    block_number: Optional[int] = None
    gas_used: Optional[int] = None
    confirmed_at: datetime


@router.post("/submit-transaction", response_model=SubmitTransactionResponse)
async def submit_transaction(
    tx_payload: SubmitTransactionRequest,
    current_user_email: str = Depends(verify_token)
):
    """Submit a new blockchain transaction"""
    try:
        user_doc = await db.users.find_one({"email": current_user_email})
        if not user_doc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found or not authorized")
        # user_obj = User(**user_doc) # Not strictly needed if only wallet_address is used and directly available

        # user_wallet_address = user_obj.wallet_address # This is the ideal way
        # The original placeholder logic for submit_transaction was:
        # user_wallet_address = current_user.get("wallet_address")
        # if not user_wallet_address: logger.warning(...)
        # This will be replaced by actual user_doc.wallet_address if needed for placeholder logic.
        # For now, the placeholder logic for DB interaction doesn't use user_wallet_address.

        logger.info(f"User {current_user_email} submitted transaction {tx_payload.tx_hash} for {tx_payload.function_name}")

        # Placeholder: Database interaction for checking existing_tx and saving new tx commented out.
        # If we were to save, we'd use user_obj.wallet_address here.

        return SubmitTransactionResponse(
            tx_hash=tx_payload.tx_hash,
            status='pending', # Default status on submission
            submitted_at=datetime.utcnow(),
            message='Transaction submitted successfully (simulated)'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting transaction {tx_payload.tx_hash}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/confirm-transaction/{tx_hash}", response_model=ConfirmTransactionResponse)
async def confirm_transaction(
    tx_payload: ConfirmTransactionRequest,
    tx_hash: str = Path(..., title="Transaction Hash"),
    current_user_email: str = Depends(verify_token)
):
    """Confirm a blockchain transaction"""
    try:
        # No direct use of user_doc needed for this placeholder logic, just logging.
        logger.info(f"User {current_user_email} confirmed transaction {tx_hash} in block {tx_payload.block_number}")

        # Placeholder: Database interaction for finding and updating transaction commented out
        # WebSocket emit logic commented out (Flask-SocketIO specific)
        # try:
        #     from app import socketio # This would be a FastAPI WebSocket solution
        #     socketio.emit('blockchain_update', {...})
        # except ImportError:
        #     pass

        return ConfirmTransactionResponse(
            tx_hash=tx_hash,
            status=tx_payload.status,
            block_number=tx_payload.block_number,
            gas_used=tx_payload.gas_used,
            confirmed_at=datetime.utcnow() # Simulation
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming transaction {tx_hash}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Pydantic Models for remaining GET requests
class UserTransactionDetail(BaseModel): # Reusing part of TransactionResponse structure
    tx_hash: str
    contract_address: Optional[str] = None
    function_name: Optional[str] = None
    status: str
    gas_used: Optional[int] = None
    gas_price: Optional[int] = None
    block_number: Optional[int] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    tx_data: Optional[Dict[str, Any]] = None

class UserTransactionsResponse(BaseModel):
    transactions: List[UserTransactionDetail]
    total_count: int
    user_address: Optional[str] = None


class ContractFunctionStats(BaseModel):
    # Assuming function_calls is Dict[str, int] like {'func_name': count}
    pass # Using Dict[str, int] directly in ContractStatDetail for simplicity for now

class ContractStatDetail(BaseModel):
    contract_address: str
    total_transactions: int
    confirmed_transactions: int
    failed_transactions: int
    pending_transactions: int
    success_rate: float
    average_gas_used: float
    function_calls: Dict[str, int]

class OverallBlockchainStats(BaseModel):
    total_transactions: int
    total_gas_used: int
    unique_contracts: int
    unique_users: int

class ContractStatsResponse(BaseModel):
    contract_stats: List[ContractStatDetail]
    overall_stats: OverallBlockchainStats
    generated_at: datetime


@router.get("/user-transactions", response_model=UserTransactionsResponse)
async def get_user_transactions(
    limit: int = Query(20, ge=1, le=100, description="Number of transactions to return"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter transactions by status"),
    current_user_email: str = Depends(verify_token)
):
    """Get user's blockchain transactions"""
    try:
        user_doc = await db.users.find_one({"email": current_user_email})
        if not user_doc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found or not authorized")
        user_obj = User(**user_doc)

        user_wallet_address = user_obj.wallet_address
        if not user_wallet_address:
            logger.warning(f"User {current_user_email} has no wallet_address for get_user_transactions.")
            return UserTransactionsResponse(transactions=[], total_count=0, user_address=None)

        logger.info(f"Fetching transactions for user {current_user_email} (wallet: {user_wallet_address}) with limit: {limit}, status: {status_filter}")

        # Placeholder: Database interaction for querying transactions commented out
        # Simulated response
        simulated_transactions = []
        # Only generate sample if wallet address is theoretically available
        for i in range(min(limit, 2)): # Simulate a few transactions
            simulated_transactions.append(UserTransactionDetail(
                tx_hash=f"0xusersimulatedtx{i+1}",
                    contract_address="0xContract123",
                    function_name="transfer",
                    status=status_filter or "confirmed",
                    gas_used=21000 + i*100,
                    gas_price=50,
                    block_number=1234567 + i,
                    created_at=datetime.utcnow(),
                    confirmed_at=datetime.utcnow(),
                    tx_data={"to": "0xRecipient", "amount": 100 + i}
                ))

        return UserTransactionsResponse(
            transactions=simulated_transactions,
            total_count=len(simulated_transactions),
            user_address=user_wallet_address
        )

    except Exception as e:
        logger.error(f"Error fetching user transactions for {current_user_email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/contract-stats", response_model=ContractStatsResponse)
async def get_contract_stats(
    current_user_email: str = Depends(verify_token)
):
    """Get blockchain contract statistics"""
    try:
        user_doc = await db.users.find_one({"email": current_user_email})
        if not user_doc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found or not authorized")
        user_obj = User(**user_doc)

        user_role = user_obj.role
        if user_role not in ['regulator', 'hospital', 'admin']:
            logger.warning(f"User {current_user_email} with role '{user_role}' attempted to access contract stats.")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

        logger.info(f"User {current_user_email} (role: {user_role}) accessed contract stats.")

        # Placeholder: Database interaction for aggregating stats commented out
        # Simulated response
        sim_contract_stats = [
            ContractStatDetail(
                contract_address="0xContractAlpha",
                total_transactions=100,
                confirmed_transactions=90,
                failed_transactions=5,
                pending_transactions=5,
                success_rate=90.0,
                average_gas_used=50000,
                function_calls={"mint": 50, "transfer": 50}
            )
        ]
        sim_overall_stats = OverallBlockchainStats(
            total_transactions=150,
            total_gas_used=7500000,
            unique_contracts=1,
            unique_users=10
        )

        return ContractStatsResponse(
            contract_stats=sim_contract_stats,
            overall_stats=sim_overall_stats,
            generated_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching contract stats for user {current_user_email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
