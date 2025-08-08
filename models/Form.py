import uuid
import json
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .db import db

class Form(db.Model):
    __tablename__ = 'forms'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    schema = db.Column(JSONB)
    title = db.Column(db.String)
    is_global = db.Column(db.Boolean)
    is_deleted = db.Column(db.Boolean)

    def to_dict(self):
        return {
            'id': str(self.id),
            'schema': json.dumps(self.schema),
            'title': str(self.title),
            'is_global': self.is_global,
            'is_deleted': self.is_deleted
        }