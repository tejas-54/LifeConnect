import json
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

class BlockchainIntegrator:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('BLOCKCHAIN_RPC_URL')))
        self.donor_consent_address = os.getenv('DONOR_CONSENT_ADDRESS')
        self.organ_lifecycle_address = os.getenv('ORGAN_LIFECYCLE_ADDRESS')
        
        # Load contract ABIs (simplified for demo)
        self.donor_consent_abi = self._load_abi('DonorConsent')
        self.organ_lifecycle_abi = self._load_abi('OrganLifecycle')
        
        # Initialize contracts
        if self.donor_consent_address:
            self.donor_consent = self.w3.eth.contract(
                address=self.donor_consent_address,
                abi=self.donor_consent_abi
            )
            
        if self.organ_lifecycle_address:
            self.organ_lifecycle = self.w3.eth.contract(
                address=self.organ_lifecycle_address,
                abi=self.organ_lifecycle_abi
            )

    def _load_abi(self, contract_name):
        """Load contract ABI from artifacts"""
        try:
            abi_path = f"../blockchain/artifacts/contracts/{contract_name}.sol/{contract_name}.json"
            with open(abi_path, 'r') as f:
                contract_data = json.load(f)
                return contract_data['abi']
        except FileNotFoundError:
            print(f"⚠️ ABI file not found for {contract_name}")
            return []

    def get_all_donors(self):
        """Fetch all registered donors from blockchain"""
        try:
            donor_count = self.donor_consent.functions.getDonorCount().call()
            donors = []
            
            for i in range(donor_count):
                donor_address = self.donor_consent.functions.donorList(i).call()
                donor_data = self.donor_consent.functions.getDonor(donor_address).call()
                
                donors.append({
                    "address": donor_address,
                    "name": donor_data[1],
                    "age": donor_data[2],
                    "bloodType": donor_data[3],
                    "organTypes": donor_data[4],
                    "isActive": donor_data[5],
                    "healthCardCID": donor_data[7],
                    "familyConsent": donor_data[8]
                })
            
            return donors
        except Exception as e:
            print(f"❌ Error fetching donors: {str(e)}")
            return []

    def get_all_recipients(self):
        """Fetch all registered recipients from blockchain"""
        try:
            recipients = []
            recipient_addresses = self.organ_lifecycle.functions.getAllRecipients().call()
            
            for address in recipient_addresses:
                recipient_data = self.organ_lifecycle.functions.getRecipient(address).call()
                
                recipients.append({
                    "address": address,
                    "name": recipient_data[1],
                    "bloodType": recipient_data[2],
                    "requiredOrgan": recipient_data[3],
                    "urgencyScore": recipient_data[4],
                    "registrationTime": recipient_data[5],
                    "isActive": recipient_data[6]
                })
            
            return recipients
        except Exception as e:
            print(f"❌ Error fetching recipients: {str(e)}")
            return []

    def get_available_organs(self):
        """Fetch available organs from blockchain"""
        try:
            organs = []
            # This would need to be implemented based on your contract structure
            # For now, returning sample data
            return organs
        except Exception as e:
            print(f"❌ Error fetching organs: {str(e)}")
            return []

    def submit_match_result(self, organ_id, recipient_address, match_score, private_key):
        """Submit AI match result to blockchain"""
        try:
            account = self.w3.eth.account.from_key(private_key)
            
            # Build transaction
            transaction = self.organ_lifecycle.functions.matchOrgan(
                organ_id,
                recipient_address,
                match_score
            ).build_transaction({
                'from': account.address,
                'nonce': self.w3.eth.get_transaction_count(account.address),
                'gas': 300000,
                'gasPrice': self.w3.to_wei('20', 'gwei')
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            print(f"✅ Match result submitted. Tx hash: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            print(f"❌ Error submitting match result: {str(e)}")
            return None
