import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .db import db

class Node(db.Model):
    __tablename__ = 'nodes'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    type = db.Column(db.String)
    label = db.Column(db.String)
    sld_id = db.Column(
        UUID(as_uuid=True)
    )
    parent_id = db.Column(
        UUID(as_uuid=True)
    )
    x = db.Column(db.Float)
    y = db.Column(db.Float)
    width = db.Column(db.Float)
    height = db.Column(db.Float)
    is_deleted = db.Column(db.Boolean)
    location = db.Column(db.String)
    node_class = db.Column(
        UUID(as_uuid=True)
    )
    core_attributes = db.Column(JSONB)
    com = db.Column(db.Integer)
    qr_code = db.Column(db.String)

    def to_dict(self):
        return {
            'id': str(self.id),
            'type': self.type,
            'label': self.label,
            'sld_id': str(self.sld_id),
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'is_deleted': self.is_deleted,
            'location': self.location,
            'node_class': str(self.node_class) if self.node_class else None,
            'core_attributes': self.core_attributes,
            'com': self.com,
            'qr_code': self.qr_code
        }