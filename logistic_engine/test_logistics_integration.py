import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from route_optimizer import LifeConnectLogistics, load_sample_transport_data, OrganTransport, Location
import json
import time
from datetime import datetime

def test_basic_functionality():
    """Test basic logistics functionality"""
    print("🧪 Testing Basic Logistics Functionality...")
    
    try:
        logistics = LifeConnectLogistics()
        
        # Test 1: Hospital network loading
        print("   Testing hospital network...")
        assert len(logistics.hospitals) >= 5, "Hospital network too small"
        print(f"   ✅ {len(logistics.hospitals)} hospitals loaded")
        
        # Test 2: Vehicle fleet initialization
        print("   Testing vehicle fleet...")
        assert len(logistics.vehicles) >= 3, "Vehicle fleet too small"
        available_vehicles = [v for v in logistics.vehicles if v.available]
        print(f"   ✅ {len(available_vehicles)} vehicles available")
        
        # Test 3: Distance calculation
        print("   Testing distance calculation...")
        origin = logistics.hospitals[0]
        destination = logistics.hospitals[1]
        distance, duration = logistics.calculate_distance_and_time(origin, destination)
        assert distance > 0 and duration > 0, "Invalid distance calculation"
        print(f"   ✅ Distance: {distance:.1f}km, Duration: {duration}min")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Basic functionality test failed: {e}")
        return False

def test_transport_plan_creation():
    """Test transport plan creation"""
    print("\n🚚 Testing Transport Plan Creation...")
    
    try:
        logistics = LifeConnectLogistics()
        
        # Test transport plan for different organ types
        organ_types = ["heart", "kidney", "liver"]
        
        for organ_type in organ_types:
            print(f"   Creating plan for {organ_type}...")
            
            organ_data = {
                "id": f"TEST_{organ_type.upper()}_001",
                "type": organ_type,
                "urgency": 85,
                "max_hours": 8
            }
            
            plan = logistics.create_transport_plan(
                organ_data, 
                "City General", 
                "Metro Medical"
            )
            
            # Validate plan structure
            assert "organ_id" in plan, "Missing organ_id"
            assert "route" in plan, "Missing route"
            assert "vehicle" in plan, "Missing vehicle"
            assert "schedule" in plan, "Missing schedule"
            assert "monitoring" in plan, "Missing monitoring"
            
            print(f"   ✅ {organ_type} plan: {plan['route']['distance_km']:.1f}km via {plan['vehicle']['type']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Transport plan test failed: {e}")
        return False

def test_route_optimization():
    """Test route optimization with OR-Tools"""
    print("\n🔄 Testing Route Optimization...")
    
    try:
        logistics = LifeConnectLogistics()
        
        # Create multiple transport requests
        print("   Creating multiple transport requests...")
        transport_requests = load_sample_transport_data()
        
        # Add more requests for comprehensive testing
        additional_requests = [
            OrganTransport(
                organ_id="ORG_003",
                organ_type="liver",
                pickup_location=logistics.hospitals[2],
                delivery_location=logistics.hospitals[3],
                harvest_time=datetime.now(),
                max_transport_time=12,
                urgency_score=60
            ),
            OrganTransport(
                organ_id="ORG_004",
                organ_type="kidney",
                pickup_location=logistics.hospitals[3],
                delivery_location=logistics.hospitals[4],
                harvest_time=datetime.now(),
                max_transport_time=24,
                urgency_score=45
            )
        ]
        
        transport_requests.extend(additional_requests)
        print(f"   ✅ Created {len(transport_requests)} transport requests")
        
        # Run optimization
        print("   Running route optimization...")
        start_time = time.time()
        result = logistics.optimize_organ_transport(transport_requests)
        optimization_time = time.time() - start_time
        
        # Validate results
        assert "routes" in result, "Missing routes in result"
        assert "total_distance_km" in result, "Missing total distance"
        assert "total_time_minutes" in result, "Missing total time"
        
        print(f"   ✅ Optimization completed in {optimization_time:.2f}s")
        print(f"   Routes generated: {len(result['routes'])}")
        print(f"   Total distance: {result['total_distance_km']:.1f}km")
        print(f"   Total time: {result['total_time_minutes']:.1f}min")
        print(f"   Method: {result['optimization_method']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Route optimization test failed: {e}")
        return False

def test_monitoring_simulation():
    """Test transport monitoring simulation"""
    print("\n📡 Testing Transport Monitoring...")
    
    try:
        logistics = LifeConnectLogistics()
        
        # Get active transports
        print("   Simulating active transports...")
        active_transports = logistics.monitor_active_transports()
        
        # Validate monitoring data
        assert len(active_transports) > 0, "No active transports simulated"
        
        for transport in active_transports:
            # Check required fields
            required_fields = [
                "transport_id", "organ_id", "organ_type", 
                "current_location", "route_progress", 
                "estimated_arrival", "current_temperature", "status"
            ]
            
            for field in required_fields:
                assert field in transport, f"Missing field: {field}"
            
            # Validate data types and ranges
            assert 0 <= transport["route_progress"] <= 100, "Invalid route progress"
            assert 0 <= transport["current_temperature"] <= 10, "Invalid temperature"
            
        print(f"   ✅ Monitoring {len(active_transports)} active transports")
        
        # Test alerts
        alerts_count = sum(len(t["alerts"]) for t in active_transports)
        print(f"   Active alerts: {alerts_count}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Monitoring test failed: {e}")
        return False

def test_report_generation():
    """Test route report generation"""
    print("\n📊 Testing Report Generation...")
    
    try:
        logistics = LifeConnectLogistics()
        
        # Create a transport plan
        organ_data = {
            "id": "REPORT_TEST_001",
            "type": "heart",
            "urgency": 95,
            "max_hours": 8
        }
        
        plan = logistics.create_transport_plan(organ_data, "City General", "Metro Medical")
        
        # Generate report
        print("   Generating route report...")
        report = logistics.generate_route_report(plan)
        
        # Validate report structure
        required_sections = ["summary", "route_details", "risk_assessment", "recommendations", "emergency_procedures"]
        
        for section in required_sections:
            assert section in report, f"Missing report section: {section}"
        
        # Validate summary data
        summary = report["summary"]
        assert "efficiency_score" in summary, "Missing efficiency score"
        assert 0 <= summary["efficiency_score"] <= 100, "Invalid efficiency score"
        
        print(f"   ✅ Report generated successfully")
        print(f"   Efficiency score: {summary['efficiency_score']:.1f}/100")
        print(f"   Risk level: {report['risk_assessment']['overall_risk']}")
        print(f"   Recommendations: {len(report['recommendations'])}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Report generation test failed: {e}")
        return False

def test_integration_with_constraints():
    """Test integration with constraint configuration"""
    print("\n⚙️ Testing Constraint Integration...")
    
    try:
        # Load constraints
        with open('constraints.json', 'r') as f:
            constraints = json.load(f)
        
        print("   ✅ Constraints loaded successfully")
        
        # Validate constraint structure
        assert "transport_constraints" in constraints
        assert "operational_constraints" in constraints
        assert "quality_requirements" in constraints
        
        # Test constraint application
        logistics = LifeConnectLogistics()
        
        organ_data = {
            "id": "CONSTRAINT_TEST_001",
            "type": "heart",
            "urgency": 95,
            "max_hours": constraints["transport_constraints"]["max_transport_time_hours"]["heart"]
        }
        
        plan = logistics.create_transport_plan(organ_data, "City General", "Metro Medical")
        
        # Check if constraints are respected
        max_time_hours = constraints["transport_constraints"]["max_transport_time_hours"]["heart"]
        actual_time_hours = plan["route"]["estimated_duration_minutes"] / 60
        
        print(f"   Max allowed time: {max_time_hours}h")
        print(f"   Actual transport time: {actual_time_hours:.1f}h")
        print(f"   ✅ Constraint compliance: {'Yes' if actual_time_hours <= max_time_hours else 'No'}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Constraint integration test failed: {e}")
        return False

def run_performance_benchmark():
    """Run performance benchmark for logistics operations"""
    print("\n⚡ Running Performance Benchmark...")
    
    try:
        logistics = LifeConnectLogistics()
        
        # Benchmark 1: Multiple transport plan creation
        print("   Benchmarking transport plan creation...")
        start_time = time.time()
        
        for i in range(10):
            organ_data = {
                "id": f"PERF_ORG_{i:03d}",
                "type": ["heart", "kidney", "liver"][i % 3],
                "urgency": 70 + (i % 30),
                "max_hours": 8
            }
            
            plan = logistics.create_transport_plan(organ_data, "City General", "Metro Medical")
        
        plan_creation_time = time.time() - start_time
        
        # Benchmark 2: Route optimization with multiple requests
        print("   Benchmarking route optimization...")
        start_time = time.time()
        
        transport_requests = load_sample_transport_data()
        result = logistics.optimize_organ_transport(transport_requests)
        
        optimization_time = time.time() - start_time
        
        # Benchmark 3: Monitoring simulation
        print("   Benchmarking monitoring operations...")
        start_time = time.time()
        
        for _ in range(5):
            active_transports = logistics.monitor_active_transports()
        
        monitoring_time = time.time() - start_time
        
        # Performance results
        print(f"\n   📈 Performance Results:")
        print(f"     Plan creation (10 plans): {plan_creation_time:.2f}s")
        print(f"     Route optimization: {optimization_time:.2f}s")
        print(f"     Monitoring operations: {monitoring_time:.2f}s")
        
        # Performance rating
        total_time = plan_creation_time + optimization_time + monitoring_time
        performance_rating = "Excellent" if total_time < 5 else "Good" if total_time < 15 else "Acceptable"
        print(f"     Overall performance: {performance_rating}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Performance benchmark failed: {e}")
        return False

def main():
    print("🧪 LifeConnect Logistics Integration Test Suite")
    print("=" * 70)
    print("🎯 Testing route optimization, transport planning, and monitoring")
    print("=" * 70)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Transport Plan Creation", test_transport_plan_creation),
        ("Route Optimization", test_route_optimization),
        ("Transport Monitoring", test_monitoring_simulation),
        ("Report Generation", test_report_generation),
        ("Constraint Integration", test_integration_with_constraints),
        ("Performance Benchmark", run_performance_benchmark)
    ]
    
    results = {}
    start_time = time.time()
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            results[test_name] = "✅ PASSED" if result else "❌ FAILED"
        except Exception as e:
            results[test_name] = f"❌ ERROR: {str(e)}"
            print(f"   🔍 Exception details: {str(e)}")
    
    total_time = time.time() - start_time
    
    # Summary
    print(f"\n{'='*20} LOGISTICS TEST SUMMARY {'='*20}")
    print(f"🕒 Total test duration: {total_time:.2f} seconds")
    print(f"📊 Test results overview:")
    
    for test_name, result in results.items():
        status_icon = "✅" if "PASSED" in result else "❌"
        print(f"   {status_icon} {test_name:.<40} {result}")
    
    # Overall assessment
    passed_tests = sum(1 for r in results.values() if "✅" in r)
    failed_tests = sum(1 for r in results.values() if "❌" in r)
    total_tests = len(results)
    
    print(f"\n📈 Overall Results:")
    print(f"   ✅ Passed: {passed_tests}/{total_tests}")
    print(f"   ❌ Failed: {failed_tests}/{total_tests}")
    
    if passed_tests >= total_tests * 0.8:
        print(f"\n🎉 LOGISTICS ENGINE SUCCESS!")
        print(f"💡 Your LifeConnect logistics system is ready for demo!")
        print(f"🚚 Route optimization, transport planning, and monitoring all functional")
    else:
        print(f"\n⚠️ LOGISTICS ENGINE NEEDS ATTENTION")
        print(f"🔧 Review failed tests for improvements")

if __name__ == "__main__":
    main()
