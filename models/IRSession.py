import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from .db import db

class IRSession(db.Model):
    __tablename__ = 'ir_sessions'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name = db.Column(db.String, nullable=False)
    photo_type = db.Column(db.String, nullable=False)
    active_visual_prefix = db.Column(db.String, nullable=False)
    active_ir_prefix = db.Column(db.String, nullable=False)
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    date_closed = db.Column(db.DateTime)
    sld_id = db.Column(UUID(as_uuid=True), nullable=False)
    active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'photo_type': self.photo_type,
            'active_visual_prefix': self.active_visual_prefix,
            'active_ir_prefix': self.active_ir_prefix,
            'date_created': (
                self.date_created
                    .replace(tzinfo=timezone.utc)
                    .strftime('%Y-%m-%dT%H:%M:%SZ')
            ) if self.date_created else None,
            'date_closed': (
                self.date_closed
                    .replace(tzinfo=timezone.utc)
                    .strftime('%Y-%m-%dT%H:%M:%SZ')
            ) if self.date_closed else None,
            'sld_id': str(self.sld_id),
            'active': self.active
        }