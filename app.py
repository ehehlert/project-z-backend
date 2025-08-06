# app.py
import os
import uuid
import logging
import json
from datetime import datetime
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import timezone
from dateutil.relativedelta import relativedelta

# ─── Configure logging ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("table-and-detail")

# ─── Flask & DB setup ─────────────────────────────────────────
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:jAzQp9hwjimpOLAD6v38@project-z-db.crui6kuk09zu.us-east-2.rds.amazonaws.com:5432/postgres'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

logger.info("Starting Flask app on port 5000, connecting to DB %s", app.config['SQLALCHEMY_DATABASE_URI'])


# ─── Model ─────────────────────────────────────────────────────

class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name = db.Column(db.String, nullable=False)
    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    sld = db.Column(JSONB, nullable=False, default=lambda: {"nodes": [], "edges": []})

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'timestamp': self.timestamp.isoformat(),
            'sld': self.sld or {}
        }

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

class Node(db.Model):
    __tablename__ = 'nodes'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    type = db.Column(db.String)
    label = db.Column(db.String)
    sld_id = db.Column(
        UUID(as_uuid=True)
    )
    parent_id = db.Column(
        UUID(as_uuid=True)
    )
    x = db.Column(db.Float)
    y = db.Column(db.Float)
    width = db.Column(db.Float)
    height = db.Column(db.Float)
    is_deleted = db.Column(db.Boolean)
    location = db.Column(db.String)
    node_class = db.Column(
        UUID(as_uuid=True)
    )
    core_attributes = db.Column(JSONB)
    com = db.Column(db.Integer)
    qr_code = db.Column(db.String)

    def to_dict(self):
        return {
            'id': str(self.id),
            'type': self.type,
            'label': self.label,
            'sld_id': str(self.sld_id),
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'is_deleted': self.is_deleted,
            'location': self.location,
            'node_class': str(self.node_class) if self.node_class else None,
            'core_attributes': self.core_attributes,
            'com': self.com,
            'qr_code': self.qr_code
        }

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

class Edge(db.Model):
    __tablename__ = 'edges'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    source = db.Column(UUID(as_uuid=True))
    target = db.Column(UUID(as_uuid=True))
    sld_id = db.Column(UUID(as_uuid=True))
    is_deleted = db.Column(db.Boolean)
    core_attributes = db.Column(JSONB)
    edge_class = db.Column(UUID(as_uuid=True))

    def to_dict(self):
        return {
            'id': str(self.id),
            'source': str(self.source),
            'target': str(self.target),
            'sld_id': str(self.sld_id),
            'is_deleted': self.is_deleted,
            'core_attributes': self.core_attributes,
            'edge_class': self.edge_class
        }

class EdgeClass(db.Model):
    __tablename__ = 'edge_classes'
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

class IRPhoto(db.Model):
    __tablename__ = 'ir_photos'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    ir_session_id = db.Column(
        UUID(as_uuid=True)
    )
    visual_photo_key = db.Column(db.String)
    ir_photo_key = db.Column(db.String)
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    node_id = db.Column(
        UUID(as_uuid=True)
    )
    sld_id = db.Column(
        UUID(as_uuid=True)
    )
    is_deleted = db.Column(db.Boolean)

    def to_dict(self):
        ts = (
            self.date_created
                .replace(tzinfo=timezone.utc)
                .strftime('%Y-%m-%dT%H:%M:%SZ')
        )
        return {
            'id': str(self.id),
            'ir_session_id': str(self.ir_session_id) if self.ir_session_id else None,
            'visual_photo_key': self.visual_photo_key,
            'ir_photo_key': self.ir_photo_key,
            'date_created': ts,
            'node_id': str(self.node_id) if self.node_id else None,
            'sld_id': str(self.sld_id) if self.sld_id else None,
            'is_deleted': self.is_deleted if self.is_deleted is not None else False
        }   

class IRSession(db.Model):
    __tablename__ = 'ir_sessions'
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name = db.Column(db.String, nullable=False)
    photo_type = db.Column(db.String, nullable=False)
    active_visual_prefix = db.Column(db.String, nullable=False)
    active_ir_prefix = db.Column(db.String, nullable=False)
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    date_closed = db.Column(db.DateTime)
    sld_id = db.Column(UUID(as_uuid=True), nullable=False)
    active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'photo_type': self.photo_type,
            'active_visual_prefix': self.active_visual_prefix,
            'active_ir_prefix': self.active_ir_prefix,
            'date_created': (
                self.date_created
                    .replace(tzinfo=timezone.utc)
                    .strftime('%Y-%m-%dT%H:%M:%SZ')
            ) if self.date_created else None,
            'date_closed': (
                self.date_closed
                    .replace(tzinfo=timezone.utc)
                    .strftime('%Y-%m-%dT%H:%M:%SZ')
            ) if self.date_closed else None,
            'sld_id': str(self.sld_id),
            'active': self.active
        }

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
    details = db.Column(db.Text)  # JSON field, using Text
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
            'issue_type': self.issue_type,
            'issue_subtype': self.issue_subtype,
            'is_deleted': self.is_deleted if self.is_deleted is not None else False,
            'session_id': str(self.session_id) if self.session_id else None,
            'sld_id': str(self.sld_id) if self.sld_id else None,
            'details': json.dumps(self.details),
            'status': self.status,
            'proposed_resolution': self.proposed_resolution,
            'modified_date': modified_ts
        }

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
    sow = db.Column(db.Text)  # JSON field, using Text
    tnm = db.Column(db.Text)  # JSON field, using Text
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

# ─── Health Check  ────────────────────────────────────────────

@app.route('/health', methods=['GET'])
def health_check():
    logger.debug("Health check invoked")
    return jsonify({
        'status': 'ok',
        'uptime': datetime.utcnow().isoformat()
    }), 200

# ─── Quotes ────────────────────────────────────────────

@app.route('/quote/create', methods=['POST'])
def create_quote():
    """Create a new quote"""
    try:
        data = request.get_json()
        
        # Create new quote instance
        quote = Quote(
            title=data.get('title'),
            sow=data.get('sow'),
            tnm=data.get('tnm'),
            sld_id=uuid.UUID(data['sld_id']) if data.get('sld_id') else None,
            description=data.get('description'),
            status=data.get('status'),
            is_deleted=data.get('is_deleted', False)
        )
        
        db.session.add(quote)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': quote.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/quote/update/<uuid:quote_id>', methods=['PUT'])
def update_quote(quote_id):
    """Update an existing quote"""
    try:
        # Find the quote
        quote = Quote.query.get(quote_id)
        if not quote:
            return jsonify({
                'success': False,
                'error': 'Quote not found'
            }), 404
        
        # Get update data
        data = request.get_json()
        
        # Update fields if provided
        if 'title' in data:
            quote.title = data['title']
        if 'sow' in data:
            quote.sow = data['sow']
        if 'tnm' in data:
            quote.tnm = data['tnm']
        if 'sld_id' in data:
            quote.sld_id = uuid.UUID(data['sld_id']) if data['sld_id'] else None
        if 'description' in data:
            quote.description = data['description']
        if 'status' in data:
            quote.status = data['status']
        if 'is_deleted' in data:
            quote.is_deleted = data['is_deleted']
        
        # Update modified_date
        quote.modified_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': quote.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

# ─── Issues ────────────────────────────────────────────

@app.route('/issue/create', methods=['POST'])
def create_issue():
    """Create a new issue"""
    try:
        data = request.get_json()
        
        # Create new issue instance
        issue = Issue(
            title=data.get('title'),
            description=data.get('description'),
            node_id=uuid.UUID(data['node_id']) if data.get('node_id') else None,
            issue_type=data.get('issue_type'),
            issue_subtype=data.get('issue_subtype'),
            is_deleted=data.get('is_deleted', False),
            session_id=uuid.UUID(data['session_id']) if data.get('session_id') else None,
            sld_id=uuid.UUID(data['sld_id']) if data.get('sld_id') else None,
            details=data.get('details'),
            status=data.get('status'),
            proposed_resolution=data.get('proposed_resolution')
        )
        
        db.session.add(issue)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': issue.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/issue/update/<uuid:issue_id>', methods=['PUT'])
def update_issue(issue_id):
    """Update an existing issue"""
    try:
        # Find the issue
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({
                'success': False,
                'error': 'Issue not found'
            }), 404
        
        # Get update data
        data = request.get_json()
        
        # Update fields if provided
        if 'title' in data:
            issue.title = data['title']
        if 'description' in data:
            issue.description = data['description']
        if 'node_id' in data:
            issue.node_id = uuid.UUID(data['node_id']) if data['node_id'] else None
        if 'issue_type' in data:
            issue.issue_type = data['issue_type']
        if 'issue_subtype' in data:
            issue.issue_subtype = data['issue_subtype']
        if 'is_deleted' in data:
            issue.is_deleted = data['is_deleted']
        if 'session_id' in data:
            issue.session_id = uuid.UUID(data['session_id']) if data['session_id'] else None
        if 'sld_id' in data:
            issue.sld_id = uuid.UUID(data['sld_id']) if data['sld_id'] else None
        if 'details' in data:
            issue.details = data['details']
        if 'status' in data:
            issue.status = data['status']
        if 'proposed_resolution' in data:
            issue.proposed_resolution = data['proposed_resolution']
        
        # Update modified_date
        issue.modified_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': issue.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

# ─── IR Photos / Sessions ────────────────────────────────────────────
@app.route('/ir_photos/<uuid:sld_id>')
def get_ir_photos(sld_id):
    logger.info("READ IR_PHOTOS FOR SLD: %s", sld_id)
    tasks = IRPhoto.query.filter_by(sld_id=sld_id).all()
    ir_photo_dicts = [t.to_dict() for t in tasks]
    result = ir_photo_dicts
    logger.info("READ succeeded: %s", result)
    return jsonify(result), 200

@app.route('/ir_photo/create', methods=['POST'])
def create_ir_photo():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['id', 'node_id', 'ir_session_id', 'visual_photo_key', 'ir_photo_key']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create new IR photo
        ir_photo = IRPhoto(
            id=uuid.UUID(data['id']),
            ir_session_id=uuid.UUID(data['ir_session_id']) if data.get('ir_session_id') else None,
            node_id=uuid.UUID(data['node_id']),
            sld_id=uuid.UUID(data['sld_id']),
            visual_photo_key=data['visual_photo_key'],
            ir_photo_key=data['ir_photo_key'],
            date_created=datetime.fromisoformat(data['date_created']) if data.get('date_created') else datetime.utcnow(),
            is_deleted=data.get('is_deleted', False)
        )
        
        db.session.add(ir_photo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'ir_photo': ir_photo.to_dict()
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/ir_session/create', methods=['POST'])
def create_ir_session():
    try:
        data = request.get_json()
        logger.info("CREATE /ir_session/create with payload: %s", data)
        
        # Validate required fields
        required_fields = ['id', 'photo_type', 'active_visual_prefix', 'active_ir_prefix', 'sld_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create new IR session
        ir_session = IRSession(
            id=uuid.UUID(data['id']),
            name=data['name'],
            photo_type=data['photo_type'],
            active_visual_prefix=data['active_visual_prefix'],
            active_ir_prefix=data['active_ir_prefix'],
            sld_id=uuid.UUID(data['sld_id']),
            date_created=datetime.fromisoformat(data['date_created']) if data.get('date_created') else datetime.utcnow(),
            date_closed=datetime.fromisoformat(data['date_closed']) if data.get('date_closed') else None,
            active=data.get('active', True)
        )
        
        db.session.add(ir_session)
        db.session.commit()
        
        logger.info("CREATE succeeded: IR Session %s", ir_session.id)
        return jsonify({
            'success': True,
            'ir_session': ir_session.to_dict()
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        logger.error("Invalid data format: %s", str(e))
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logger.exception("Error creating IR session")
        return jsonify({'error': str(e)}), 500

@app.route('/ir_session/update/<uuid:ir_session_id>', methods=['PUT'])
def update_ir_session(ir_session_id):
    data = request.get_json() or {}
    logger.info("UPDATE /ir_session/update/%s with payload: %s", ir_session_id, data)

    ir_session = IRSession.query.get_or_404(ir_session_id)

    if 'name' in data:
        ir_session.name = data['name']
    if 'photo_type' in data:
        ir_session.photo_type = data['photo_type']
    if 'active_visual_prefix' in data:
        ir_session.active_visual_prefix = data['active_visual_prefix']
    if 'active_ir_prefix' in data:
        ir_session.active_ir_prefix = data['active_ir_prefix']
    if 'date_created' in data:
        try:
            ir_session.date_created = datetime.fromisoformat(data['date_created'])
        except Exception as e:
            logger.error("Invalid date_created format: %s", data['date_created'])
            return jsonify({'error': 'Invalid date_created format'}), 400
    if 'date_closed' in data:
        try:
            ir_session.date_closed = datetime.fromisoformat(data['date_closed']) if data['date_closed'] else None
        except Exception as e:
            logger.error("Invalid date_closed format: %s", data['date_closed'])
            return jsonify({'error': 'Invalid date_closed format'}), 400
    if 'sld_id' in data:
        try:
            ir_session.sld_id = uuid.UUID(data['sld_id'])
        except ValueError:
            return jsonify({'error': 'Invalid sld_id format'}), 400
    if 'active' in data:
        ir_session.active = data['active']

    db.session.commit()

    result = ir_session.to_dict()
    logger.info("UPDATE succeeded: %s", result)
    return jsonify(result), 200

# IR Photo methods
@app.route('/ir_photo/update/<uuid:photo_id>', methods=['PUT'])
def update_ir_photo(photo_id):
    data = request.get_json() or {}
    logger.info("UPDATE /ir_photo/update/%s with payload: %s", photo_id, data)

    ir_photo = IRPhoto.query.get_or_404(photo_id)

    if 'ir_session_id' in data:
        try:
            ir_photo.ir_session_id = uuid.UUID(data['ir_session_id']) if data['ir_session_id'] else None
        except ValueError:
            return jsonify({'error': 'Invalid ir_session_id format'}), 400
    if 'visual_photo_key' in data:
        ir_photo.visual_photo_key = data['visual_photo_key']
    if 'ir_photo_key' in data:
        ir_photo.ir_photo_key = data['ir_photo_key']
    if 'date_created' in data:
        try:
            ir_photo.date_created = datetime.fromisoformat(data['date_created'])
        except Exception as e:
            logger.error("Invalid date_created format: %s", data['date_created'])
            return jsonify({'error': 'Invalid date_created format'}), 400
    if 'node_id' in data:
        try:
            ir_photo.node_id = uuid.UUID(data['node_id']) if data['node_id'] else None
        except ValueError:
            return jsonify({'error': 'Invalid node_id format'}), 400
    if 'sld_id' in data:
        try:
            ir_photo.sld_id = uuid.UUID(data['sld_id']) if data['sld_id'] else None
        except ValueError:
            return jsonify({'error': 'Invalid sld_id format'}), 400
    if 'is_deleted' in data:
        ir_photo.is_deleted = data['is_deleted']

    db.session.commit()

    result = ir_photo.to_dict()
    logger.info("UPDATE succeeded: %s", result)
    return jsonify(result), 200

# ─── Task and Form Endpoiints ───────────────────────────────────────────
@app.route('/forms', methods=['GET'])
def get_all_forms():
    logger.info("READ ALL FORMS")
    forms = Form.query.all()
    result = [form.to_dict() for form in forms]
    logger.info("READ succeeded")
    return jsonify(result), 200

@app.route('/tasks/<uuid:sld_id>', methods=['GET'])
def get_tasks(sld_id):
    logger.info("READ TASKS FOR SLD: %s", sld_id)
    tasks = Task.query.filter_by(sld_id=sld_id).all()
    task_dicts = [t.to_dict() for t in tasks]
    # this used to be a multi-key payload, leaving it as such to avoid too much refactoring in mobile codebase
    result = {
        "user_tasks":       task_dicts 
    }
    logger.info("READ succeeded: %s", result)
    return jsonify(result), 200

# Task methods
@app.route('/task/update/<uuid:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json() or {}
    logger.info("UPDATE /task/update/%s with payload: %s", task_id, data)

    task = Task.query.get_or_404(task_id)

    # Remember original completed state
    was_completed = task.completed

    # Apply any updates
    if 'title' in data:
        task.title = data['title']
    if 'task_description' in data:
        task.task_description = data['task_description']
    if 'completed' in data:
        task.completed = data['completed']
    if 'node_id' in data:
        task.node_id = data['node_id']
    if 'form_id' in data:
        task.form_id = data['form_id']
    if 'sld_id' in data:
        task.sld_id = data['sld_id']
    if 'is_deleted' in data:
        task.is_deleted = data['is_deleted']
    if 'submission' in data:
        task.submission = data['submission']
    if 'submitted_at' in data:
        task.submitted_at = data['submitted_at']

    # If we just marked it completed (and it was previously not), and it's recurring:
    if data.get('completed') and not was_completed and task.recurring:
        if task.due_date and task.interval:
            next_due = task.due_date + relativedelta(months=task.interval)
            new_task = Task(
                title            = task.title,
                task_description = task.task_description,
                completed        = False,
                node_id          = task.node_id,
                form_id          = task.form_id,
                sld_id           = task.sld_id,
                is_deleted       = False,
                submission       = {},                  # start fresh
                submitted_at     = None,                # not yet submitted
                due_date         = next_due,
                created_at       = datetime.utcnow(),
                task_type        = task.task_type,
                recurring        = task.recurring,
                interval         = task.interval,
                procedure_id     = task.procedure_id,
                shortcut_id      = task.shortcut_id
            )
            db.session.add(new_task)
            db.session.flush()  # Add this to ensure the new task is persisted
            
            # Explicitly set submitted_at to None after adding to session
            new_task.submitted_at = None
            
            logger.info(
                "Scheduled next recurring task %s for %s with submitted_at=%s",
                new_task.id, next_due, new_task.submitted_at
            )

    # Commit both the update and (if created) the new task
    db.session.commit()

    result = task.to_dict()
    logger.info("UPDATE succeeded: %s", result)
    return jsonify(result), 200

@app.route('/task/create', methods=['POST'])
def create_task():
    data = request.get_json() or {}
    logger.info("CREATE /task/create with payload: %s", data)

    try:
        task = Task(
            id              = data.get('id'),
            title           = data.get('title'),
            task_description= data.get('task_description'),
            completed       = data.get('completed', False),
            node_id         = data.get('node_id'),
            form_id         = data.get('form_id'),
            sld_id          = data.get('sld_id'),
            is_deleted      = data.get('is_deleted', False),
            submission      = data.get('submission', {}),
            submitted_at    = data.get('submitted_at')  # if you want to allow custom timestamp
        )

        db.session.add(task)
        db.session.commit()

        return jsonify({"message": "Task created", "id": str(task.id)}), 201

    except Exception as e:
        logger.exception("Error creating task")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ─── Node, Edge, and SLD Endpoints ────────────────────────────────────────────

# Create
@app.route('/items', methods=['POST'])
def create_item():
    data = request.get_json() or {}
    logger.info("CREATE /items with payload: %s", data)

    id_to_use = data.get('id')
    try:
        if id_to_use:
            item_id = uuid.UUID(id_to_use)
        else:
            item_id = uuid.uuid4()
    except ValueError:
        abort(400, "Invalid 'id' format")

    if not data.get('name'):
        logger.warning("CREATE failed: 'name' missing")
        abort(400, "'name' is required")

    timestamp = datetime.utcnow()
    
    if data.get('timestamp'):
        try:
            timestamp = datetime.fromisoformat(data['timestamp'])
        except Exception as e:
            logger.error("Invalid timestamp format: %s", data['timestamp'])
            abort(400, "Invalid 'timestamp' format")

    item = Item(id=item_id, name=data['name'], timestamp=timestamp)
    db.session.add(item)
    db.session.commit()

    result = item.to_dict()
    logger.info("CREATE succeeded: %s", result)
    return jsonify(result), 201

# Read all
@app.route('/items', methods=['GET'])
def list_items():
    logger.info("READ ALL /items")
    items = Item.query.order_by(Item.timestamp).all()
    result = [i.to_dict() for i in items]
    logger.debug("READ ALL result count: %d", len(result))
    return jsonify(result), 200

# Read all nodes and edges
@app.route('/slddep/<uuid:sld_id>', methods=['GET'])
def get_sld_dep(sld_id):
    logger.info("READ SLD: %s", sld_id)
    sld = SLD.query.get_or_404(sld_id)
    nodes = Node.query.filter_by(sld_id=sld_id).all()
    edges = Edge.query.filter_by(sld_id=sld_id).all()
    photos = Photo.query.filter_by(sld_id=sld_id).all()
    ir_photos = IRPhoto.query.filter_by(sld_id=sld_id).all()
    ir_sessions = IRSession.query.filter_by(sld_id=sld_id).all()
    result = {
        "id": sld.to_dict().get("id"),
        "name": sld.to_dict().get("name"),
        "nodes": [node.to_dict() for node in nodes],
        "edges": [edge.to_dict() for edge in edges],
        "photos": [photo.to_dict() for photo in photos],
        "ir_photos": [ir_photo.to_dict() for ir_photo in ir_photos],
        "ir_sessions": [ir_session.to_dict() for ir_session in ir_sessions]
    }
    logger.info("READ succeeded: %s", result)
    return jsonify(result), 200

# Updated get_sld route
@app.route('/sld/<uuid:sld_id>', methods=['GET'])
def get_sld(sld_id):
    logger.info("READ SLD: %s", sld_id)
    sld = SLD.query.get_or_404(sld_id)
    nodes = Node.query.filter_by(sld_id=sld_id).all()
    edges = Edge.query.filter_by(sld_id=sld_id).all()
    photos = Photo.query.filter_by(sld_id=sld_id).all()
    ir_photos = IRPhoto.query.filter_by(sld_id=sld_id).all()
    ir_sessions = IRSession.query.filter_by(sld_id=sld_id).all()
    issues = Issue.query.filter_by(sld_id=sld_id).all()
    quotes = Quote.query.filter_by(sld_id=sld_id).all()
    tasks = Task.query.filter_by(sld_id=sld_id).all()
    logger.info("Found %d tasks for SLD %s", len(tasks), sld_id)

    task_dicts = []
    for task in tasks:
        logger.info("  ↳ processing Task.id=%s (sld_id=%s)", task.id, task.sld_id)
        try:
            d = task.to_dict()
            logger.info("      → to_dict succeeded: %s", { 'id': d['id'], 'submitted_at': d['submitted_at'] })
        except Exception as e:
            logger.error("      → to_dict FAILED for Task.id=%s: %s", task.id, e)
            d = None
        if d:
            task_dicts.append(d)
    
    # Get IDs for filtering mappings
    issue_ids = [issue.id for issue in issues]
    quote_ids = [quote.id for quote in quotes]
    task_ids = [task.id for task in tasks]
    session_ids = [session.id for session in ir_sessions]
    
    # Get mappings that involve entities from this SLD
    issue_task_mappings = MappingIssueTask.query.filter(
        (MappingIssueTask.issue_id.in_(issue_ids)) | 
        (MappingIssueTask.task_id.in_(task_ids))
    ).all() if issue_ids or task_ids else []
    
    task_session_mappings = MappingTaskSession.query.filter(
        (MappingTaskSession.task_id.in_(task_ids)) | 
        (MappingTaskSession.session_id.in_(session_ids))
    ).all() if task_ids or session_ids else []
    
    quote_task_mappings = MappingQuoteTask.query.filter(
        (MappingQuoteTask.quote_id.in_(quote_ids)) | 
        (MappingQuoteTask.task_id.in_(task_ids))
    ).all() if quote_ids or task_ids else []
    
    result = {
        "id": sld.to_dict().get("id"),
        "name": sld.to_dict().get("name"),
        "nodes": [node.to_dict() for node in nodes],
        "edges": [edge.to_dict() for edge in edges],
        "photos": [photo.to_dict() for photo in photos],
        "ir_photos": [ir_photo.to_dict() for ir_photo in ir_photos],
        "ir_sessions": [ir_session.to_dict() for ir_session in ir_sessions],
        "issues": [issue.to_dict() for issue in issues],
        "quotes": [quote.to_dict() for quote in quotes],
        "tasks": task_dicts,
        "mappings": {
            "issue_task": [mapping.to_dict() for mapping in issue_task_mappings],
            "task_session": [mapping.to_dict() for mapping in task_session_mappings],
            "quote_task": [mapping.to_dict() for mapping in quote_task_mappings]
        }
    }
    logger.info("READ succeeded: %s", result)
    return jsonify(result), 200

# Read all node classes
@app.route('/node_classes', methods=['GET'])
def get_node_classes():
    logger.info("READ NODE CLASSES")
    node_classes = NodeClass.query.all()
    result = [node_class.to_dict() for node_class in node_classes]
    logger.info("READ succeeded: %s", result)
    return jsonify(result), 200

# Read one
@app.route('/items/<uuid:item_id>', methods=['GET'])
def get_item(item_id):
    logger.info("READ /items/%s", item_id)
    item = Item.query.get_or_404(item_id)
    result = item.to_dict()
    logger.info("READ succeeded: %s", result)
    return jsonify(result), 200

# Node methods
@app.route('/node/update/<uuid:node_id>', methods=['PUT'])
def update_node(node_id):
    data = request.get_json() or {}
    logger.info("UPDATE /node/update/%s with payload: %s", node_id, data)

    node = Node.query.get_or_404(node_id)

    if 'type' in data:
        node.type = data['type']
    if 'label' in data:
        node.label = data['label']
    if 'x' in data:
        node.x = data['x']
    if 'y' in data:
        node.y = data['y']
    if 'width' in data:
        node.width = data['width']
    if 'height' in data:
        node.height = data['height']
    if 'is_deleted' in data:
        node.is_deleted = data['is_deleted']
    if 'parent_id' in data:
        node.parent_id = data['parent_id']
    if 'location' in data:
        node.location = data['location']
    if 'node_class' in data:
        node.node_class = data['node_class']
    if 'core_attributes' in data:
        node.core_attributes = data['core_attributes']
    if 'com' in data:
        node.com = data['com']
    if 'qr_code' in data:
        node.qr_code = data['qr_code']
        
    db.session.commit()

    result = node.to_dict()
    logger.info("UPDATE succeeded: %s", result)
    return jsonify(result), 200

@app.route('/node/create', methods=['POST'])
def create_node():
    data = request.get_json() or {}
    logger.info("CREATE /node/create with payload: %s", data)

    try:
        node = Node(
            id = data.get('id'),
            type = data.get('type'),
            label = data.get('label'),
            sld_id = data.get('sld_id'),
            parent_id = data.get('parent_id'),
            x = data.get('x', 0),
            y = data.get('y', 0),
            width = data.get('width', 80),
            height = data.get('height', 80),
            is_deleted = data.get('is_deleted'),
            location = data.get('location'),
            node_class = data.get('node_class'),
            core_attributes = data.get('core_attributes', []),
            com = data.get('com', 1),
            qr_code = data.get('qr_code')
        )

        db.session.add(node)
        db.session.commit()

        return jsonify({"message": "Node created", "id": str(node.id)}), 201

    except Exception as e:
        logger.exception("Error creating node")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
# Edge methods

# Read all edge classes
@app.route('/edge_classes', methods=['GET'])
def get_edge_classes():
    logger.info("READ EDGE CLASSES")
    edge_classes = EdgeClass.query.all()
    result = [edge_class.to_dict() for edge_class in edge_classes]
    logger.info("READ succeeded: %s", result)
    return jsonify(result), 200

@app.route('/edge/create', methods=['POST'])
def create_edge():
    data = request.get_json() or {}
    logger.info("CREATE /edge/create with payload: %s", data)

    try:
        edge = Edge(
            id = data.get('id'),
            source = data.get('source'),
            target = data.get('target'),
            sld_id = data.get('sld_id'),
            is_deleted = data.get('is_deleted'),
        )

        db.session.add(edge)
        db.session.commit()

        return jsonify({"message": "Edge created", "id": str(edge.id)}), 201

    except Exception as e:
        logger.exception("Error creating edge")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/edge/update/<uuid:edge_id>', methods=['PUT'])
def update_edge(edge_id):
    data = request.get_json() or {}
    logger.info("UPDATE /edge/update/%s with payload: %s", edge_id, data)

    edge = Edge.query.get_or_404(edge_id)

    if 'source' in data:
        edge.source = data['source']
    if 'target' in data:
        edge.target = data['target']
    if 'is_deleted' in data:
        edge.is_deleted = data['is_deleted']
    if 'core_attributes' in data:
        edge.core_attributes = data['core_attributes']
    if 'edge_class' in data:
        edge.edge_class = data['edge_class']
          
    db.session.commit()

    result = edge.to_dict()
    logger.info("UPDATE succeeded: %s", result)
    return jsonify(result), 200

# Photo methods
@app.route('/photo/create', methods=['POST'])
def create_photo():
    data = request.get_json() or {}
    logger.info("CREATE /photo/create with payload: %s", data)

    try:
        photo = Photo(
            id = data.get('id'),
            entity_id = data.get('entity_id'),
            url = data.get('url'),
            type = data.get('type'),
            sld_id = data.get('sld_id'),
            upload_needed = data.get('upload_needed', True),
            local_filepath = data.get('local_filepath'),
            filename = data.get('filename'),
            is_deleted = data.get('is_deleted')
        )

        db.session.add(photo)
        db.session.commit()

        return jsonify({"message": "Photo created", "id": str(photo.id)}), 201

    except Exception as e:
        logger.exception("Error creating photo")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
# Update photo 
@app.route('/photo/update/<uuid:photo_id>', methods=['PUT'])
def update_photo(photo_id):
    data = request.get_json() or {}
    logger.info("UPDATE /photo/update/%s with payload: %s", photo_id, data)

    photo = Photo.query.get_or_404(photo_id)

    if 'is_deleted' in data:
        photo.is_deleted = data['is_deleted']
    
    db.session.commit()

    result = photo.to_dict()
    logger.info("UPDATE succeeded: %s", result)
    return jsonify(result), 200

# Update item
@app.route('/items/<uuid:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.get_json() or {}
    logger.info("UPDATE /items/%s with payload: %s", item_id, data)

    item = Item.query.get_or_404(item_id)

    if 'name' in data:
        item.name = data['name']
    if 'timestamp' in data:
        try:
            item.timestamp = datetime.fromisoformat(data['timestamp'])
        except Exception as e:
            logger.error("Invalid timestamp on update: %s", data['timestamp'])
            abort(400, "Invalid 'timestamp' format")
    if 'sld' in data:
        item.sld = data['sld']

    db.session.commit()

    result = item.to_dict()
    logger.info("UPDATE succeeded: %s", result)
    return jsonify(result), 200

# Delete
@app.route('/items/<uuid:item_id>', methods=['DELETE'])
def delete_item(item_id):
    logger.info("DELETE /items/%s", item_id)
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    logger.info("DELETE succeeded for id: %s", item_id)
    return '', 204

# MAPPING ROUTES

# Issue-Task Mapping Routes
@app.route('/mapping/issue-task/create', methods=['POST'])
def create_issue_task_mapping():
    """Create a new issue-task mapping"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('issue_id') or not data.get('task_id'):
            return jsonify({
                'success': False,
                'error': 'Both issue_id and task_id are required'
            }), 400
        
        # Check if mapping already exists
        existing = MappingIssueTask.query.filter_by(
            issue_id=uuid.UUID(data['issue_id']),
            task_id=uuid.UUID(data['task_id'])
        ).first()
        
        if existing:
            # If it exists but is soft deleted, restore it
            if existing.is_deleted:
                existing.is_deleted = False
                db.session.commit()
                return jsonify({
                    'success': True,
                    'data': existing.to_dict(),
                    'message': 'Mapping restored'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Mapping already exists'
                }), 409
        
        # Create new mapping
        mapping = MappingIssueTask(
            issue_id=uuid.UUID(data['issue_id']),
            task_id=uuid.UUID(data['task_id']),
            is_deleted=data.get('is_deleted', False)
        )
        
        db.session.add(mapping)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': mapping.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/mapping/issue-task/update/<uuid:issue_id>/<uuid:task_id>', methods=['PUT'])
def update_issue_task_mapping(issue_id, task_id):
    """Update an issue-task mapping (mainly for soft delete)"""
    try:
        mapping = MappingIssueTask.query.filter_by(
            issue_id=issue_id,
            task_id=task_id
        ).first()
        
        if not mapping:
            return jsonify({
                'success': False,
                'error': 'Mapping not found'
            }), 404
        
        # Get update data
        data = request.get_json()
        
        # Update is_deleted if provided
        if 'is_deleted' in data:
            mapping.is_deleted = data['is_deleted']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': mapping.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

# Task-Session Mapping Routes
@app.route('/mapping/task-session/create', methods=['POST'])
def create_task_session_mapping():
    """Create a new task-session mapping"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('task_id') or not data.get('session_id'):
            return jsonify({
                'success': False,
                'error': 'Both task_id and session_id are required'
            }), 400
        
        # Check if mapping already exists
        existing = MappingTaskSession.query.filter_by(
            task_id=uuid.UUID(data['task_id']),
            session_id=uuid.UUID(data['session_id'])
        ).first()
        
        if existing:
            # If it exists but is soft deleted, restore it
            if existing.is_deleted:
                existing.is_deleted = False
                db.session.commit()
                return jsonify({
                    'success': True,
                    'data': existing.to_dict(),
                    'message': 'Mapping restored'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Mapping already exists'
                }), 409
        
        # Create new mapping
        mapping = MappingTaskSession(
            task_id=uuid.UUID(data['task_id']),
            session_id=uuid.UUID(data['session_id']),
            is_deleted=data.get('is_deleted', False)
        )
        
        db.session.add(mapping)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': mapping.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/mapping/task-session/update/<uuid:task_id>/<uuid:session_id>', methods=['PUT'])
def update_task_session_mapping(task_id, session_id):
    """Update a task-session mapping (mainly for soft delete)"""
    try:
        mapping = MappingTaskSession.query.filter_by(
            task_id=task_id,
            session_id=session_id
        ).first()
        
        if not mapping:
            return jsonify({
                'success': False,
                'error': 'Mapping not found'
            }), 404
        
        # Get update data
        data = request.get_json()
        
        # Update is_deleted if provided
        if 'is_deleted' in data:
            mapping.is_deleted = data['is_deleted']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': mapping.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

# Quote-Task Mapping Routes
@app.route('/mapping/quote-task/create', methods=['POST'])
def create_quote_task_mapping():
    """Create a new quote-task mapping"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('quote_id') or not data.get('task_id'):
            return jsonify({
                'success': False,
                'error': 'Both quote_id and task_id are required'
            }), 400
        
        # Check if mapping already exists
        existing = MappingQuoteTask.query.filter_by(
            quote_id=uuid.UUID(data['quote_id']),
            task_id=uuid.UUID(data['task_id'])
        ).first()
        
        if existing:
            # If it exists but is soft deleted, restore it
            if existing.is_deleted:
                existing.is_deleted = False
                db.session.commit()
                return jsonify({
                    'success': True,
                    'data': existing.to_dict(),
                    'message': 'Mapping restored'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Mapping already exists'
                }), 409
        
        # Create new mapping
        mapping = MappingQuoteTask(
            quote_id=uuid.UUID(data['quote_id']),
            task_id=uuid.UUID(data['task_id']),
            is_deleted=data.get('is_deleted', False)
        )
        
        db.session.add(mapping)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': mapping.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/mapping/quote-task/update/<uuid:quote_id>/<uuid:task_id>', methods=['PUT'])
def update_quote_task_mapping(quote_id, task_id):
    """Update a quote-task mapping (mainly for soft delete)"""
    try:
        mapping = MappingQuoteTask.query.filter_by(
            quote_id=quote_id,
            task_id=task_id
        ).first()
        
        if not mapping:
            return jsonify({
                'success': False,
                'error': 'Mapping not found'
            }), 404
        
        # Get update data
        data = request.get_json()
        
        # Update is_deleted if provided
        if 'is_deleted' in data:
            mapping.is_deleted = data['is_deleted']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': mapping.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

# ─── Bootstrap & Run ───────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        logger.info("Database tables created/verified")
    app.run(host='0.0.0.0', port=5000, debug=True)