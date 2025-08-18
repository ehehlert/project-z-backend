import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from .db import db

class Device(db.Model):
    __tablename__ = 'device_tokens'
    
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('users.id'),
        primary_key=True,
        nullable=False
    )
    device_id = db.Column(
        db.String(255),
        primary_key=True,
        nullable=False
    )
    device_token = db.Column(
        db.String(255),
        nullable=False
    )
    platform = db.Column(
        db.String(20),
        default='ios'
    )
    environment = db.Column(
        db.String(20),
        nullable=False
    )
    endpoint_arn = db.Column(
        db.String(500)
    )
    device_name = db.Column(
        db.String(255)
    )
    is_active = db.Column(
        db.Boolean,
        default=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        def format_dt(dt):
            return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if dt else None
        
        return {
            'user_id': str(self.user_id),
            'device_id': self.device_id,
            'device_token': self.device_token,
            'platform': self.platform,
            'environment': self.environment,
            'endpoint_arn': self.endpoint_arn,
            'device_name': self.device_name,
            'is_active': self.is_active,
            'created_at': format_dt(self.created_at),
            'updated_at': format_dt(self.updated_at)
        }