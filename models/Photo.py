import uuid
from sqlalchemy.dialects.postgresql import UUID
from .db import db

class Photo(db.Model):
    __tablename__ = 'photos'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    entity_id = db.Column(UUID(as_uuid=True))
    url = db.Column(db.String)
    type = db.Column(db.String)
    sld_id = db.Column(UUID(as_uuid=True))
    upload_needed = db.Column(db.Boolean)
    local_filepath = db.Column(db.String)
    filename = db.Column(db.String)
    is_deleted = db.Column(db.Boolean)

    def to_dict(self):
        return {
            'id': str(self.id),
            'entity_id': str(self.entity_id),
            'url': self.url,
            'type': self.type,
            'sld_id': str(self.sld_id),
            'upload_needed': self.upload_needed,
            'local_filepath': self.local_filepath,
            'filename': self.filename,
            'is_deleted': self.is_deleted
        }