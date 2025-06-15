import sys
import os
import logging

# Add paths for component integration
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

sys.path.append(os.path.join(project_root, 'ai_engine'))
sys.path.append(os.path.join(project_root, 'logistics_engine'))
sys.path.append(os.path.join(project_root, 'health_card_generator'))
sys.path.append(os.path.join(project_root, 'ipfs_scripts'))
sys.path.append(os.path.join(project_root, 'blockchain'))

logger = logging.getLogger(__name__)

class ComponentService:
    """Service class to manage all component integrations"""
    
    def __init__(self):
        self.ai_engine = None
        self.logistics_engine = None
        self.health_card_generator = None
        self.initialize_components()
    
    def initialize_components(self):
        """Initialize all component services"""
        try:
            # Initialize AI Engine
            try:
                from match_engine import LifeConnectAI, load_sample_data
                self.ai_engine = LifeConnectAI()
                self.load_sample_data = load_sample_data
                logger.info("AI Engine component initialized")
            except ImportError as e:
                logger.warning(f"AI Engine not available: {e}")
                self.ai_engine = self._create_mock_ai_engine()
            
            # Initialize Logistics Engine
            try:
                from route_optimizer import LifeConnectLogistics
                self.logistics_engine = LifeConnectLogistics()
                logger.info("Logistics Engine component initialized")
            except ImportError as e:
                logger.warning(f"Logistics Engine not available: {e}")
                self.logistics_engine = self._create_mock_logistics_engine()
            
            # Initialize Health Card Generator
            try:
                from health_card_generator import HealthCardGenerator
                self.health_card_generator = HealthCardGenerator()
                logger.info("Health Card Generator component initialized")
            except ImportError as e:
                logger.warning(f"Health Card Generator not available: {e}")
                self.health_card_generator = self._create_mock_health_card_generator()
            
            logger.info("All component services initialized")
            
        except Exception as e:
            logger.error(f"Component initialization error: {e}")
            self._create_mock_services()
    
    def _create_mock_ai_engine(self):
        """Create mock AI engine for testing"""
        class MockAI:
            def find_best_matches(self, donor, recipients, top_n=5):
                return [{"donor": {"name": "Mock Donor"}, "match_score": 85, "recipient": {"name": "Mock Recipient"}}]
            
            def get_compatibility_score(self, donor, recipient):
                return 85
        
        return MockAI()
    
    def _create_mock_logistics_engine(self):
        """Create mock logistics engine for testing"""
        class MockLogistics:
            def create_transport_plan(self, organ_data, pickup, delivery):
                return {
                    "route": {"distance_km": 15.5, "duration_minutes": 45},
                    "vehicle": {"type": "ambulance"}
                }
            
            def monitor_active_transports(self):
                return []
            
            def optimize_organ_transport(self, requests):
                return {"routes": [], "total_distance_km": 0, "total_time_minutes": 0}
        
        return MockLogistics()
    
    def _create_mock_health_card_generator(self):
        """Create mock health card generator for testing"""
        class MockHealthCardGenerator:
            def complete_health_card_workflow(self, patient_data):
                return {
                    "health_card": patient_data,
                    "json_path": "mock.json",
                    "pdf_path": "mock.pdf",
                    "image_path": "mock.png",
                    "ipfs_result": {"cid": "mock_cid"}
                }
            
            @property
            def output_dir(self):
                return "mock_output"
        
        return MockHealthCardGenerator()
    
    def _create_mock_services(self):
        """Create all mock services"""
        self.ai_engine = self._create_mock_ai_engine()
        self.logistics_engine = self._create_mock_logistics_engine()
        self.health_card_generator = self._create_mock_health_card_generator()
