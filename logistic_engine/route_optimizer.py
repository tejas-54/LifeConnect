import os
import json
import time
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from geopy.distance import geodesic
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Location:
    """Represents a geographic location"""
    name: str
    address: str
    lat: float
    lng: float
    location_type: str  # 'hospital', 'warehouse', 'checkpoint'
    contact: str = ""
    
@dataclass
class OrganTransport:
    """Represents an organ transport request"""
    organ_id: str
    organ_type: str
    pickup_location: Location
    delivery_location: Location
    harvest_time: datetime
    max_transport_time: int  # hours
    urgency_score: int
    temperature_required: float = 4.0  # Celsius
    special_requirements: List[str] = None

@dataclass
class TransportVehicle:
    """Represents a transport vehicle"""
    vehicle_id: str
    vehicle_type: str  # 'ambulance', 'helicopter', 'medical_van'
    current_location: Location
    capacity: int
    speed_kmh: float
    available: bool = True
    temperature_controlled: bool = True

class LifeConnectLogistics:
    def __init__(self):
        self.google_maps_key = os.getenv('GOOGLE_MAPS_API_KEY')
        
        # Load hospital network and checkpoints
        self.hospitals = self._load_hospital_network()
        self.checkpoints = self._load_checkpoints()
        self.vehicles = self._initialize_vehicle_fleet()
        
        print("🚚 LifeConnect Logistics Engine initialized")
        print(f"   Google Maps API: {'✅ Configured' if self.google_maps_key else '❌ Not configured'}")
        print(f"   Hospital Network: {len(self.hospitals)} hospitals loaded")
        print(f"   Vehicle Fleet: {len(self.vehicles)} vehicles available")

    def _load_hospital_network(self) -> List[Location]:
        """Load major hospitals and medical centers"""
        hospitals = [
            Location("City General Hospital", "123 Medical Center Dr, Downtown, New York, NY", 40.7128, -74.0060, "hospital", "+1-555-0123"),
            Location("Metro Medical Center", "456 Health Plaza, Uptown, New York, NY", 40.7589, -73.9851, "hospital", "+1-555-0456"),
            Location("Regional Trauma Center", "789 Emergency Ave, Midtown, New York, NY", 40.7505, -73.9934, "hospital", "+1-555-0789"),
            Location("University Hospital", "321 Campus Blvd, University District, New York, NY", 40.7282, -73.9942, "hospital", "+1-555-0321"),
            Location("Specialty Transplant Center", "654 Organ Ave, Medical District, New York, NY", 40.7614, -73.9776, "hospital", "+1-555-0654"),
        ]
        return hospitals

    def _load_checkpoints(self) -> List[Location]:
        """Load strategic checkpoints for monitoring"""
        checkpoints = [
            Location("Highway Junction A", "Interstate 95 & Route 1, New York, NY", 40.7305, -74.0031, "checkpoint"),
            Location("Medical District Bridge", "Health Sciences Bridge, New York, NY", 40.7421, -73.9897, "checkpoint"),
            Location("Airport Medical Hub", "JFK International Airport, Queens, NY", 40.6413, -73.7781, "checkpoint"),
            Location("Emergency Relay Station", "Central Emergency Services, New York, NY", 40.7831, -73.9712, "checkpoint"),
        ]
        return checkpoints

    def _initialize_vehicle_fleet(self) -> List[TransportVehicle]:
        """Initialize available transport vehicles"""
        vehicles = [
            TransportVehicle("MED001", "medical_helicopter", self.hospitals[0], 2, 200, True, True),
            TransportVehicle("AMB001", "ambulance", self.hospitals[1], 4, 80, True, True),
            TransportVehicle("AMB002", "ambulance", self.hospitals[2], 4, 80, True, True),
            TransportVehicle("VAN001", "medical_van", self.hospitals[3], 6, 60, True, True),
            TransportVehicle("MED002", "medical_helicopter", self.hospitals[4], 2, 200, True, True),
        ]
        return vehicles

    def geocode_address_google(self, address: str) -> Tuple[float, float]:
        """Convert address to coordinates using Google Maps Geocoding API"""
        if not self.google_maps_key:
            print("⚠️ Google Maps API key not configured, using fallback coordinates")
            return 40.7128, -74.0060
        
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': address,
                'key': self.google_maps_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data['status'] == 'OK' and data['results']:
                    location = data['results'][0]['geometry']['location']
                    lat, lng = location['lat'], location['lng']
                    print(f"🗺️ Google Geocoded: {address[:30]}... → ({lat:.4f}, {lng:.4f})")
                    return lat, lng
                else:
                    print(f"⚠️ Geocoding failed: {data.get('status', 'Unknown error')}")
                    return 40.7128, -74.0060
            else:
                print(f"❌ Geocoding HTTP error: {response.status_code}")
                return 40.7128, -74.0060
                
        except requests.exceptions.Timeout:
            print(f"⏰ Geocoding timeout for address: {address[:30]}...")
            return 40.7128, -74.0060
        except Exception as e:
            print(f"❌ Geocoding error: {str(e)}")
            return 40.7128, -74.0060

    def calculate_distance_and_time(self, origin: Location, destination: Location, 
                                  transport_mode: str = "driving") -> Tuple[float, int]:
        """Calculate distance and travel time using Google Maps Directions API"""
        try:
            if self.google_maps_key:
                return self._get_google_directions(origin, destination, transport_mode)
            else:
                print("⚠️ Google Maps API not configured, using geodesic calculation")
                return self._calculate_geodesic_route(origin, destination, transport_mode)
                
        except Exception as e:
            print(f"❌ Route calculation error: {e}")
            return self._calculate_geodesic_route(origin, destination, transport_mode)

    def _get_google_directions(self, origin: Location, destination: Location, 
                              transport_mode: str) -> Tuple[float, int]:
        """Get route information from Google Maps Directions API"""
        try:
            # Map transport modes to Google Maps modes
            mode_mapping = {
                "medical_helicopter": "driving",  # No helicopter mode in API
                "ambulance": "driving",
                "medical_van": "driving",
                "driving": "driving"
            }
            
            travel_mode = mode_mapping.get(transport_mode, "driving")
            
            url = "https://maps.googleapis.com/maps/api/directions/json"
            params = {
                'origin': f"{origin.lat},{origin.lng}",
                'destination': f"{destination.lat},{destination.lng}",
                'mode': travel_mode,
                'key': self.google_maps_key,
                'units': 'metric',
                'avoid': 'tolls',  # Avoid tolls for emergency vehicles
                'departure_time': 'now'
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data['status'] == 'OK' and data['routes']:
                    route = data['routes'][0]['legs'][0]
                    
                    distance_km = route['distance']['value'] / 1000  # Convert to km
                    duration_min = route['duration']['value'] / 60    # Convert to minutes
                    
                    # Adjust for special vehicles
                    if transport_mode == "medical_helicopter":
                        # Helicopters are faster and can take direct routes
                        duration_min = duration_min * 0.4  # 60% time reduction
                        distance_km = distance_km * 0.7    # More direct route
                    elif transport_mode == "ambulance":
                        # Ambulances can use emergency lanes and have traffic priority
                        duration_min = duration_min * 0.7  # 30% time reduction
                    
                    print(f"🗺️ Google Directions: {distance_km:.1f}km, {duration_min:.1f}min ({transport_mode})")
                    return distance_km, int(duration_min)
                else:
                    print(f"⚠️ Directions failed: {data.get('status', 'Unknown')}")
                    return self._calculate_geodesic_route(origin, destination, transport_mode)
            else:
                print(f"❌ Directions HTTP error: {response.status_code}")
                return self._calculate_geodesic_route(origin, destination, transport_mode)
                
        except requests.exceptions.Timeout:
            print(f"⏰ Google Directions timeout")
            return self._calculate_geodesic_route(origin, destination, transport_mode)
        except Exception as e:
            print(f"❌ Google Directions error: {e}")
            return self._calculate_geodesic_route(origin, destination, transport_mode)

    def _calculate_geodesic_route(self, origin: Location, destination: Location, 
                                 transport_mode: str) -> Tuple[float, int]:
        """Calculate route using geodesic distance (fallback)"""
        distance_km = geodesic((origin.lat, origin.lng), (destination.lat, destination.lng)).kilometers
        
        # Estimate travel time based on transport mode
        speed_map = {
            "medical_helicopter": 200,  # km/h
            "ambulance": 60,           # km/h (city driving)
            "medical_van": 50,         # km/h
            "driving": 60              # default
        }
        
        avg_speed = speed_map.get(transport_mode, 60)
        duration_min = (distance_km / avg_speed) * 60
        
        print(f"📐 Geodesic route: {distance_km:.1f}km, {duration_min:.1f}min")
        return distance_km, int(duration_min)

    def test_google_maps_connectivity(self) -> Dict:
        """Test Google Maps API connectivity"""
        if not self.google_maps_key:
            return {
                'api_configured': False,
                'geocoding_working': False,
                'directions_working': False,
                'message': 'Google Maps API key not configured'
            }
        
        results = {
            'api_configured': True,
            'geocoding_working': False,
            'directions_working': False,
            'message': ''
        }
        
        # Test geocoding
        try:
            lat, lng = self.geocode_address_google("Times Square, New York, NY")
            if 40.0 < lat < 41.0 and -75.0 < lng < -73.0:  # Reasonable NYC coordinates
                results['geocoding_working'] = True
                print("✅ Google Geocoding API working")
            else:
                print("⚠️ Google Geocoding returned unexpected coordinates")
        except Exception as e:
            print(f"❌ Google Geocoding test failed: {e}")
        
        # Test directions
        try:
            origin = Location("Test Origin", "Times Square, NY", 40.7580, -73.9855, "test")
            destination = Location("Test Dest", "Central Park, NY", 40.7812, -73.9665, "test")
            distance, duration = self._get_google_directions(origin, destination, "driving")
            
            if distance > 0 and duration > 0:
                results['directions_working'] = True
                print("✅ Google Directions API working")
            else:
                print("⚠️ Google Directions returned invalid data")
        except Exception as e:
            print(f"❌ Google Directions test failed: {e}")
        
        # Overall status
        if results['geocoding_working'] and results['directions_working']:
            results['message'] = 'All Google Maps APIs working correctly'
        elif results['geocoding_working'] or results['directions_working']:
            results['message'] = 'Some Google Maps APIs working, fallback available'
        else:
            results['message'] = 'Google Maps APIs not working, using fallback methods'
        
        return results

    def optimize_organ_transport(self, transport_requests: List[OrganTransport]) -> Dict:
        """Optimize multiple organ transport routes using OR-Tools"""
        print(f"🔄 Optimizing routes for {len(transport_requests)} organ transports...")
        
        if not transport_requests:
            return {"routes": [], "total_time": 0, "total_distance": 0}
        
        # Create distance matrix
        locations = []
        for request in transport_requests:
            locations.extend([request.pickup_location, request.delivery_location])
        
        # Remove duplicates while preserving order
        unique_locations = []
        seen = set()
        for loc in locations:
            loc_key = (loc.lat, loc.lng)
            if loc_key not in seen:
                unique_locations.append(loc)
                seen.add(loc_key)
        
        distance_matrix = self._create_distance_matrix(unique_locations)
        
        # Solve with OR-Tools
        solution = self._solve_vrp(distance_matrix, transport_requests, unique_locations)
        
        return solution

    def _create_distance_matrix(self, locations: List[Location]) -> List[List[int]]:
        """Create distance matrix for OR-Tools"""
        print(f"📊 Creating distance matrix for {len(locations)} locations...")
        
        matrix = []
        for i, origin in enumerate(locations):
            row = []
            for j, destination in enumerate(locations):
                if i == j:
                    row.append(0)
                else:
                    distance_km, duration_min = self.calculate_distance_and_time(origin, destination)
                    row.append(duration_min)  # Use time as distance metric
            matrix.append(row)
        
        print(f"✅ Distance matrix created: {len(matrix)}x{len(matrix[0])}")
        return matrix

    def _solve_vrp(self, distance_matrix: List[List[int]], 
                   transport_requests: List[OrganTransport], 
                   locations: List[Location]) -> Dict:
        """Solve Vehicle Routing Problem with OR-Tools"""
        try:
            # Create the routing index manager
            manager = pywrapcp.RoutingIndexManager(
                len(distance_matrix),
                min(len(self.vehicles), len(transport_requests)),  # Number of vehicles
                0  # Depot index (start location)
            )
            
            # Create Routing Model
            routing = pywrapcp.RoutingModel(manager)
            
            # Create distance callback
            def distance_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                return distance_matrix[from_node][to_node]
            
            transit_callback_index = routing.RegisterTransitCallback(distance_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
            
            # Add time window constraints
            time = "Time"
            routing.AddDimension(
                transit_callback_index,
                30,  # allow waiting time
                720,  # maximum time per vehicle (12 hours)
                False,  # Don't force start cumul to zero
                time
            )
            time_dimension = routing.GetDimensionOrDie(time)
            
            # Add time windows for urgent organs
            for i, request in enumerate(transport_requests):
                if request.urgency_score > 80:
                    # High urgency - tight time window
                    pickup_index = manager.NodeToIndex(i * 2)
                    delivery_index = manager.NodeToIndex(i * 2 + 1)
                    
                    time_dimension.CumulVar(pickup_index).SetRange(0, 60)  # Pick up within 1 hour
                    time_dimension.CumulVar(delivery_index).SetRange(0, request.max_transport_time * 60)
            
            # Setting first solution heuristic
            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            )
            search_parameters.local_search_metaheuristic = (
                routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
            )
            search_parameters.time_limit.FromSeconds(30)
            
            # Solve the problem
            print("🔍 Solving VRP with OR-Tools...")
            solution = routing.SolveWithParameters(search_parameters)
            
            if solution:
                return self._extract_solution(manager, routing, solution, transport_requests, locations)
            else:
                print("⚠️ No solution found, using fallback routing")
                return self._create_fallback_solution(transport_requests)
                
        except Exception as e:
            print(f"❌ OR-Tools VRP error: {e}")
            return self._create_fallback_solution(transport_requests)

    def _extract_solution(self, manager, routing, solution, 
                         transport_requests: List[OrganTransport], 
                         locations: List[Location]) -> Dict:
        """Extract solution from OR-Tools solver"""
        print("✅ OR-Tools solution found!")
        
        routes = []
        total_distance = 0
        total_time = 0
        
        for vehicle_id in range(min(len(self.vehicles), len(transport_requests))):
            index = routing.Start(vehicle_id)
            route_distance = 0
            route_time = 0
            route_locations = []
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                if node_index < len(locations):
                    route_locations.append(locations[node_index])
                
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
            
            # Add final location
            final_node = manager.IndexToNode(index)
            if final_node < len(locations):
                route_locations.append(locations[final_node])
            
            if len(route_locations) > 2:  # Only include routes with actual stops
                vehicle = self.vehicles[vehicle_id]
                route_info = {
                    "vehicle": vehicle,
                    "locations": route_locations,
                    "distance_km": route_distance * 0.06,  # Rough conversion
                    "time_minutes": route_distance,
                    "organs_transported": []
                }
                
                # Map organs to this route
                for request in transport_requests:
                    if request.pickup_location in route_locations:
                        route_info["organs_transported"].append(request.organ_id)
                
                routes.append(route_info)
                total_distance += route_info["distance_km"]
                total_time += route_info["time_minutes"]
        
        return {
            "routes": routes,
            "total_distance_km": total_distance,
            "total_time_minutes": total_time,
            "optimization_method": "or_tools",
            "vehicles_used": len(routes)
        }

    def _create_fallback_solution(self, transport_requests: List[OrganTransport]) -> Dict:
        """Create fallback solution when OR-Tools fails"""
        print("🔄 Creating fallback routing solution...")
        
        routes = []
        total_distance = 0
        total_time = 0
        
        for i, request in enumerate(transport_requests):
            if i < len(self.vehicles):
                vehicle = self.vehicles[i]
                distance, duration = self.calculate_distance_and_time(
                    request.pickup_location, 
                    request.delivery_location,
                    vehicle.vehicle_type
                )
                
                route = {
                    "vehicle": vehicle,
                    "locations": [request.pickup_location, request.delivery_location],
                    "distance_km": distance,
                    "time_minutes": duration,
                    "organs_transported": [request.organ_id]
                }
                
                routes.append(route)
                total_distance += distance
                total_time += duration
        
        return {
            "routes": routes,
            "total_distance_km": total_distance,
            "total_time_minutes": total_time,
            "optimization_method": "fallback_direct",
            "vehicles_used": len(routes)
        }

    def create_transport_plan(self, organ_data: Dict, pickup_hospital: str, 
                            delivery_hospital: str) -> Dict:
        """Create comprehensive transport plan for single organ"""
        print(f"📋 Creating transport plan for organ {organ_data.get('id', 'Unknown')}")
        
        # Find hospitals
        pickup_loc = self._find_hospital(pickup_hospital)
        delivery_loc = self._find_hospital(delivery_hospital)
        
        if not pickup_loc or not delivery_loc:
            raise ValueError("Hospital not found in network")
        
        # Calculate route
        distance, duration = self.calculate_distance_and_time(pickup_loc, delivery_loc)
        
        # Select best vehicle
        best_vehicle = self._select_best_vehicle(pickup_loc, distance, organ_data)
        
        # Create detailed plan
        transport_plan = {
            "organ_id": organ_data.get('id', f"ORG_{int(time.time())}"),
            "organ_type": organ_data.get('type', 'unknown'),
            "route": {
                "pickup": {
                    "hospital": pickup_loc.name,
                    "address": pickup_loc.address,
                    "coordinates": [pickup_loc.lat, pickup_loc.lng],
                    "contact": pickup_loc.contact
                },
                "delivery": {
                    "hospital": delivery_loc.name,
                    "address": delivery_loc.address,
                    "coordinates": [delivery_loc.lat, delivery_loc.lng],
                    "contact": delivery_loc.contact
                },
                "distance_km": distance,
                "estimated_duration_minutes": duration,
                "checkpoints": self._get_route_checkpoints(pickup_loc, delivery_loc)
            },
            "vehicle": {
                "id": best_vehicle.vehicle_id,
                "type": best_vehicle.vehicle_type,
                "speed_kmh": best_vehicle.speed_kmh,
                "temperature_controlled": best_vehicle.temperature_controlled
            },
            "schedule": {
                "pickup_time": datetime.now().isoformat(),
                "estimated_delivery": (datetime.now() + timedelta(minutes=duration)).isoformat(),
                "max_transport_time_hours": organ_data.get('max_hours', 8),
                "buffer_time_minutes": 30
            },
            "monitoring": {
                "temperature_target": 4.0,
                "gps_tracking": True,
                "real_time_updates": True,
                "emergency_contacts": [pickup_loc.contact, delivery_loc.contact]
            },
            "compliance": {
                "documentation_required": True,
                "chain_of_custody": True,
                "quality_checks": ["temperature", "packaging", "time"]
            },
            "created_at": datetime.now().isoformat(),
            "status": "planned"
        }
        
        print(f"✅ Transport plan created: {distance:.1f}km, {duration}min via {best_vehicle.vehicle_type}")
        return transport_plan

    def _find_hospital(self, hospital_name: str) -> Optional[Location]:
        """Find hospital by name or partial match"""
        for hospital in self.hospitals:
            if hospital_name.lower() in hospital.name.lower():
                return hospital
        return None

    def _select_best_vehicle(self, pickup_location: Location, distance: float, 
                           organ_data: Dict) -> TransportVehicle:
        """Select best vehicle for transport based on multiple factors"""
        available_vehicles = [v for v in self.vehicles if v.available]
        
        if not available_vehicles:
            return self.vehicles[0]  # Fallback
        
        # Score vehicles based on suitability
        best_vehicle = available_vehicles[0]
        best_score = 0
        
        for vehicle in available_vehicles:
            score = 0
            
            # Distance to pickup location
            pickup_distance = geodesic(
                (vehicle.current_location.lat, vehicle.current_location.lng),
                (pickup_location.lat, pickup_location.lng)
            ).kilometers
            
            score += max(0, 100 - pickup_distance)  # Closer is better
            
            # Vehicle type suitability
            urgency = organ_data.get('urgency', 50)
            if urgency > 90 and vehicle.vehicle_type == "medical_helicopter":
                score += 50  # Helicopter for urgent cases
            elif vehicle.vehicle_type == "ambulance":
                score += 30  # Ambulance is versatile
            
            # Speed factor
            score += vehicle.speed_kmh / 10
            
            if score > best_score:
                best_score = score
                best_vehicle = vehicle
        
        return best_vehicle

    def _get_route_checkpoints(self, pickup: Location, delivery: Location) -> List[Dict]:
        """Get checkpoints along the route for monitoring"""
        checkpoints = []
        
        # Find checkpoints between pickup and delivery
        for checkpoint in self.checkpoints:
            # Simple distance-based selection (can be improved with actual route planning)
            pickup_dist = geodesic((pickup.lat, pickup.lng), 
                                 (checkpoint.lat, checkpoint.lng)).kilometers
            delivery_dist = geodesic((delivery.lat, delivery.lng), 
                                   (checkpoint.lat, checkpoint.lng)).kilometers
            total_route_dist = geodesic((pickup.lat, pickup.lng), 
                                      (delivery.lat, delivery.lng)).kilometers
            
            # Include checkpoint if it's roughly along the route
            if pickup_dist + delivery_dist <= total_route_dist * 1.2:
                checkpoints.append({
                    "name": checkpoint.name,
                    "address": checkpoint.address,
                    "coordinates": [checkpoint.lat, checkpoint.lng],
                    "estimated_arrival": None,  # Will be calculated later
                    "required_checks": ["temperature", "time_stamp", "condition"]
                })
        
        return checkpoints

    def monitor_active_transports(self) -> List[Dict]:
        """Monitor all active transports (simulation)"""
        # This would integrate with real GPS tracking systems
        active_transports = []
        
        # Simulate some active transports
        for i in range(3):
            transport = {
                "transport_id": f"TRANS_{2025000 + i}",
                "organ_id": f"ORG_{100 + i}",
                "organ_type": ["heart", "kidney", "liver"][i],
                "current_location": {
                    "lat": 40.7128 + (i * 0.01),
                    "lng": -74.0060 + (i * 0.01),
                    "last_update": datetime.now().isoformat()
                },
                "route_progress": min(100, 25 + (i * 25)),  # %
                "estimated_arrival": (datetime.now() + timedelta(hours=2-i)).isoformat(),
                "current_temperature": 4.0 + (i * 0.1),
                "alerts": [] if i == 0 else [f"Temperature variation detected"],
                "status": "in_transit"
            }
            active_transports.append(transport)
        
        return active_transports

    def generate_route_report(self, transport_plan: Dict) -> Dict:
        """Generate comprehensive route report"""
        report = {
            "summary": {
                "organ_id": transport_plan["organ_id"],
                "total_distance": transport_plan["route"]["distance_km"],
                "total_time": transport_plan["route"]["estimated_duration_minutes"],
                "vehicle_type": transport_plan["vehicle"]["type"],
                "efficiency_score": min(100, 100 - (transport_plan["route"]["estimated_duration_minutes"] / 10))
            },
            "route_details": transport_plan["route"],
            "risk_assessment": {
                "time_risk": "Low" if transport_plan["route"]["estimated_duration_minutes"] < 240 else "Medium",
                "weather_risk": "Low",  # Would integrate with weather API
                "traffic_risk": "Medium",  # Would integrate with traffic API
                "overall_risk": "Low"
            },
            "recommendations": [
                "Maintain temperature at 4°C throughout transport",
                "Monitor GPS location every 15 minutes",
                "Contact destination hospital 30 minutes before arrival"
            ],
            "emergency_procedures": {
                "vehicle_breakdown": "Contact dispatch immediately: +1-555-EMERGENCY",
                "medical_emergency": "Proceed to nearest trauma center",
                "route_blockage": "Use alternate route via Highway 95"
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return report

# Sample data for testing
def load_sample_transport_data():
    """Load sample transport requests for testing"""
    city_general = Location("City General Hospital", "123 Medical Center Dr", 40.7128, -74.0060, "hospital")
    metro_medical = Location("Metro Medical Center", "456 Health Plaza", 40.7589, -73.9851, "hospital")
    regional_trauma = Location("Regional Trauma Center", "789 Emergency Ave", 40.7505, -73.9934, "hospital")
    
    transport_requests = [
        OrganTransport(
            organ_id="ORG_001",
            organ_type="heart",
            pickup_location=city_general,
            delivery_location=metro_medical,
            harvest_time=datetime.now(),
            max_transport_time=8,
            urgency_score=95
        ),
        OrganTransport(
            organ_id="ORG_002", 
            organ_type="kidney",
            pickup_location=metro_medical,
            delivery_location=regional_trauma,
            harvest_time=datetime.now(),
            max_transport_time=12,
            urgency_score=78
        )
    ]
    
    return transport_requests

# CLI Interface
def main():
    import sys
    
    if len(sys.argv) < 2:
        print("\n🚚 LifeConnect Logistics Engine - Usage:")
        print("=" * 60)
        print("  python route_optimizer.py test                    # Run comprehensive tests")
        print("  python route_optimizer.py test-gmaps              # Test Google Maps APIs")
        print("  python route_optimizer.py optimize                # Test route optimization")
        print("  python route_optimizer.py plan <pickup> <delivery> # Create transport plan")
        print("  python route_optimizer.py monitor                 # Monitor active transports")
        print("\nExamples:")
        print("  python route_optimizer.py plan 'City General' 'Metro Medical'")
        print("  python route_optimizer.py test-gmaps")
        return
    
    logistics = LifeConnectLogistics()
    command = sys.argv[1]
    
    if command == "test-gmaps":
        print(f"\n{'='*20} GOOGLE MAPS API TEST {'='*20}")
        
        # Test Google Maps connectivity
        connectivity = logistics.test_google_maps_connectivity()
        
        print(f"\n📊 Google Maps API Status:")
        print(f"   API Configured: {'✅' if connectivity['api_configured'] else '❌'}")
        print(f"   Geocoding: {'✅' if connectivity['geocoding_working'] else '❌'}")
        print(f"   Directions: {'✅' if connectivity['directions_working'] else '❌'}")
        print(f"   Message: {connectivity['message']}")
        
        if connectivity['geocoding_working'] and connectivity['directions_working']:
            print(f"\n🎉 Google Maps integration is working perfectly!")
        elif connectivity['api_configured']:
            print(f"\n⚠️ Some Google Maps features available, fallback methods will be used")
        else:
            print(f"\n❌ Google Maps API not configured. Set GOOGLE_MAPS_API_KEY in .env file")
    
    elif command == "test":
        print(f"\n{'='*20} LOGISTICS ENGINE TEST {'='*20}")
        
        # Test 1: Google Maps API
        print("\n1️⃣ Testing Google Maps Integration...")
        connectivity = logistics.test_google_maps_connectivity()
        print(f"   Google Maps Status: {connectivity['message']}")
        
        # Test 2: Basic functionality
        print("\n2️⃣ Testing Basic Functionality...")
        
        # Test geocoding
        test_address = "Empire State Building, New York, NY"
        lat, lng = logistics.geocode_address_google(test_address)
        print(f"   Geocoding test: {lat:.4f}, {lng:.4f}")
        
        # Test distance calculation
        origin = Location("Origin", "Times Square, New York, NY", 40.7580, -73.9855, "test")
        destination = Location("Dest", "Central Park, New York, NY", 40.7812, -73.9665, "test")
        distance, duration = logistics.calculate_distance_and_time(origin, destination)
        print(f"   Distance calculation: {distance:.1f}km, {duration}min")
        
        # Test 3: Transport plan creation
        print("\n3️⃣ Testing Transport Plan Creation...")
        organ_data = {
            "id": "TEST_ORG_001",
            "type": "heart",
            "urgency": 90,
            "max_hours": 8
        }
        
        plan = logistics.create_transport_plan(organ_data, "City General", "Metro Medical")
        print(f"   Transport plan created for {plan['organ_type']}")
        print(f"   Route: {plan['route']['distance_km']:.1f}km via {plan['vehicle']['type']}")
        
        # Test 4: Route optimization
        print("\n4️⃣ Testing Route Optimization...")
        transport_requests = load_sample_transport_data()
        optimization_result = logistics.optimize_organ_transport(transport_requests)
        
        print(f"   Optimized {len(optimization_result['routes'])} routes")
        print(f"   Total distance: {optimization_result['total_distance_km']:.1f}km")
        print(f"   Total time: {optimization_result['total_time_minutes']:.1f}min")
        
        print(f"\n{'='*20} TESTS COMPLETE {'='*20}")
    
    elif command == "optimize":
        print("\n🔄 Running Route Optimization Demo...")
        
        transport_requests = load_sample_transport_data()
        result = logistics.optimize_organ_transport(transport_requests)
        
        print(f"\n📊 Optimization Results:")
        print(f"   Method: {result['optimization_method']}")
        print(f"   Vehicles used: {result['vehicles_used']}")
        print(f"   Total distance: {result['total_distance_km']:.1f}km")
        print(f"   Total time: {result['total_time_minutes']:.1f}min")
        
        for i, route in enumerate(result['routes'], 1):
            print(f"\n   Route {i} ({route['vehicle'].vehicle_type}):")
            print(f"     Distance: {route['distance_km']:.1f}km")
            print(f"     Time: {route['time_minutes']}min")
            print(f"     Organs: {', '.join(route['organs_transported'])}")
    
    elif command == "plan":
        if len(sys.argv) < 4:
            print("Usage: python route_optimizer.py plan <pickup_hospital> <delivery_hospital>")
            return
        
        pickup = sys.argv[2]
        delivery = sys.argv[3]
        
        print(f"\n📋 Creating transport plan: {pickup} → {delivery}")
        
        organ_data = {
            "id": f"DEMO_ORG_{int(time.time())}",
            "type": "heart",
            "urgency": 85,
            "max_hours": 8
        }
        
        try:
            plan = logistics.create_transport_plan(organ_data, pickup, delivery)
            report = logistics.generate_route_report(plan)
            
            print(f"\n✅ Transport Plan Created:")
            print(f"   Organ: {plan['organ_type']} ({plan['organ_id']})")
            print(f"   Vehicle: {plan['vehicle']['type']} ({plan['vehicle']['id']})")
            print(f"   Distance: {plan['route']['distance_km']:.1f}km")
            print(f"   Duration: {plan['route']['estimated_duration_minutes']}min")
            print(f"   Checkpoints: {len(plan['route']['checkpoints'])}")
            
            print(f"\n📈 Route Report:")
            print(f"   Efficiency Score: {report['summary']['efficiency_score']:.1f}/100")
            print(f"   Risk Level: {report['risk_assessment']['overall_risk']}")
            
        except ValueError as e:
            print(f"❌ Error: {e}")
    
    elif command == "monitor":
        print("\n📡 Monitoring Active Transports...")
        
        active_transports = logistics.monitor_active_transports()
        
        print(f"\n🚚 {len(active_transports)} Active Transports:")
        
        for transport in active_transports:
            status_icon = "🟢" if transport['status'] == 'in_transit' else "🔴"
            print(f"\n   {status_icon} {transport['transport_id']} ({transport['organ_type']})")
            print(f"      Progress: {transport['route_progress']}%")
            print(f"      Temperature: {transport['current_temperature']}°C")
            print(f"      ETA: {transport['estimated_arrival']}")
            
            if transport['alerts']:
                print(f"      ⚠️ Alerts: {', '.join(transport['alerts'])}")

if __name__ == "__main__":
    main()
