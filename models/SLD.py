import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from .db import db

class SLD(db.Model):
    __tablename__ = 'slds'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name = db.Column(
        db.String,
        nullable=False
    )
    company_id = db.Column(
        UUID(as_uuid=True), 
        db.ForeignKey('companies.id'),
        nullable=False
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
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

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'is_deleted': self.is_deleted
        }