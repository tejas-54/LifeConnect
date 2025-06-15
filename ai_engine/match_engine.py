import os
import json
import random
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

class LifeConnectAI:
    def __init__(self):
        # Initialize Gemini AI with updated model
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.gemini_model_name = 'gemini-1.5-flash'  # Updated model name
        
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel(self.gemini_model_name)
                print(f"🧠 Gemini AI Model: {self.gemini_model_name}")
            except Exception as e:
                print(f"⚠️ Gemini setup warning: {e}")
                self.gemini_model = None
        else:
            self.gemini_model = None
        
        # Initialize blockchain connection
        try:
            self.w3 = Web3(Web3.HTTPProvider(os.getenv('BLOCKCHAIN_RPC_URL')))
            blockchain_status = "✅ Connected" if self.w3.is_connected() else "❌ Not connected"
        except:
            blockchain_status = "❌ Connection failed"
        
        # Configuration
        self.use_gemini = os.getenv('USE_GEMINI_API', 'true').lower() == 'true'
        self.fallback_to_algorithm = os.getenv('FALLBACK_TO_ALGORITHM', 'true').lower() == 'true'
        self.match_threshold = int(os.getenv('MATCH_THRESHOLD', '70'))
        
        print("🤖 LifeConnect AI Engine initialized")
        print(f"   Gemini API: {'✅ Enabled' if self.gemini_model else '❌ Not configured'}")
        print(f"   Blockchain: {blockchain_status}")
        print(f"   Match Threshold: {self.match_threshold}%")

    def test_gemini_connection(self):
        """Test Gemini API connection"""
        if not self.gemini_model:
            return False, "Gemini not configured"
        
        try:
            response = self.gemini_model.generate_content("Hello, this is a test.")
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)

    def get_gemini_match_score(self, donor_data: Dict, recipient_data: Dict) -> Dict:
        """Use Gemini AI for advanced organ matching analysis"""
        if not self.gemini_model:
            print("🔄 Gemini not available, using algorithmic matching...")
            return self.algorithmic_match(donor_data, recipient_data)
        
        try:
            # Create comprehensive medical prompt
            prompt = f"""
            As a medical AI specializing in organ transplant compatibility, analyze the following case:

            DONOR PROFILE:
            - Name: {donor_data.get('name', 'Anonymous')}
            - Age: {donor_data.get('age', 'Unknown')} years
            - Blood Type: {donor_data.get('bloodType', 'Unknown')}
            - Organ: {donor_data.get('organType', 'Unknown')}
            - Health Status: {donor_data.get('healthStatus', 'Good')}
            - Medical History: {donor_data.get('medicalHistory', 'None provided')}

            RECIPIENT PROFILE:
            - Name: {recipient_data.get('name', 'Anonymous')}
            - Age: {recipient_data.get('age', 'Unknown')} years
            - Blood Type: {recipient_data.get('bloodType', 'Unknown')}
            - Needed Organ: {recipient_data.get('requiredOrgan', 'Unknown')}
            - Urgency Score: {recipient_data.get('urgencyScore', 'Unknown')}/100
            - Medical Condition: {recipient_data.get('condition', 'Unknown')}
            - Waiting Time: {recipient_data.get('waitingTime', 'Unknown')} days

            Provide a medical compatibility analysis with:
            1. Overall compatibility score (0-100)
            2. Key compatibility factors
            3. Medical risks and considerations
            4. Clinical recommendation

            Respond in this JSON format:
            {{
                "match_score": <number 0-100>,
                "compatibility_factors": ["factor1", "factor2", "factor3"],
                "medical_risks": ["risk1", "risk2"],
                "clinical_recommendation": "recommendation text",
                "confidence_level": "high/medium/low"
            }}
            """
            
            response = self.gemini_model.generate_content(prompt)
            result_text = response.text
            
            # Parse JSON response
            try:
                # Clean the response to extract JSON
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = result_text[json_start:json_end]
                    result = json.loads(json_str)
                    
                    # Validate and format result
                    formatted_result = {
                        "match_score": min(100, max(0, result.get('match_score', 85))),
                        "factors": result.get('compatibility_factors', ['AI analysis completed']),
                        "risks": result.get('medical_risks', ['Standard transplant risks']),
                        "recommendation": result.get('clinical_recommendation', 'Proceed with standard protocols'),
                        "confidence": result.get('confidence_level', 'medium'),
                        "ai_source": "gemini_ai"
                    }
                    
                    print(f"🧠 Gemini AI Analysis - Score: {formatted_result['match_score']}/100")
                    return formatted_result
                else:
                    raise ValueError("No valid JSON found in response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ JSON parsing failed: {e}")
                # Extract score from text if JSON fails
                score = self._extract_score_from_text(result_text)
                return {
                    "match_score": score,
                    "factors": ["AI compatibility analysis", "Medical history review"],
                    "risks": ["Standard transplant considerations"],
                    "recommendation": "Medical team evaluation recommended",
                    "confidence": "medium",
                    "ai_source": "gemini_text_parsed"
                }
                
        except Exception as e:
            print(f"❌ Gemini AI Error: {str(e)}")
            if self.fallback_to_algorithm:
                print("🔄 Falling back to algorithmic matching...")
                return self.algorithmic_match(donor_data, recipient_data)
            raise e

    def _extract_score_from_text(self, text: str) -> int:
        """Extract compatibility score from Gemini text response"""
        import re
        
        # Look for score patterns
        score_patterns = [
            r'score[:\s]*(\d{1,3})',
            r'compatibility[:\s]*(\d{1,3})',
            r'(\d{1,3})[:\s]*out of 100',
            r'(\d{1,3})/100',
            r'(\d{1,3})%'
        ]
        
        for pattern in score_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    score = int(matches[0])
                    if 0 <= score <= 100:
                        return score
                except ValueError:
                    continue
        
        # Default score based on text sentiment
        if any(word in text.lower() for word in ['excellent', 'perfect', 'ideal']):
            return 90
        elif any(word in text.lower() for word in ['good', 'compatible', 'suitable']):
            return 80
        elif any(word in text.lower() for word in ['acceptable', 'possible']):
            return 70
        else:
            return 75

    def algorithmic_match(self, donor_data: Dict, recipient_data: Dict) -> Dict:
        """Enhanced algorithmic matching with medical factors"""
        print("⚙️ Running Algorithmic Match Analysis...")
        
        score = 0
        factors = []
        risks = []
        
        # 1. Blood Type Compatibility (35 points max)
        blood_score, blood_factor = self._calculate_blood_compatibility(
            donor_data.get('bloodType'), recipient_data.get('bloodType')
        )
        score += blood_score
        factors.append(blood_factor)
        
        # 2. Organ Type Match (25 points max)
        organ_score, organ_factor = self._calculate_organ_compatibility(
            donor_data.get('organType'), recipient_data.get('requiredOrgan')
        )
        score += organ_score
        factors.append(organ_factor)
        
        # 3. Age Compatibility (15 points max)
        age_score, age_factor = self._calculate_age_compatibility(
            donor_data.get('age'), recipient_data.get('age')
        )
        score += age_score
        factors.append(age_factor)
        
        # 4. Urgency Factor (15 points max)
        urgency_score = min(15, recipient_data.get('urgencyScore', 50) * 0.15)
        score += urgency_score
        factors.append(f"Urgency bonus: {urgency_score:.1f}/15 (priority: {recipient_data.get('urgencyScore', 50)}/100)")
        
        # 5. Medical History Compatibility (10 points max)
        medical_score = self._calculate_medical_compatibility(donor_data, recipient_data)
        score += medical_score
        factors.append(f"Medical compatibility: {medical_score:.1f}/10")
        
        # Risk Assessment
        self._assess_medical_risks(donor_data, recipient_data, risks, score)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(score, risks)
        
        final_score = min(100, round(score))
        
        print(f"⚙️ Algorithmic Analysis Complete - Score: {final_score}/100")
        
        return {
            "match_score": final_score,
            "factors": factors,
            "risks": risks if risks else ["Standard transplant monitoring required"],
            "recommendation": recommendation,
            "ai_source": "algorithmic",
            "detailed_scores": {
                "blood_compatibility": blood_score,
                "organ_match": organ_score,
                "age_compatibility": age_score,
                "urgency_factor": urgency_score,
                "medical_compatibility": medical_score
            }
        }

    def _calculate_blood_compatibility(self, donor_blood: str, recipient_blood: str) -> Tuple[float, str]:
        """Enhanced blood type compatibility with detailed scoring"""
        if not donor_blood or not recipient_blood:
            return 15, "⚠️ Blood type data incomplete"
        
        # Comprehensive compatibility matrix with medical accuracy
        compatibility_matrix = {
            "O-": {  # Universal donor
                "O-": 35, "O+": 33, "A-": 35, "A+": 33, 
                "B-": 35, "B+": 33, "AB-": 35, "AB+": 33
            },
            "O+": {
                "O+": 35, "A+": 30, "B+": 30, "AB+": 30
            },
            "A-": {
                "A-": 35, "A+": 33, "AB-": 35, "AB+": 33
            },
            "A+": {
                "A+": 35, "AB+": 30
            },
            "B-": {
                "B-": 35, "B+": 33, "AB-": 35, "AB+": 33
            },
            "B+": {
                "B+": 35, "AB+": 30
            },
            "AB-": {
                "AB-": 35, "AB+": 33
            },
            "AB+": {
                "AB+": 35
            }
        }
        
        score = compatibility_matrix.get(donor_blood, {}).get(recipient_blood, 0)
        
        if score >= 35:
            level = "Perfect"
        elif score >= 30:
            level = "Excellent"
        elif score > 0:
            level = "Compatible"
        else:
            level = "Incompatible"
        
        return score, f"Blood compatibility: {level} ({donor_blood} → {recipient_blood})"

    def _calculate_organ_compatibility(self, donor_organ: str, required_organ: str) -> Tuple[float, str]:
        """Calculate organ type compatibility"""
        if not donor_organ or not required_organ:
            return 10, "⚠️ Organ type data incomplete"
        
        if donor_organ.lower() == required_organ.lower():
            return 25, f"✅ Perfect organ match: {donor_organ}"
        else:
            return 0, f"❌ Organ mismatch: {donor_organ} ≠ {required_organ}"

    def _calculate_age_compatibility(self, donor_age: int, recipient_age: int) -> Tuple[float, str]:
        """Calculate age compatibility with medical guidelines"""
        if not donor_age or not recipient_age:
            return 8, "⚠️ Age data incomplete"
        
        age_diff = abs(donor_age - recipient_age)
        
        # Medical age compatibility guidelines
        if age_diff <= 5:
            score, level = 15, "Optimal"
        elif age_diff <= 10:
            score, level = 12, "Excellent"
        elif age_diff <= 15:
            score, level = 10, "Good"
        elif age_diff <= 25:
            score, level = 6, "Acceptable"
        else:
            score, level = 2, "Challenging"
        
        return score, f"Age compatibility: {level} (Δ{age_diff} years)"

    def _calculate_medical_compatibility(self, donor_data: Dict, recipient_data: Dict) -> float:
        """Calculate medical history and health status compatibility"""
        score = 5  # Base score
        
        # Donor health status bonus
        health_status = donor_data.get('healthStatus', 'Unknown').lower()
        if health_status == 'excellent':
            score += 3
        elif health_status == 'good':
            score += 2
        elif health_status == 'fair':
            score += 1
        
        # Recipient condition factor
        condition = recipient_data.get('condition', '').lower()
        if 'acute' in condition or 'critical' in condition:
            score += 2  # Higher urgency adds compatibility
        
        return min(10, score)

    def _assess_medical_risks(self, donor_data: Dict, recipient_data: Dict, risks: List[str], score: float):
        """Assess and document medical risks"""
        if score < 70:
            risks.append("⚠️ Below optimal compatibility threshold")
        
        # Blood type risks
        donor_blood = donor_data.get('bloodType', '')
        if donor_blood and 'AB' in donor_blood:
            risks.append("💉 AB blood type - monitor for antibody reactions")
        
        # Age-related risks
        donor_age = donor_data.get('age', 0)
        recipient_age = recipient_data.get('age', 0)
        
        if abs(donor_age - recipient_age) > 20:
            risks.append("👥 Significant age difference - enhanced monitoring required")
        
        if donor_age > 60:
            risks.append("📈 Older donor organ - evaluate organ function carefully")
        
        # Urgency-related considerations
        urgency = recipient_data.get('urgencyScore', 0)
        if urgency > 90:
            risks.append("🚨 Critical urgency - expedited processing required")

    def _generate_recommendation(self, score: float, risks: List[str]) -> str:
        """Generate clinical recommendation based on analysis"""
        if score >= 90:
            return "🟢 Highly Recommended - Excellent compatibility, proceed with standard protocols"
        elif score >= 80:
            return "🟡 Recommended - Good compatibility, standard transplant protocols"
        elif score >= 70:
            return "🟠 Acceptable - Enhanced monitoring and evaluation recommended"
        elif score >= 60:
            return "🔶 Marginal - Requires detailed medical team consultation"
        else:
            return "🔴 Not Recommended - Significant compatibility concerns, explore alternatives"

    def find_best_matches(self, organ_data: Dict, recipients_list: List[Dict], top_n: int = 5) -> List[Dict]:
        """Find best recipient matches using both AI and algorithmic analysis"""
        matches = []
        
        print(f"🔍 Analyzing {len(recipients_list)} potential recipients...")
        print(f"💡 Using: {'Gemini AI + Algorithmic' if self.use_gemini and self.gemini_model else 'Algorithmic Only'}")
        
        for i, recipient in enumerate(recipients_list, 1):
            try:
                print(f"   Analyzing recipient {i}/{len(recipients_list)}: {recipient.get('name', 'Unknown')}")
                
                # Use Gemini AI if available and enabled
                if self.use_gemini and self.gemini_model:
                    match_result = self.get_gemini_match_score(organ_data, recipient)
                else:
                    match_result = self.algorithmic_match(organ_data, recipient)
                
                match_result['recipient'] = recipient
                match_result['timestamp'] = datetime.now().isoformat()
                match_result['analysis_method'] = match_result.get('ai_source', 'unknown')
                matches.append(match_result)
                
            except Exception as e:
                print(f"❌ Error analyzing recipient {recipient.get('name', 'Unknown')}: {str(e)}")
                continue
        
        # Sort by match score (descending)
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Filter by threshold
        qualified_matches = [m for m in matches if m['match_score'] >= self.match_threshold]
        
        print(f"✅ Analysis complete: {len(qualified_matches)}/{len(matches)} qualified matches (≥{self.match_threshold}%)")
        
        return qualified_matches[:top_n]

    def analyze_waiting_list(self, recipients_list: List[Dict]) -> Dict:
        """Comprehensive waiting list analysis"""
        if not recipients_list:
            return {
                "total": 0, 
                "by_organ": {}, 
                "by_urgency": {}, 
                "recommendations": ["No recipients in waiting list"]
            }
        
        df = pd.DataFrame(recipients_list)
        
        analysis = {
            "total_recipients": len(recipients_list),
            "by_organ": df['requiredOrgan'].value_counts().to_dict() if 'requiredOrgan' in df.columns else {},
            "by_blood_type": df['bloodType'].value_counts().to_dict() if 'bloodType' in df.columns else {},
            "by_urgency": {
                "critical (90-100)": len(df[df['urgencyScore'] >= 90]) if 'urgencyScore' in df.columns else 0,
                "high (80-89)": len(df[(df['urgencyScore'] >= 80) & (df['urgencyScore'] < 90)]) if 'urgencyScore' in df.columns else 0,
                "medium (70-79)": len(df[(df['urgencyScore'] >= 70) & (df['urgencyScore'] < 80)]) if 'urgencyScore' in df.columns else 0,
                "low (<70)": len(df[df['urgencyScore'] < 70]) if 'urgencyScore' in df.columns else 0
            },
            "average_urgency": df['urgencyScore'].mean() if 'urgencyScore' in df.columns else 0,
            "recommendations": []
        }
        
        # Generate intelligent recommendations
        critical_count = analysis["by_urgency"]["critical (90-100)"]
        if critical_count > 0:
            analysis["recommendations"].append(f"🚨 {critical_count} critical patients need immediate attention")
        
        high_count = analysis["by_urgency"]["high (80-89)"]
        if high_count > 0:
            analysis["recommendations"].append(f"⚠️ {high_count} high-priority patients require monitoring")
        
        # Most needed organ analysis
        if analysis["by_organ"]:
            most_needed = max(analysis["by_organ"].items(), key=lambda x: x[1])
            analysis["recommendations"].append(f"🫀 Most needed: {most_needed[0]} ({most_needed[1]} patients)")
        
        # Blood type analysis
        if analysis["by_blood_type"]:
            most_common_blood = max(analysis["by_blood_type"].items(), key=lambda x: x[1])
            analysis["recommendations"].append(f"🩸 Most common blood type: {most_common_blood[0]} ({most_common_blood[1]} patients)")
        
        return analysis

# Sample data for testing (enhanced with more realistic medical data)
def load_sample_data():
    """Load comprehensive sample data for testing"""
    sample_donors = [
        {
            "id": "DONOR_001",
            "name": "Alice Johnson",
            "age": 35,
            "bloodType": "O+",
            "organType": "heart",
            "healthStatus": "Excellent",
            "medicalHistory": {
                "surgeries": [],
                "medications": [],
                "allergies": ["None"]
            }
        },
        {
            "id": "DONOR_002", 
            "name": "Bob Smith",
            "age": 28,
            "bloodType": "A-",
            "organType": "kidney",
            "healthStatus": "Good",
            "medicalHistory": {
                "surgeries": ["Appendectomy"],
                "medications": ["None"],
                "allergies": ["Penicillin"]
            }
        },
        {
            "id": "DONOR_003",
            "name": "Carol Davis",
            "age": 42,
            "bloodType": "B+",
            "organType": "liver",
            "healthStatus": "Good",
            "medicalHistory": {
                "surgeries": [],
                "medications": ["Multivitamin"],
                "allergies": ["None"]
            }
        }
    ]
    
    sample_recipients = [
        {
            "id": "RECIPIENT_001",
            "name": "Charlie Brown",
            "age": 32,
            "bloodType": "O+",
            "requiredOrgan": "heart",
            "urgencyScore": 95,
            "condition": "Cardiomyopathy",
            "waitingTime": 180
        },
        {
            "id": "RECIPIENT_002",
            "name": "Diana Prince", 
            "age": 29,
            "bloodType": "A+",
            "requiredOrgan": "heart",
            "urgencyScore": 78,
            "condition": "Heart failure",
            "waitingTime": 120
        },
        {
            "id": "RECIPIENT_003",
            "name": "Eva Davis",
            "age": 45,
            "bloodType": "A-",
            "requiredOrgan": "kidney",
            "urgencyScore": 85,
            "condition": "Chronic kidney disease",
            "waitingTime": 200
        },
        {
            "id": "RECIPIENT_004",
            "name": "Frank Miller",
            "age": 38,
            "bloodType": "B+",
            "requiredOrgan": "liver",
            "urgencyScore": 92,
            "condition": "Liver cirrhosis",
            "waitingTime": 150
        }
    ]
    
    return sample_donors, sample_recipients

# CLI Interface
def main():
    import sys
    
    if len(sys.argv) < 2:
        print("\n🤖 LifeConnect AI Engine - Usage:")
        print("=" * 50)
        print("  python match_engine.py test                    # Run comprehensive tests")
        print("  python match_engine.py match <donor_id> <organ> # Find matches for specific organ")
        print("  python match_engine.py analyze                 # Analyze waiting list")
        print("  python match_engine.py gemini-test             # Test Gemini API connection")
        print("\nExample:")
        print("  python match_engine.py match DONOR_001 heart")
        return
    
    ai_engine = LifeConnectAI()
    donors, recipients = load_sample_data()
    
    command = sys.argv[1]
    
    if command == "test":
        print(f"\n{'='*20} AI ENGINE COMPREHENSIVE TEST {'='*20}")
        
        # Test 1: Gemini API connection
        print("\n1️⃣ Testing Gemini API Connection...")
        success, message = ai_engine.test_gemini_connection()
        print(f"   Status: {'✅ Success' if success else '❌ Failed'}")
        print(f"   Message: {message}")
        
        # Test 2: Single algorithmic match
        print("\n2️⃣ Testing Algorithmic Match...")
        donor = donors[0]
        recipient = recipients[0]
        
        print(f"   Donor: {donor['name']} ({donor['organType']}, {donor['bloodType']})")
        print(f"   Recipient: {recipient['name']} ({recipient['requiredOrgan']}, {recipient['bloodType']})")
        
        result = ai_engine.algorithmic_match(donor, recipient)
        print(f"   Match Score: {result['match_score']}/100")
        print(f"   Method: {result['ai_source']}")
        print(f"   Recommendation: {result['recommendation']}")
        
        # Test 3: Batch matching
        print(f"\n3️⃣ Testing Batch Matching...")
        print(f"   Finding matches for {donor['organType']} from {donor['name']}")
        
        matches = ai_engine.find_best_matches(donor, recipients, top_n=3)
        
        for i, match in enumerate(matches, 1):
            recipient_name = match['recipient']['name']
            score = match['match_score']
            method = match['analysis_method']
            print(f"   #{i} {recipient_name}: {score}/100 ({method})")
        
        # Test 4: Waiting list analysis
        print(f"\n4️⃣ Testing Waiting List Analysis...")
        analysis = ai_engine.analyze_waiting_list(recipients)
        
        print(f"   Total Recipients: {analysis['total_recipients']}")
        print(f"   Critical Cases: {analysis['by_urgency']['critical (90-100)']}")
        print(f"   Average Urgency: {analysis['average_urgency']:.1f}")
        
        print("\n   Recommendations:")
        for rec in analysis['recommendations']:
            print(f"     {rec}")
        
        print(f"\n{'='*20} TEST COMPLETE {'='*20}")
    
    elif command == "gemini-test":
        print("\n🧠 Testing Gemini API Connection...")
        success, message = ai_engine.test_gemini_connection()
        print(f"Status: {'✅ Success' if success else '❌ Failed'}")
        print(f"Details: {message}")
        
        if success:
            print("\n🧪 Testing Gemini Match Analysis...")
            donor = donors[0]
            recipient = recipients[0]
            result = ai_engine.get_gemini_match_score(donor, recipient)
            print(f"Gemini Score: {result['match_score']}/100")
            print(f"Confidence: {result.get('confidence', 'Unknown')}")
    
    elif command == "match":
        if len(sys.argv) < 4:
            print("Usage: python match_engine.py match <donor_id> <organ_type>")
            print("Example: python match_engine.py match DONOR_001 heart")
            return
        
        donor_id = sys.argv[2]
        organ_type = sys.argv[3]
        
        # Find donor
        donor = next((d for d in donors if d['id'] == donor_id), None)
        if not donor:
            print(f"❌ Donor {donor_id} not found")
            print(f"Available donors: {[d['id'] for d in donors]}")
            return
        
        donor['organType'] = organ_type
        print(f"\n🎯 Finding matches for {organ_type} from {donor['name']}")
        print(f"   Donor Details: {donor['age']} years old, {donor['bloodType']} blood type")
        
        matches = ai_engine.find_best_matches(donor, recipients)
        
        if matches:
            print(f"\n📊 Top {len(matches)} matches found:")
            for i, match in enumerate(matches, 1):
                recipient = match['recipient']
                print(f"\n{i}. {recipient['name']} - {match['match_score']}/100")
                print(f"   Age: {recipient['age']}, Blood: {recipient['bloodType']}")
                print(f"   Urgency: {recipient['urgencyScore']}/100")
                print(f"   Condition: {recipient['condition']}")
                print(f"   Recommendation: {match['recommendation']}")
                print(f"   Analysis: {match['analysis_method']}")
        else:
            print(f"❌ No qualified matches found (threshold: {ai_engine.match_threshold}%)")
    
    elif command == "analyze":
        print("\n📊 Comprehensive Waiting List Analysis")
        print("=" * 50)
        
        analysis = ai_engine.analyze_waiting_list(recipients)
        
        print(f"📈 Overall Statistics:")
        print(f"   Total Recipients: {analysis['total_recipients']}")
        print(f"   Average Urgency: {analysis['average_urgency']:.1f}/100")
        
        print(f"\n🫀 By Organ Type:")
        for organ, count in analysis['by_organ'].items():
            print(f"   {organ.capitalize()}: {count} patients")
        
        print(f"\n🩸 By Blood Type:")
        for blood, count in analysis['by_blood_type'].items():
            print(f"   {blood}: {count} patients")
        
        print(f"\n⚠️ By Urgency Level:")
        for level, count in analysis['by_urgency'].items():
            print(f"   {level.capitalize()}: {count} patients")
        
        print(f"\n💡 Recommendations:")
        for rec in analysis['recommendations']:
            print(f"   {rec}")

if __name__ == "__main__":
    main()
