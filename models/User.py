import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .db import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    username = db.Column(
        db.String,
        nullable=False
    )
    company_id = db.Column(
        UUID(as_uuid=True), 
        db.ForeignKey('companies.id'),
        nullable=False
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    modified_at =db.Column(
        db.DateTime(timezone=True),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    def to_dict(self):
        def format_dt(dt):
            return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if dt else None
        
        return {
            'id': str(self.id),
            'username': self.username,
            'company_id': str(self.company_id),
            'created_at': format_dt(self.created_at),
            'modified_at': format_dt(self.modified_at),
            'is_deleted': self.is_deleted,
            'active': self.active
        }