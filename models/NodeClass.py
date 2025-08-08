import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .db import db

class NodeClass(db.Model):
    __tablename__ = 'node_classes'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name = db.Column(db.String)
    style = db.Column(db.String)
    definition = db.Column(JSONB)
    box = db.Column(db.Boolean)
    ocp = db.Column(db.Boolean)
    width = db.Column(db.Float)
    height = db.Column(db.Float)
    color = db.Column(db.String)
    needs_source = db.Column(db.Boolean)

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': str(self.name),
            'style': str(self.style),
            'definition': self.definition,
            'box': self.box,
            'ocp': self.ocp,
            'width': self.width,
            'height': self.height,
            'color': str(self.color),
            'needs_source': self.needs_source
        }