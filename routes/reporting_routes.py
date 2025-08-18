import uuid
import json
import logging
from flask import Blueprint, request, jsonify
from models.Device import Device
from models.db import db
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

reporting_bp = Blueprint('reporting', __name__, url_prefix='/reporting')

# Step Function ARN
STEP_FUNCTION_ARN = "arn:aws:states:us-east-2:637423518604:stateMachine:pgz-reporting-step-function"

def get_stepfunctions_client():
    """Get or create Step Functions client - lazy initialization to avoid debug mode issues"""
    if not hasattr(get_stepfunctions_client, '_client'):
        get_stepfunctions_client._client = boto3.client('stepfunctions', region_name='us-east-2')
    return get_stepfunctions_client._client


@reporting_bp.route('/generate', methods=['POST'])
def generate_report():
    """
    Start report generation via Step Function
    
    Expected payload from iOS:
    {
        "ir_session_id": "33a6730c-a888-4624-95c9-ab1d1b76c3f3",
        "type": "session",
        "user_id": "8aea6063-f7b6-4187-8025-2fbbc8f29a35",
        "device_id": "1E32EB25-371A-472B-82BB-845FA56F1AA3"
    }
    """
    try:
        data = request.get_json()
        logger.info("POST /reporting/generate with payload: %s", data)
        
        # Extract required fields
        ir_session_id = data.get('ir_session_id')
        report_type = data.get('type', 'session')
        user_id = data.get('user_id')
        device_id = data.get('device_id')
        
        # Validate required fields
        if not all([ir_session_id, user_id, device_id]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: ir_session_id, user_id, device_id'
            }), 400
        
        # Get the specific device that's requesting the report
        device = Device.query.filter_by(
            user_id=uuid.UUID(user_id),
            device_id=device_id,
            is_active=True
        ).first()
        
        if not device:
            return jsonify({
                'success': False,
                'error': 'Device not found or inactive'
            }), 404
        
        if not device.endpoint_arn:
            return jsonify({
                'success': False,
                'error': 'Device has no push notification endpoint'
            }), 400
        
        # Prepare the Step Function input
        step_function_input = {
            "ir_session_id": ir_session_id,
            "type": report_type,
            "device_endpoints": [
                {
                    "endpoint_arn": device.endpoint_arn,
                    "device_name": device.device_name or device_id
                }
            ]
        }
        
        # Start the Step Function execution
        response = get_stepfunctions_client().start_execution(
            stateMachineArn=STEP_FUNCTION_ARN,
            input=json.dumps(step_function_input)
        )
        
        execution_arn = response['executionArn']
        logger.info(f"Started Step Function execution: {execution_arn}")
        
        return jsonify({
            'success': True,
            'execution_arn': execution_arn
        }), 200
        
    except Exception as e:
        logger.error("Error starting report generation: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
@reporting_bp.route('/generate_simple', methods=['POST'])
def generate_report_simple():
    """
    Start report generation via Step Function
    
    Expected payload from frontend:
    {
        "ir_session_id": "33a6730c-a888-4624-95c9-ab1d1b76c3f3",
        "type": "session"
    }
    """
    try:
        data = request.get_json()
        logger.info("POST /reporting/generate_simple with payload: %s", data)
        
        # Extract required fields
        ir_session_id = data.get('ir_session_id')
        report_type = data.get('type', 'session')
        
        # Validate required fields
        if not all([ir_session_id]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: ir_session_id, user_id, device_id'
            }), 400
        
        # Prepare the Step Function input
        step_function_input = {
            "ir_session_id": ir_session_id,
            "type": report_type,
            "device_endpoints": []
        }
        
        # Start the Step Function execution
        response = get_stepfunctions_client().start_execution(
            stateMachineArn=STEP_FUNCTION_ARN,
            input=json.dumps(step_function_input)
        )
        
        execution_arn = response['executionArn']
        logger.info(f"Started Step Function execution: {execution_arn}")
        
        return jsonify({
            'success': True,
            'execution_arn': execution_arn
        }), 200
        
    except Exception as e:
        logger.error("Error starting report generation: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500