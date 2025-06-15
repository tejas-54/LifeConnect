import os
import json
import sys
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

class BlockchainIntegrator:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('BLOCKCHAIN_RPC_URL', 'http://127.0.0.1:8545')))
        
        # Load contract data
        self.contract_data = self._load_contract_data()
        
        if self.contract_data:
            self.donor_consent_address = self.contract_data['addresses'].get('DonorConsent')
            self.donor_consent_abi = json.loads(self.contract_data['abis'].get('DonorConsent', '[]'))
            
            # Initialize contract
            if self.donor_consent_address and self.donor_consent_abi:
                self.donor_consent = self.w3.eth.contract(
                    address=self.donor_consent_address,
                    abi=self.donor_consent_abi
                )
            else:
                self.donor_consent = None
        else:
            self.donor_consent = None

    def _load_contract_data(self):
        """Load contract data from deployment file"""
        try:
            # Add paths to find the integration file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            
            possible_paths = [
                os.path.join(current_dir, 'integration-contracts.json'),
                os.path.join(project_root, 'integration-contracts.json'),
                os.path.join(project_root, 'blockchain', 'deployed-contracts.json')
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        return json.load(f)
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error loading contract data: {str(e)}")
            return None

    def register_donor_on_blockchain(self, health_card, private_key=None):
        """Register a donor on the blockchain"""
        if not self.donor_consent:
            print("⚠️ DonorConsent contract not available")
            return None
            
        try:
            # Get account to use
            if private_key:
                account = self.w3.eth.account.from_key(private_key)
                address = account.address
            else:
                # Use first account from node
                address = self.w3.eth.accounts[0]
            
            # Extract donor info from health card
            name = health_card.get('name', 'Unknown')
            age = health_card.get('age', 0)
            blood_type = health_card.get('bloodType', 'Unknown')
            organ_types = health_card.get('organTypes', [])
            ipfs_hash = health_card.get('ipfsHash', '')
            
            print(f"🔗 Registering donor on blockchain: {name}")
            
            # Build transaction
            if private_key:
                # Use account with private key
                tx = self.donor_consent.functions.registerDonor(
                    name, 
                    age, 
                    blood_type, 
                    organ_types, 
                    ipfs_hash
                ).build_transaction({
                    'from': address,
                    'nonce': self.w3.eth.get_transaction_count(address),
                    'gas': 300000,
                    'gasPrice': self.w3.to_wei('50', 'gwei')
                })
                
                # Sign and send transaction
                signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            else:
                # Use unlocked account on node
                tx_hash = self.donor_consent.functions.registerDonor(
                    name, 
                    age, 
                    blood_type, 
                    organ_types, 
                    ipfs_hash
                ).transact({'from': address})
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                print(f"✅ Donor registered successfully! Transaction hash: {tx_hash.hex()}")
                
                # Add blockchain info to health card
                health_card['blockchainAddress'] = address
                health_card['blockchainTxHash'] = tx_hash.hex()
                
                return {
                    'success': True,
                    'tx_hash': tx_hash.hex(),
                    'address': address
                }
            else:
                print(f"❌ Donor registration failed! Transaction hash: {tx_hash.hex()}")
                return {
                    'success': False,
                    'tx_hash': tx_hash.hex()
                }
                
        except Exception as e:
            print(f"❌ Error registering donor: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_donor_from_blockchain(self, address):
        """Get donor information from blockchain"""
        if not self.donor_consent:
            print("⚠️ DonorConsent contract not available")
            return None
            
        try:
            # Call contract to get donor info
            donor_data = self.donor_consent.functions.getDonor(address).call()
            
            # Format donor data
            donor = {
                "address": address,
                "name": donor_data[1],
                "age": donor_data[2],
                "bloodType": donor_data[3],
                "organTypes": donor_data[4],
                "isActive": donor_data[5],
                "registrationTime": donor_data[6],
                "healthCardCID": donor_data[7],
                "familyConsent": donor_data[8]
            }
            
            return donor
            
        except Exception as e:
            print(f"❌ Error getting donor data: {str(e)}")
            return None

def main():
    """Test blockchain integration"""
    integrator = BlockchainIntegrator()
    
    # Check if contract is available
    if not integrator.donor_consent:
        print("❌ DonorConsent contract not available. Make sure contracts are deployed.")
        return
    
    # Create a test health card
    health_card = {
        "patientId": "TEST_DONOR_001",
        "name": "Blockchain Test Donor",
        "age": 30,
        "bloodType": "O+",
        "donorStatus": True,
        "organTypes": ["heart", "liver"],
        "ipfsHash": "QmTestIPFSHash123456789"
    }
    
    # Register donor on blockchain
    result = integrator.register_donor_on_blockchain(health_card)
    
    if result and result['success']:
        # Get donor from blockchain
        donor = integrator.get_donor_from_blockchain(result['address'])
        
        if donor:
            print("\n✅ Donor successfully retrieved from blockchain:")
            print(f"Name: {donor['name']}")
            print(f"Age: {donor['age']}")
            print(f"Blood Type: {donor['bloodType']}")
            print(f"Organ Types: {donor['organTypes']}")
            print(f"Health Card CID: {donor['healthCardCID']}")

if __name__ == "__main__":
    main()
