from flask import Blueprint, jsonify
from models import Node, Edge, Photo, IRPhoto, Issue, Task
from models.db import db
from uuid import UUID

graph_bp = Blueprint('graph', __name__, url_prefix='/api/graph')

@graph_bp.route('/nodes/<node_id>', methods=['GET'])
def get_node_by_id(node_id):
    try:
        node_uuid = UUID(node_id)
        node = Node.query.filter_by(id=node_uuid).first()
        
        if not node:
            return jsonify({'error': 'Node not found'}), 404
        
        # Get related data
        photos = Photo.query.filter_by(entity_id=node_uuid).all()
        ir_photos = IRPhoto.query.filter_by(node_id=node_uuid).all()
        issues = Issue.query.filter_by(node_id=node_uuid).all()
        tasks = Task.query.filter_by(node_id=node_uuid).all()
        
        # Build response
        response = node.to_dict()
        response['photos'] = [photo.to_dict() for photo in photos]
        response['ir_photos'] = [ir_photo.to_dict() for ir_photo in ir_photos]
        response['issues'] = [issue.to_dict() for issue in issues]
        response['tasks'] = [task.to_dict() for task in tasks]
        
        return jsonify(response), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid UUID format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@graph_bp.route('/edges/<edge_id>', methods=['GET'])
def get_edge_by_id(edge_id):
    try:
        edge_uuid = UUID(edge_id)
        edge = Edge.query.filter_by(id=edge_uuid).first()
        
        if not edge:
            return jsonify({'error': 'Edge not found'}), 404
            
        return jsonify(edge.to_dict()), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid UUID format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500