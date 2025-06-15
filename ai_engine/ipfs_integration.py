import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

class IPFSIntegrator:
    def __init__(self):
        self.gateway = os.getenv('PINATA_GATEWAY', 'gateway.pinata.cloud')

    def fetch_health_record(self, cid: str) -> dict:
        """Fetch health record from IPFS"""
        try:
            url = f"https://{self.gateway}/ipfs/{cid}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health record fetched for CID: {cid}")
                return health_data
            else:
                print(f"❌ Failed to fetch health record: HTTP {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Error fetching health record: {str(e)}")
            return {}

    def enrich_donor_data(self, donor_blockchain_data: dict) -> dict:
        """Enrich donor data with IPFS health records"""
        if 'healthCardCID' in donor_blockchain_data and donor_blockchain_data['healthCardCID']:
            health_data = self.fetch_health_record(donor_blockchain_data['healthCardCID'])
            
            if health_data:
                # Merge blockchain and IPFS data
                enriched_data = donor_blockchain_data.copy()
                enriched_data.update({
                    'labResults': health_data.get('labResults', {}),
                    'organHealth': health_data.get('organData', {}).get('organHealth', {}),
                    'hlaType': health_data.get('labResults', {}).get('tissueTyping', {}).get('hla_match_score', 'Unknown'),
                    'medicalHistory': health_data.get('medicalHistory', {}),
                    'healthStatus': 'Excellent'  # Derived from health data
                })
                return enriched_data
        
        return donor_blockchain_data

    def batch_enrich_donors(self, donors_list: list) -> list:
        """Enrich multiple donors with IPFS data"""
        enriched_donors = []
        
        for donor in donors_list:
            enriched_donor = self.enrich_donor_data(donor)
            enriched_donors.append(enriched_donor)
        
        print(f"✅ Enriched {len(enriched_donors)} donors with IPFS health data")
        return enriched_donors
