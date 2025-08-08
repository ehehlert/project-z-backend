import uuid
import json
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .db import db

class FormSubmission(db.Model):
    __tablename__ = 'form_submissions'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    form_id = db.Column(
        UUID(as_uuid=True)
    )
    submission = db.Column(JSONB)
    task_id = db.Column(
        UUID(as_uuid=True)
    )
    submitted_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'form_id': str(self.form_id),
            'submission': json.dumps(self.submission),
            'task_id': str(self.task_id),
            'submitted_at': self.submitted_at.isoformat()
        }