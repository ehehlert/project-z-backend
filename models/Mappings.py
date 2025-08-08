import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .db import db 

class MappingIssueTask(db.Model):
    __tablename__ = 'mapping_issue_task'
    
    issue_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True
    )
    task_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True
    )
    is_deleted = db.Column(db.Boolean)
    
    def to_dict(self):
        return {
            'issue_id': str(self.issue_id),
            'task_id': str(self.task_id),
            'is_deleted': self.is_deleted
        }

class MappingTaskSession(db.Model):
    __tablename__ = 'mapping_task_session'

    # New standalone primary key
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    task_id = db.Column(
        UUID(as_uuid=True),
        nullable=False
    )
    session_id = db.Column(
        UUID(as_uuid=True),
        nullable=False
    )

    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'task_id': str(self.task_id),
            'session_id': str(self.session_id),
            'is_deleted': self.is_deleted
        }

class MappingQuoteTask(db.Model):
    __tablename__ = 'mapping_quote_task'
    
    quote_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True
    )
    task_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True
    )
    is_deleted = db.Column(db.Boolean)
    
    def to_dict(self):
        return {
            'quote_id': str(self.quote_id),
            'task_id': str(self.task_id),
            'is_deleted': self.is_deleted
        }
