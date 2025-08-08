import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from .db import db

class IRPhoto(db.Model):
    __tablename__ = 'ir_photos'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    ir_session_id = db.Column(
        UUID(as_uuid=True)
    )
    visual_photo_key = db.Column(db.String)
    ir_photo_key = db.Column(db.String)
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    node_id = db.Column(
        UUID(as_uuid=True)
    )
    sld_id = db.Column(
        UUID(as_uuid=True)
    )
    issue_id = db.Column(
        UUID(as_uuid=True)
    )
    is_deleted = db.Column(db.Boolean)

    def to_dict(self):
        ts = (
            self.date_created
                .replace(tzinfo=timezone.utc)
                .strftime('%Y-%m-%dT%H:%M:%SZ')
        )
        return {
            'id': str(self.id),
            'ir_session_id': str(self.ir_session_id) if self.ir_session_id else None,
            'visual_photo_key': self.visual_photo_key,
            'ir_photo_key': self.ir_photo_key,
            'date_created': ts,
            'node_id': str(self.node_id) if self.node_id else None,
            'sld_id': str(self.sld_id) if self.sld_id else None,
            'issue_id': str(self.issue_id) if self.issue_id else None,
            'is_deleted': self.is_deleted if self.is_deleted is not None else False
        }