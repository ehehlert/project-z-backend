import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from .db import db

class Issue(db.Model):
    __tablename__ = 'issues'
    
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    title = db.Column(db.String)
    description = db.Column(db.String)
    created_date = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    node_id = db.Column(
        UUID(as_uuid=True)
    )
    issue_class = db.Column(
        UUID(as_uuid=True)
    )
    issue_type = db.Column(db.String)
    issue_subtype = db.Column(db.String)
    is_deleted = db.Column(
        db.Boolean,
        default=False
    )
    session_id = db.Column(
        UUID(as_uuid=True)
    )
    sld_id = db.Column(
        UUID(as_uuid=True)
    )
    details = db.Column(db.JSON)
    status = db.Column(db.String)
    proposed_resolution = db.Column(db.String)
    modified_date = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self):
        created_ts = (
            self.created_date
                .replace(tzinfo=timezone.utc)
                .strftime('%Y-%m-%dT%H:%M:%SZ')
            if self.created_date else None
        )
        modified_ts = (
            self.modified_date
                .replace(tzinfo=timezone.utc)
                .strftime('%Y-%m-%dT%H:%M:%SZ')
            if self.modified_date else None
        )
        
        return {
            'id': str(self.id),
            'title': self.title,
            'description': self.description,
            'created_date': created_ts,
            'node_id': str(self.node_id) if self.node_id else None,
            'issue_class': str(self.issue_class),
            'issue_type': self.issue_type,
            'issue_subtype': self.issue_subtype,
            'is_deleted': self.is_deleted if self.is_deleted is not None else False,
            'session_id': str(self.session_id) if self.session_id else None,
            'sld_id': str(self.sld_id) if self.sld_id else None,
            'details': self.details,
            'status': self.status,
            'proposed_resolution': self.proposed_resolution,
            'modified_date': modified_ts
        }