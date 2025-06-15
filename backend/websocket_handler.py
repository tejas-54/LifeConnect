import logging
from datetime import datetime
from flask import request
from flask_socketio import emit, join_room, leave_room

logger = logging.getLogger(__name__)

def setup_websocket_handlers(socketio):
    """Setup all WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info(f'WebSocket client connected: {request.sid}')
        emit('connection_response', {
            'status': 'connected',
            'message': 'Welcome to LifeConnect Real-time System!',
            'server_time': datetime.utcnow().isoformat()
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info(f'WebSocket client disconnected: {request.sid}')

    @socketio.on('join_user_room')
    def handle_join_room(data):
        """Join user to their personal notification room"""
        user_id = data.get('user_id')
        user_type = data.get('user_type', 'user')
        
        if user_id:
            join_room(f"user_{user_id}")
            join_room(f"type_{user_type}")
            
            emit('room_joined', {
                'user_room': f"user_{user_id}",
                'type_room': f"type_{user_type}",
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Send welcome notification
            socketio.emit('notification', {
                'type': 'welcome',
                'title': 'Connected to LifeConnect',
                'message': f'You are now connected as a {user_type}',
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"user_{user_id}")

    @socketio.on('leave_user_room')
    def handle_leave_room(data):
        """Leave user room"""
        user_id = data.get('user_id')
        user_type = data.get('user_type', 'user')
        
        if user_id:
            leave_room(f"user_{user_id}")
            leave_room(f"type_{user_type}")
            
            emit('room_left', {
                'user_room': f"user_{user_id}",
                'type_room': f"type_{user_type}",
                'timestamp': datetime.utcnow().isoformat()
            })

    return socketio
