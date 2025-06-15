import os
import json
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class PinataUploader:
    def __init__(self):
        self.jwt = os.getenv('PINATA_JWT')
        self.api_key = os.getenv('PINATA_API_KEY') 
        self.secret_key = os.getenv('PINATA_SECRET_KEY')
        self.gateway = os.getenv('PINATA_GATEWAY', 'gateway.pinata.cloud')

    def pin_json_to_ipfs(self, data: dict, metadata: dict = None) -> dict:
        """Upload JSON data to IPFS via Pinata"""
        url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Use JWT if available, otherwise use API key
        if self.jwt:
            headers["Authorization"] = f"Bearer {self.jwt}"
        elif self.api_key and self.secret_key:
            headers["pinata_api_key"] = self.api_key
            headers["pinata_secret_api_key"] = self.secret_key
        else:
            raise ValueError("No Pinata credentials found. Set PINATA_JWT or PINATA_API_KEY/PINATA_SECRET_KEY")

        payload = {
            "pinataContent": data,
            "pinataOptions": {"cidVersion": 1}
        }
        
        if metadata:
            payload["pinataMetadata"] = metadata

        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Pinata upload failed: {response.status_code} - {response.text}")

    def get_from_ipfs(self, cid: str) -> dict:
        """Retrieve data from IPFS via gateway"""
        url = f"https://{self.gateway}/ipfs/{cid}"
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"IPFS retrieval failed: {response.status_code}")

def generateHealthCardData(donorInfo: dict) -> dict:
    """Generate comprehensive health card data"""
    return {
        # Patient Identity
        "patientId": donorInfo.get('id', f"DONOR_{int(datetime.now().timestamp())}"),
        "name": donorInfo.get('name', 'John Doe'),
        "age": donorInfo.get('age', 35),
        "bloodType": donorInfo.get('bloodType', 'O+'),
        "gender": donorInfo.get('gender', 'Male'),
        
        # Medical History
        "medicalHistory": {
            "allergies": donorInfo.get('allergies', ['None']),
            "medications": donorInfo.get('medications', ['None']),
            "surgeries": donorInfo.get('surgeries', ['Appendectomy - 2015']),
            "chronicConditions": donorInfo.get('chronicConditions', []),
            "familyHistory": {
                "heartDisease": False,
                "diabetes": False,
                "cancer": False
            }
        },
        
        # Organ Data
        "organData": {
            "availableOrgans": donorInfo.get('organs', ['heart', 'liver', 'kidneys']),
            "organHealth": {
                "heart": "Excellent",
                "liver": "Good", 
                "kidneys": "Excellent",
                "lungs": "Good",
                "pancreas": "Good"
            },
            "compatibilityData": {
                "hlaTyping": "A1,A2;B7,B8;C1,C7;DR15,DR4;DQ6,DQ8",
                "crossmatchResults": "Negative"
            }
        },
        
        # Laboratory Results
        "labResults": {
            "bloodTests": {
                "hemoglobin": "14.5 g/dL",
                "whiteBloodCells": "7,200/μL",
                "platelets": "250,000/μL",
                "creatinine": "1.0 mg/dL",
                "alt": "25 U/L",
                "ast": "22 U/L"
            },
            "viralScreening": {
                "hiv": "Negative",
                "hepatitisB": "Negative", 
                "hepatitisC": "Negative",
                "cmv": "Negative",
                "ebv": "Negative"
            },
            "tissueTyping": {
                "blood_group": donorInfo.get('bloodType', 'O+'),
                "rh_factor": "Positive",
                "hla_match_score": 95
            }
        },
        
        # Metadata
        "timestamp": datetime.now().isoformat(),
        "hospitalId": donorInfo.get('hospitalId', 'HOSPITAL_001'),
        "doctorSignature": "Dr. Sarah Johnson, MD",
        "version": "1.0",
        "ipfsHash": None, # Will be filled after upload
        
        # Blockchain Integration
        "blockchainData": {
            "donorAddress": donorInfo.get('donorAddress', None),
            "consentGiven": True,
            "familyConsent": donorInfo.get('familyConsent', False)
        }
    }

def uploadHealthCard(donorInfo: dict = {}) -> dict:
    """Upload health card to IPFS via Pinata"""
    try:
        print('🏥 Generating health card data...')
        healthData = generateHealthCardData(donorInfo)
        
        print('📤 Uploading health card to IPFS via Pinata...')
        
        uploader = PinataUploader()
        
        # Create metadata for better organization
        metadata = {
            "name": f"HealthCard_{healthData['patientId']}",
            "keyvalues": {
                "patientId": healthData['patientId'],
                "bloodType": healthData['bloodType'],
                "timestamp": healthData['timestamp'],
                "version": healthData['version']
            }
        }
        
        # Upload JSON to IPFS
        result = uploader.pin_json_to_ipfs(healthData, metadata)
        
        print('✅ Health card uploaded successfully!')
        print('📋 IPFS CID:', result['IpfsHash'])
        print('🔗 Gateway URL:', f"https://{uploader.gateway}/ipfs/{result['IpfsHash']}")
        print('📊 File Size:', result['PinSize'], 'bytes')
        
        return {
            "cid": result['IpfsHash'],
            "url": f"https://{uploader.gateway}/ipfs/{result['IpfsHash']}",
            "size": result['PinSize'],
            "timestamp": result['Timestamp'],
            "healthData": healthData
        }
        
    except Exception as error:
        print('❌ Error uploading health card:', str(error))
        raise error

def retrieveHealthCard(cid: str) -> dict:
    """Retrieve health card from IPFS"""
    try:
        print(f'📥 Retrieving health card with CID: {cid}')
        
        uploader = PinataUploader()
        healthData = uploader.get_from_ipfs(cid)
        
        print('✅ Health card retrieved successfully!')
        print('👤 Patient:', healthData.get('name', 'Unknown'))
        print('🩸 Blood Type:', healthData.get('bloodType', 'Unknown'))
        print('🫀 Available Organs:', ', '.join(healthData.get('organData', {}).get('availableOrgans', [])))
        
        return healthData
        
    except Exception as error:
        print('❌ Error retrieving health card:', str(error))
        raise error

def testConnection() -> bool:
    """Test Pinata connection"""
    try:
        print('🔍 Testing Pinata connection...')
        uploader = PinataUploader()
        
        # Test with minimal data
        test_data = {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Connection test"
        }
        
        result = uploader.pin_json_to_ipfs(test_data, {"name": "ConnectionTest"})
        
        if result.get('IpfsHash'):
            print('✅ Pinata connection successful!')
            return True
        else:
            print('❌ Pinata connection failed')
            return False
            
    except Exception as error:
        print('❌ Pinata connection failed:', str(error))
        return False

# Alternative: Call JavaScript version via subprocess
def uploadHealthCardJS(donorInfo: dict = {}) -> dict:
    """Upload health card using JavaScript version via subprocess"""
    try:
        print('🔄 Using JavaScript IPFS uploader...')
        
        # Save donor info to temp file
        temp_file = 'temp_donor_info.json'
        with open(temp_file, 'w') as f:
            json.dump(donorInfo, f)
        
        # Call JavaScript version
        result = subprocess.run(
            ['node', 'upload_healthcard.js', 'upload'],
            cwd='./ipfs_scripts',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        if result.returncode == 0:
            print('✅ JavaScript IPFS upload successful')
            # Parse output to extract CID (would need to modify JS script to output JSON)
            return {"cid": "JS_UPLOAD_SUCCESS", "method": "javascript"}
        else:
            print('❌ JavaScript IPFS upload failed:', result.stderr)
            raise Exception(f"JavaScript upload failed: {result.stderr}")
            
    except Exception as error:
        print('❌ Error calling JavaScript uploader:', str(error))
        raise error

# CLI Interface
def main():
    import sys
    
    if len(sys.argv) < 2:
        print('Usage:')
        print('  Test connection: python upload_healthcard.py test')
        print('  Upload sample: python upload_healthcard.py upload')
        print('  Retrieve: python upload_healthcard.py retrieve <CID>')
        print('  Use JS version: python upload_healthcard.py upload-js')
        return
    
    action = sys.argv[1]
    
    if action == 'test':
        testConnection()
    elif action == 'upload':
        # Sample donor info for demo
        sampleDonor = {
            "id": "DONOR_001",
            "name": "Alice Johnson", 
            "age": 28,
            "bloodType": "O+",
            "organs": ["heart", "liver"],
            "donorAddress": "0x1234567890123456789012345678901234567890"
        }
        
        result = uploadHealthCard(sampleDonor)
        print('\n📊 Upload Result:', json.dumps(result, indent=2))
    elif action == 'upload-js':
        sampleDonor = {
            "name": "Alice Johnson", 
            "bloodType": "O+"
        }
        result = uploadHealthCardJS(sampleDonor)
        print('\n📊 JS Upload Result:', json.dumps(result, indent=2))
    elif action == 'retrieve':
        if len(sys.argv) < 3:
            print('❌ Please provide CID: python upload_healthcard.py retrieve <CID>')
            return
        
        cid = sys.argv[2]
        data = retrieveHealthCard(cid)
        print('\n📋 Retrieved Health Data:')
        print('   Patient ID:', data.get('patientId', 'Unknown'))
        print('   Name:', data.get('name', 'Unknown'))
        print('   Blood Type:', data.get('bloodType', 'Unknown'))

if __name__ == "__main__":
    main()
