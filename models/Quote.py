import uuid
import json
from sqlalchemy.dialects.postgresql import UUID, JSONB 
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from .db import db

class Quote(db.Model):
    __tablename__ = 'quotes'
    
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    created_date = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    modified_date = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    title = db.Column(db.String)
    sow = db.Column(db.Text)
    tnm = db.Column(db.Text)
    sld_id = db.Column(
        UUID(as_uuid=True)
    )
    description = db.Column(db.String)
    status = db.Column(db.String)
    is_deleted = db.Column(
        db.Boolean,
        default=False
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
            'created_date': created_ts,
            'modified_date': modified_ts,
            'title': self.title,
            'sow': json.dumps(self.sow),
            'tnm': json.dumps(self.tnm),
            'sld_id': str(self.sld_id) if self.sld_id else None,
            'description': self.description,
            'status': self.status,
            'is_deleted': self.is_deleted if self.is_deleted is not None else False
        }
