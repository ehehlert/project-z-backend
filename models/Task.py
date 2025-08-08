import uuid
import json
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .db import db

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    title = db.Column(db.String)
    task_description = db.Column(db.String)
    completed = db.Column(db.Boolean)
    node_id = db.Column(
        UUID(as_uuid=True)
    )
    form_id = db.Column(
        UUID(as_uuid=True)
    )
    sld_id = db.Column(
        UUID(as_uuid=True)
    )
    is_deleted = db.Column(db.Boolean)
    submission = db.Column(JSONB)
    submitted_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    due_date = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    task_type = db.Column(db.String)
    recurring = db.Column(db.Boolean)
    interval = db.Column(db.Integer)
    procedure_id = db.Column(
        UUID(as_uuid=True)
    )
    shortcut_id = db.Column(
        UUID(as_uuid=True)
    )

    def to_dict(self):
        def fmt_dt(dt):
            return (
                dt.replace(tzinfo=timezone.utc)
                .strftime('%Y-%m-%dT%H:%M:%SZ')
                if dt else None
            )

        return {
            'id': str(self.id),
            'title': self.title,
            'task_description': self.task_description,
            'completed': self.completed,
            'node_id': str(self.node_id) if self.node_id else None,
            'form_id': str(self.form_id) if self.form_id else None,
            'sld_id': str(self.sld_id) if self.sld_id else None,
            'is_deleted': self.is_deleted,
            'submission': json.dumps(self.submission),
            'submitted_at': fmt_dt(self.submitted_at),
            'created_at': fmt_dt(self.created_at),
            'due_date': fmt_dt(self.due_date),
            'task_type': self.task_type,
            'recurring': self.recurring,
            'interval': self.interval,
            'procedure_id': str(self.procedure_id) if self.procedure_id else None,
            'shortcut_id': str(self.shortcut_id) if self.shortcut_id else None,
        }