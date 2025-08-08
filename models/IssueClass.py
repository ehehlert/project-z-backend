import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .db import db

class IssueClass(db.Model):
    __tablename__ = 'issue_classes'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name = db.Column(db.String)
    definition = db.Column(JSONB)

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': str(self.name),
            'definition': self.definition
        }