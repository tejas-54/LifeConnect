from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(42), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    name = db.Column(db.String(100), nullable=True)
    user_type = db.Column(db.String(20), nullable=False)  # donor, hospital, regulator
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    profile_data = db.Column(db.Text, nullable=True)  # JSON string for additional data
    
    # Relationships
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True)
    health_cards = db.relationship('HealthCard', backref='user', lazy=True)
    organ_matches = db.relationship('OrganMatch', backref='user', lazy=True)

class HealthCard(db.Model):
    __tablename__ = 'health_cards'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    card_data = db.Column(db.Text, nullable=False)  # JSON string
    ipfs_cid = db.Column(db.String(100), nullable=True)
    pdf_path = db.Column(db.String(255), nullable=True)
    image_path = db.Column(db.String(255), nullable=True)
    qr_code_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)

class OrganMatch(db.Model):
    __tablename__ = 'organ_matches'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    donor_address = db.Column(db.String(42), nullable=False)
    recipient_address = db.Column(db.String(42), nullable=False)
    organ_type = db.Column(db.String(50), nullable=False)
    compatibility_score = db.Column(db.Float, nullable=False)
    ai_analysis = db.Column(db.Text, nullable=True)  # JSON string
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, completed
    match_timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    transport_id = db.Column(db.String(100), nullable=True)
    blockchain_tx_hash = db.Column(db.String(66), nullable=True)

class TransportPlan(db.Model):
    __tablename__ = 'transport_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    transport_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    organ_match_id = db.Column(db.Integer, db.ForeignKey('organ_matches.id'), nullable=True)
    organ_type = db.Column(db.String(50), nullable=False)
    pickup_location = db.Column(db.Text, nullable=False)  # JSON string
    delivery_location = db.Column(db.Text, nullable=False)  # JSON string
    vehicle_type = db.Column(db.String(50), nullable=False)
    route_data = db.Column(db.Text, nullable=False)  # JSON string
    estimated_duration = db.Column(db.Integer, nullable=False)  # minutes
    estimated_distance = db.Column(db.Float, nullable=False)  # km
    actual_duration = db.Column(db.Integer, nullable=True)
    actual_distance = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='planned')  # planned, in_progress, completed, cancelled
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    meta_data = db.Column(db.Text, nullable=True)  # JSON string
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    severity = db.Column(db.String(20), default='info')  # info, warning, error, critical

class SystemMetrics(db.Model):
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(50), nullable=False, index=True)
    metric_value = db.Column(db.Float, nullable=False)
    metric_data = db.Column(db.Text, nullable=True)  # JSON string for complex metrics
    recorded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

class BlockchainTransaction(db.Model):
    __tablename__ = 'blockchain_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    tx_hash = db.Column(db.String(66), unique=True, nullable=False, index=True)
    contract_address = db.Column(db.String(42), nullable=False)
    function_name = db.Column(db.String(100), nullable=False)
    user_address = db.Column(db.String(42), nullable=False)
    tx_data = db.Column(db.Text, nullable=True)  # JSON string
    gas_used = db.Column(db.Integer, nullable=True)
    gas_price = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, failed
    block_number = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    confirmed_at = db.Column(db.DateTime, nullable=True)
