import uuid
from sqlalchemy.dialects.postgresql import UUID
from .db import db

class SLD(db.Model):
    __tablename__ = 'slds'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name = db.Column(db.String)

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name
        }