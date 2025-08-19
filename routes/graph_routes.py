from flask import Blueprint, jsonify
from models import Node, Edge
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
            
        return jsonify(node.to_dict()), 200
        
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