from datetime import datetime, timezone
from .auth_routes import auth_bp
from .health_card_routes import health_card_bp
from .ai_routes import ai_bp
from .logistics_routes import logistics_bp
from .dashboard_routes import dashboard_bp
from .blockchain_routes import blockchain_bp

def register_routes(app, component_service):
    """Register all route blueprints"""
    
    # Set component service for all blueprints
    auth_bp.component_service = component_service
    health_card_bp.component_service = component_service
    ai_bp.component_service = component_service
    logistics_bp.component_service = component_service
    dashboard_bp.component_service = component_service
    blockchain_bp.component_service = component_service
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(health_card_bp, url_prefix='/api/health-cards')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(logistics_bp, url_prefix='/api/logistics')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(blockchain_bp, url_prefix='/api/blockchain')
    
    # Add health check route
    @app.route('/api/health')
    def health_check():
        """Simple health check endpoint"""
        from utils import create_response
        return create_response(True, {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '1.0.0',
            'components': {
                'database': True,
                'ai_engine': True,
                'logistics': True,
                'health_cards': True,
                'websocket': True
            }
        })
