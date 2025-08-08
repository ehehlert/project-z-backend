import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .db import db

class Edge(db.Model):
    __tablename__ = 'edges'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    source = db.Column(UUID(as_uuid=True))
    target = db.Column(UUID(as_uuid=True))
    sld_id = db.Column(UUID(as_uuid=True))
    is_deleted = db.Column(db.Boolean)
    core_attributes = db.Column(JSONB)
    edge_class = db.Column(UUID(as_uuid=True))

    def to_dict(self):
        return {
            'id': str(self.id),
            'source': str(self.source),
            'target': str(self.target),
            'sld_id': str(self.sld_id),
            'is_deleted': self.is_deleted,
            'core_attributes': self.core_attributes,
            'edge_class': self.edge_class
        }