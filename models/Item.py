import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .db import db

class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name = db.Column(db.String, nullable=False)
    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    sld = db.Column(JSONB, nullable=False, default=lambda: {"nodes": [], "edges": []})

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'timestamp': self.timestamp.isoformat(),
            'sld': self.sld or {}
        }