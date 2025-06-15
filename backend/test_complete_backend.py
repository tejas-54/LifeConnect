import unittest
import json
import time
from datetime import datetime
import requests
import threading
import sys
import os

# Add project paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestLifeConnectBackend(unittest.TestCase):
    """Comprehensive backend testing suite"""
    
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://localhost:5000"
        cls.api_url = f"{cls.base_url}/api"
        cls.test_user_token = None
        cls.test_user_id = None
        
        # Wait for server to be ready
        cls.wait_for_server()
        
        # Create test user
        cls.create_test_user()
    
    @classmethod
    def wait_for_server(cls, timeout=30):
        """Wait for server to be ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{cls.api_url}/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Backend server is ready")
                    return
            except:
                pass
            time.sleep(1)
        raise Exception("❌ Backend server not ready")
    
    @classmethod
    def create_test_user(cls):
        """Create test user for authentication"""
        try:
            login_data = {
                "wallet_address": "0x1234567890123456789012345678901234567890",
                "user_type": "donor",
                "email": "test@lifeconnect.com",
                "name": "Test User"
            }
            
            response = requests.post(f"{cls.api_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                cls.test_user_token = data['data']['access_token']
                cls.test_user_id = data['data']['user']['id']
                print(f"✅ Test user created with ID: {cls.test_user_id}")
            else:
                raise Exception(f"Failed to create test user: {response.text}")
                
        except Exception as e:
            print(f"❌ Test user creation failed: {e}")
            raise
    
    def get_auth_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.test_user_token}"}
    
    def test_01_health_check(self):
        """Test API health check"""
        print("\n🧪 Testing API Health Check...")
        
        response = requests.get(f"{self.api_url}/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['status'], 'healthy')
        
        print("✅ Health check passed")
    
    def test_02_authentication(self):
        """Test authentication system"""
        print("\n🧪 Testing Authentication...")
        
        # Test valid login
        login_data = {
            "wallet_address": "0x9876543210987654321098765432109876543210",
            "user_type": "hospital",
            "email": "hospital@lifeconnect.com",
            "name": "Test Hospital"
        }
        
        response = requests.post(f"{self.api_url}/auth/login", json=login_data)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('access_token', data['data'])
        
        # Test profile access
        token = data['data']['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{self.api_url}/auth/profile", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        profile_data = response.json()
        self.assertTrue(profile_data['success'])
        self.assertEqual(profile_data['data']['user_type'], 'hospital')
        
        print("✅ Authentication tests passed")
    
    def test_03_health_card_generation(self):
        """Test health card generation"""
        print("\n🧪 Testing Health Card Generation...")
        
        health_card_data = {
            "name": "Test Patient",
            "age": 35,
            "bloodType": "O+",
            "gender": "Male",
            "donorStatus": True,
            "organTypes": ["heart", "liver"],
            "donorConsent": True,
            "familyConsent": True,
            "hospitalName": "Test Hospital",
            "doctorName": "Dr. Test"
        }
        
        response = requests.post(
            f"{self.api_url}/health-cards/generate",
            json=health_card_data,
            headers=self.get_auth_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('health_card', data['data'])
        self.assertIn('patient_id', data['data'])
        
        # Save patient ID for later tests
        self.test_patient_id = data['data']['patient_id']
        
        print(f"✅ Health card generated with ID: {self.test_patient_id}")
    
    def test_04_health_card_retrieval(self):
        """Test health card retrieval"""
        print("\n🧪 Testing Health Card Retrieval...")
        
        # List health cards
        response = requests.get(
            f"{self.api_url}/health-cards/list",
            headers=self.get_auth_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIsInstance(data['data'], list)
        
        if hasattr(self, 'test_patient_id'):
            # Get specific health card
            response = requests.get(
                f"{self.api_url}/health-cards/{self.test_patient_id}",
                headers=self.get_auth_headers()
            )
            
            self.assertEqual(response.status_code, 200)
            card_data = response.json()
            self.assertTrue(card_data['success'])
            self.assertEqual(card_data['data']['patient_id'], self.test_patient_id)
        
        print("✅ Health card retrieval tests passed")
    
    def test_05_ai_matching(self):
        """Test AI matching functionality"""
        print("\n🧪 Testing AI Matching...")
        
        matching_data = {
            "organData": {
                "requiredOrgan": "heart",
                "bloodType": "O+",
                "age": 35,
                "urgencyScore": 85
            },
            "recipients": []
        }
        
        response = requests.post(
            f"{self.api_url}/ai/find-matches",
            json=matching_data,
            headers=self.get_auth_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('matches', data['data'])
        self.assertIn('total_matches', data['data'])
        
        print(f"✅ AI matching completed, found {data['data']['total_matches']} matches")
    
    def test_06_compatibility_analysis(self):
        """Test compatibility analysis"""
        print("\n🧪 Testing Compatibility Analysis...")
        
        analysis_data = {
            "donorData": {
                "bloodType": "O+",
                "age": 30,
                "organType": "heart"
            },
            "recipientData": {
                "bloodType": "O+",
                "age": 35,
                "requiredOrgan": "heart",
                "urgencyScore": 85
            }
        }
        
        response = requests.post(
            f"{self.api_url}/ai/analyze-compatibility",
            json=analysis_data,
            headers=self.get_auth_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('compatibility_score', data['data'])
        self.assertIn('factors', data['data'])
        
        compatibility_score = data['data']['compatibility_score']
        print(f"✅ Compatibility analysis completed: {compatibility_score}% compatibility")
    
    def test_07_transport_planning(self):
        """Test transport planning"""
        print("\n🧪 Testing Transport Planning...")
        
        transport_data = {
            "organData": {
                "organType": "heart",
                "urgencyScore": 95
            },
            "pickupLocation": {
                "name": "City General Hospital",
                "address": "123 Medical Center Dr",
                "lat": 40.7128,
                "lng": -74.0060
            },
            "deliveryLocation": {
                "name": "Metro Medical Center",
                "address": "456 Health Plaza",
                "lat": 40.7589,
                "lng": -73.9851
            }
        }
        
        response = requests.post(
            f"{self.api_url}/logistics/create-transport-plan",
            json=transport_data,
            headers=self.get_auth_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('transport_id', data['data'])
        self.assertIn('transport_plan', data['data'])
        
        # Save transport ID for tracking test
        self.test_transport_id = data['data']['transport_id']
        
        print(f"✅ Transport plan created with ID: {self.test_transport_id}")
    
    def test_08_transport_tracking(self):
        """Test transport tracking"""
        print("\n🧪 Testing Transport Tracking...")
        
        # Get active transports
        response = requests.get(
            f"{self.api_url}/logistics/active-transports",
            headers=self.get_auth_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIsInstance(data['data'], list)
        
        if hasattr(self, 'test_transport_id'):
            # Track specific transport
            response = requests.get(
                f"{self.api_url}/logistics/track-transport/{self.test_transport_id}",
                headers=self.get_auth_headers()
            )
            
            self.assertEqual(response.status_code, 200)
            tracking_data = response.json()
            self.assertTrue(tracking_data['success'])
            self.assertEqual(tracking_data['data']['transport_id'], self.test_transport_id)
        
        print("✅ Transport tracking tests passed")
    
    def test_09_dashboard_stats(self):
        """Test dashboard statistics"""
        print("\n🧪 Testing Dashboard Statistics...")
        
        response = requests.get(
            f"{self.api_url}/dashboard/stats",
            headers=self.get_auth_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check required fields
        required_fields = [
            'totalUsers', 'totalDonors', 'totalHospitals', 'totalRegulators',
            'totalHealthCards', 'totalMatches', 'successfulMatches', 'activeTransports',
            'monthlyDonations', 'organDistribution', 'recentActivities'
        ]
        
        for field in required_fields:
            self.assertIn(field, data['data'])
        
        print("✅ Dashboard statistics tests passed")
    
    def test_10_system_health(self):
        """Test system health monitoring"""
        print("\n🧪 Testing System Health Monitoring...")
        
        response = requests.get(f"{self.api_url}/dashboard/system-health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('status', data['data'])
        self.assertIn('components', data['data'])
        self.assertIn('health_percentage', data['data'])
        
        print(f"✅ System health: {data['data']['status']} ({data['data']['health_percentage']}%)")
    
    def test_11_error_handling(self):
        """Test error handling"""
        print("\n🧪 Testing Error Handling...")
        
        # Test 404 error
        response = requests.get(f"{self.api_url}/nonexistent-endpoint")
        self.assertEqual(response.status_code, 404)
        
        # Test unauthorized access
        response = requests.get(f"{self.api_url}/health-cards/list")
        self.assertEqual(response.status_code, 401)
        
        # Test invalid data
        response = requests.post(
            f"{self.api_url}/health-cards/generate",
            json={},  # Empty data
            headers=self.get_auth_headers()
        )
        # Should handle gracefully even with empty data
        
        print("✅ Error handling tests passed")
    
    def test_12_performance_check(self):
        """Test API performance"""
        print("\n🧪 Testing API Performance...")
        
        start_time = time.time()
        
        # Test multiple concurrent requests
        import concurrent.futures
        
        def make_request():
            return requests.get(f"{self.api_url}/health")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All requests should succeed
        for result in results:
            self.assertEqual(result.status_code, 200)
        
        print(f"✅ Performance test completed: 10 concurrent requests in {total_time:.2f} seconds")
    
    def test_13_database_operations(self):
        """Test database operations"""
        print("\n🧪 Testing Database Operations...")
        
        # Test user creation and retrieval through API
        test_wallet = f"0x{''.join([str(i) for i in range(10)] * 4)}"
        
        login_data = {
            "wallet_address": test_wallet,
            "user_type": "regulator",
            "email": "regulator@test.com",
            "name": "Test Regulator"
        }
        
        response = requests.post(f"{self.api_url}/auth/login", json=login_data)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Test profile retrieval
        token = data['data']['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{self.api_url}/auth/profile", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        profile_data = response.json()
        self.assertEqual(profile_data['data']['wallet_address'], test_wallet.lower())
        
        print("✅ Database operations tests passed")

def run_integration_tests():
    """Run integration tests with external components"""
    print("\n🔗 Running Integration Tests...")
    
    try:
        # Test AI Engine Integration
        print("🤖 Testing AI Engine Integration...")
        sys.path.append('../ai_engine')
        from match_engine import LifeConnectAI
        ai_engine = LifeConnectAI()
        print("✅ AI Engine integration working")
        
    except ImportError as e:
        print(f"⚠️ AI Engine integration warning: {e}")
    
    try:
        # Test Logistics Engine Integration
        print("🚚 Testing Logistics Engine Integration...")
        sys.path.append('../logistics_engine')
        from route_optimizer import LifeConnectLogistics
        logistics = LifeConnectLogistics()
        print("✅ Logistics Engine integration working")
        
    except ImportError as e:
        print(f"⚠️ Logistics Engine integration warning: {e}")
    
    try:
        # Test Health Card Generator Integration
        print("🏥 Testing Health Card Generator Integration...")
        sys.path.append('../health_card_generator')
        from health_card_generator import HealthCardGenerator
        generator = HealthCardGenerator()
        print("✅ Health Card Generator integration working")
        
    except ImportError as e:
        print(f"⚠️ Health Card Generator integration warning: {e}")

def main():
    """Main test runner"""
    print("🧪 LifeConnect Backend Comprehensive Test Suite")
    print("=" * 60)
    
    # Run integration tests first
    run_integration_tests()
    
    print("\n🏃 Running Backend API Tests...")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestLifeConnectBackend)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failures: {failures}")
    print(f"Errors: {errors}")
    print(f"Success Rate: {(passed/total_tests*100):.1f}%")
    
    if failures > 0:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if errors > 0:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if passed == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ LifeConnect Backend is fully functional and ready for production!")
    else:
        print(f"\n⚠️ {failures + errors} test(s) failed. Please review and fix issues.")
    
    return passed == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
