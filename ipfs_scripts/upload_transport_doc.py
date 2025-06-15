import os
import json
import requests
import subprocess
from datetime import datetime, timedelta
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
            raise ValueError("No Pinata credentials found")

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

def generateTransportDocument(organInfo: dict) -> dict:
    """Generate comprehensive transport document"""
    return {
        # Document Identity
        "documentId": f"TRANS_{int(datetime.now().timestamp())}",
        "organId": organInfo.get('organId', 'ORG_001'),
        "transportId": f"TRANSPORT_{int(datetime.now().timestamp())}",
        
        # Organ Information
        "organDetails": {
            "type": organInfo.get('organType', 'heart'),
            "harvestTime": organInfo.get('harvestTime', datetime.now().isoformat()),
            "expiryTime": organInfo.get('expiryTime', (datetime.now() + timedelta(hours=8)).isoformat()),
            "viabilityWindow": "8 hours",
            "currentStatus": "In Transit"
        },
        
        # Donor & Recipient
        "donor": {
            "id": organInfo.get('donorId', 'DONOR_001'),
            "hospital": organInfo.get('donorHospital', 'City General Hospital'),
            "location": "Downtown Medical District"
        },
        "recipient": {
            "id": organInfo.get('recipientId', 'RECIPIENT_001'),
            "hospital": organInfo.get('recipientHospital', 'Metro Medical Center'), 
            "location": "Uptown Medical Complex"
        },
        
        # Logistics & Route
        "logistics": {
            "pickupTime": datetime.now().isoformat(),
            "estimatedDelivery": (datetime.now() + timedelta(hours=4)).isoformat(),
            "actualDelivery": None,
            "route": {
                "origin": "City General Hospital, Downtown",
                "destination": "Metro Medical Center, Uptown", 
                "distance": "15.7 km",
                "estimatedDuration": "45 minutes",
                "actualDuration": None,
                "waypoints": [
                    { 
                        "location": "Highway Junction A", 
                        "eta": (datetime.now() + timedelta(minutes=15)).isoformat() 
                    },
                    { 
                        "location": "Medical District Bridge", 
                        "eta": (datetime.now() + timedelta(minutes=30)).isoformat() 
                    }
                ]
            },
            "transportMethod": organInfo.get('transportMethod', 'Medical Helicopter'),
            "priority": "Critical",
            "courierDetails": {
                "name": "Emergency Medical Transport",
                "licenseNumber": "EMT-2025-447", 
                "contactNumber": "+1-555-0199",
                "driverName": "Dr. Michael Chen",
                "medicalPersonnel": "Nurse Jennifer Lopez"
            }
        },
        
        # Real-time Monitoring
        "monitoring": {
            "temperatureLog": [
                { 
                    "timestamp": datetime.now().isoformat(), 
                    "temperature": "4°C", 
                    "location": "Origin Hospital",
                    "status": "Optimal"
                }
            ],
            "gpsTracking": {
                "currentLocation": { "lat": 40.7128, "lng": -74.0060 },
                "speed": "85 km/h",
                "lastUpdate": datetime.now().isoformat()
            },
            "qualityMetrics": {
                "vibrationLevel": "Minimal",
                "humidityLevel": "65%", 
                "oxygenSaturation": "98%"
            }
        },
        
        # Chain of Custody
        "custodyChain": [
            {
                "timestamp": datetime.now().isoformat(),
                "handler": "Dr. Sarah Johnson",
                "role": "Harvesting Surgeon",
                "action": "Organ harvested and prepared for transport",
                "location": "City General Hospital OR-3",
                "signature": "SJ_2025_001"
            }
        ],
        
        # Quality & Safety Checks
        "qualityChecks": {
            "preTransport": {
                "visualInspection": "Normal - no visible damage",
                "temperatureCheck": "4°C - Optimal range",
                "packagingIntegrity": "Secure - triple sealed",
                "documentationComplete": True,
                "timeStamp": datetime.now().isoformat()
            },
            "postTransport": None # Will be filled upon delivery
        },
        
        # Emergency Information
        "emergency": {
            "contacts": {
                "originHospital": "+1-555-0123",
                "destinationHospital": "+1-555-0456", 
                "transportCoordinator": "+1-555-0789",
                "medicalDirector": "+1-555-0321"
            },
            "procedures": {
                "emergencyReroute": "Contact dispatch immediately",
                "equipmentFailure": "Activate backup cooling system",
                "weatherDelay": "Secure location and monitor temperature"
            }
        },
        
        # Blockchain Integration
        "blockchain": {
            "organContractAddress": None,
            "custodyContractAddress": None,
            "transactionHashes": [],
            "smartContractEvents": []
        },
        
        # Document Metadata
        "metadata": {
            "created": datetime.now().isoformat(),
            "version": "2.0",
            "status": "Active",
            "ipfsHash": None,
            "lastUpdated": datetime.now().isoformat()
        }
    }

def uploadTransportDocument(organInfo: dict = {}) -> dict:
    """Upload transport document to IPFS via Pinata"""
    try:
        print('🚚 Generating transport document...')
        transportData = generateTransportDocument(organInfo)
        
        print('📤 Uploading transport document to IPFS...')
        
        uploader = PinataUploader()
        
        metadata = {
            "name": f"TransportDoc_{transportData['documentId']}",
            "keyvalues": {
                "organId": transportData['organId'],
                "organType": transportData['organDetails']['type'],
                "transportId": transportData['transportId'],
                "priority": transportData['logistics']['priority'],
                "timestamp": transportData['metadata']['created']
            }
        }
        
        result = uploader.pin_json_to_ipfs(transportData, metadata)
        
        print('✅ Transport document uploaded successfully!')
        print('📋 IPFS CID:', result['IpfsHash'])
        print('🔗 Gateway URL:', f"https://{uploader.gateway}/ipfs/{result['IpfsHash']}")
        
        return {
            "cid": result['IpfsHash'],
            "url": f"https://{uploader.gateway}/ipfs/{result['IpfsHash']}",
            "size": result['PinSize'],
            "transportData": transportData
        }
        
    except Exception as error:
        print('❌ Error uploading transport document:', str(error))
        raise error

def retrieveTransportDocument(cid: str) -> dict:
    """Retrieve transport document from IPFS"""
    try:
        print(f'📥 Retrieving transport document with CID: {cid}')
        
        uploader = PinataUploader()
        transportData = uploader.get_from_ipfs(cid)
        
        print('✅ Transport document retrieved successfully!')
        print('🚚 Transport ID:', transportData.get('transportId', 'Unknown'))
        print('🫀 Organ Type:', transportData.get('organDetails', {}).get('type', 'Unknown'))
        print('📍 Route:', f"{transportData.get('logistics', {}).get('route', {}).get('origin', 'Unknown')} → {transportData.get('logistics', {}).get('route', {}).get('destination', 'Unknown')}")
        
        return transportData
        
    except Exception as error:
        print('❌ Error retrieving transport document:', str(error))
        raise error

# Alternative: Call JavaScript version via subprocess
def uploadTransportDocumentJS(organInfo: dict = {}) -> dict:
    """Upload transport document using JavaScript version via subprocess"""
    try:
        print('🔄 Using JavaScript transport uploader...')
        
        # Call JavaScript version
        result = subprocess.run(
            ['node', 'upload_transport_doc.js', 'upload'],
            cwd='./ipfs_scripts',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print('✅ JavaScript transport upload successful')
            return {"cid": "JS_TRANSPORT_SUCCESS", "method": "javascript"}
        else:
            print('❌ JavaScript transport upload failed:', result.stderr)
            raise Exception(f"JavaScript upload failed: {result.stderr}")
            
    except Exception as error:
        print('❌ Error calling JavaScript uploader:', str(error))
        raise error

# CLI Interface
def main():
    import sys
    
    if len(sys.argv) < 2:
        print('Usage:')
        print('  Upload: python upload_transport_doc.py upload')
        print('  Retrieve: python upload_transport_doc.py retrieve <CID>')
        print('  Use JS version: python upload_transport_doc.py upload-js')
        return
    
    action = sys.argv[1]
    
    if action == 'upload':
        sampleOrgan = {
            "organId": "ORG_001",
            "organType": "heart",
            "donorId": "DONOR_001", 
            "recipientId": "RECIPIENT_001",
            "transportMethod": "Medical Helicopter"
        }
        
        result = uploadTransportDocument(sampleOrgan)
        print('\n📊 Upload Result:', json.dumps(result, indent=2))
    elif action == 'upload-js':
        sampleOrgan = {
            "organType": "heart",
            "transportMethod": "ambulance"
        }
        result = uploadTransportDocumentJS(sampleOrgan)
        print('\n📊 JS Upload Result:', json.dumps(result, indent=2))
    elif action == 'retrieve':
        if len(sys.argv) < 3:
            print('❌ Please provide CID: python upload_transport_doc.py retrieve <CID>')
            return
        
        cid = sys.argv[2]
        data = retrieveTransportDocument(cid)
        print('\n📋 Transport Summary:')
        print('   Document ID:', data.get('documentId', 'Unknown'))
        print('   Organ Type:', data.get('organDetails', {}).get('type', 'Unknown'))
        print('   Distance:', data.get('logistics', {}).get('route', {}).get('distance', 'Unknown'))

if __name__ == "__main__":
    main()
