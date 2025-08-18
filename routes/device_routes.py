import uuid
import json
import re
import logging
from flask import Blueprint, request, jsonify
from models.Device import Device
from models.db import db
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

device_bp = Blueprint('device', __name__, url_prefix='/device')

# Initialize SNS client
sns_client = boto3.client('sns', region_name='us-east-2')

APNS_SANDBOX_ARN = "arn:aws:sns:us-east-2:637423518604:app/APNS_SANDBOX/SwiftDataTutorial"
APNS_PRODUCTION_ARN = "arn:aws:sns:us-east-2:637423518604:app/APNS/SwiftDataTutorial"

def create_sns_endpoint(device_token, user_id, environment='production'):
    """Create or retrieve SNS endpoint for device token"""
    
    # Choose the correct Platform Application ARN
    platform_arn = APNS_SANDBOX_ARN if environment == 'sandbox' else APNS_PRODUCTION_ARN
    
    try:
        # Try to create a new endpoint
        response = sns_client.create_platform_endpoint(
            PlatformApplicationArn=platform_arn,
            Token=device_token,
            CustomUserData=json.dumps({
                'userId': str(user_id),
                'environment': environment
            })
        )
        
        endpoint_arn = response['EndpointArn']
        logger.info(f"Created new SNS endpoint: {endpoint_arn}")
        
        # Enable the endpoint (in case it was disabled)
        sns_client.set_endpoint_attributes(
            EndpointArn=endpoint_arn,
            Attributes={'Enabled': 'true'}
        )
        
        return endpoint_arn
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        
        if error_code == 'InvalidParameter':
            # Endpoint already exists, extract it from error message
            error_message = e.response['Error']['Message']
            
            # Parse the existing endpoint ARN from error message
            if 'Endpoint' in error_message and 'already exists' in error_message:
                match = re.search(r'Endpoint (arn:aws:sns:[^\s]+) already exists', error_message)
                if match:
                    endpoint_arn = match.group(1)
                    logger.info(f"Endpoint already exists: {endpoint_arn}")
                    
                    # Update the endpoint with new token (in case it changed)
                    try:
                        sns_client.set_endpoint_attributes(
                            EndpointArn=endpoint_arn,
                            Attributes={
                                'Token': device_token,
                                'Enabled': 'true'
                            }
                        )
                    except:
                        pass  # Endpoint might be deleted, will handle in next request
                    
                    return endpoint_arn
        
        logger.error(f"Error creating SNS endpoint: {str(e)}")
        raise e


@device_bp.route('/register', methods=['POST'])
def register_device():
    """Register or update a device token (upsert operation)"""
    try:
        data = request.get_json()
        logger.info("POST /device/register with payload: %s", data)
        
        # Required fields
        user_id = uuid.UUID(data['user_id'])
        device_id = data['device_id']
        device_token = data['device_token']
        environment = data.get('environment', 'production')
        
        # Create or update SNS endpoint
        try:
            endpoint_arn = create_sns_endpoint(
                device_token=device_token,
                user_id=user_id,
                environment=environment
            )
        except Exception as sns_error:
            logger.error(f"Failed to create SNS endpoint: {sns_error}")
            endpoint_arn = None  # Continue without SNS if it fails
        
        # Check if device exists
        device = Device.query.filter_by(
            user_id=user_id, 
            device_id=device_id
        ).first()
        
        if device:
            # Update existing device
            device.device_token = device_token
            device.platform = data.get('platform', device.platform)
            device.environment = environment
            device.endpoint_arn = endpoint_arn  # Update with SNS endpoint
            device.device_name = data.get('device_name', device.device_name)
            device.is_active = True  # Reactivate if it was inactive
            device.updated_at = datetime.now(timezone.utc)
            
            action = 'updated'
            logger.info(f"Updated device {device_id} with endpoint {endpoint_arn}")
        else:
            # Create new device
            device = Device(
                user_id=user_id,
                device_id=device_id,
                device_token=device_token,
                platform=data.get('platform', 'ios'),
                environment=environment,
                endpoint_arn=endpoint_arn,  # Store SNS endpoint
                device_name=data.get('device_name'),
                is_active=True
            )
            db.session.add(device)
            action = 'created'
            logger.info(f"Created device {device_id} with endpoint {endpoint_arn}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'action': action,
            'data': device.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error("Error registering device: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

    
@device_bp.route('/unregister/<uuid:user_id>/<device_id>', methods=['DELETE'])
def unregister_device(user_id, device_id):
    """Mark device as inactive (soft delete) or remove it (hard delete)"""
    try:
        logger.info("DELETE /device/unregister/%s/%s", user_id, device_id)
        
        device = Device.query.filter_by(
            user_id=user_id, 
            device_id=device_id
        ).first()
        
        if not device:
            return jsonify({
                'success': False,
                'error': 'Device not found'
            }), 404
        
        # Disable the SNS endpoint if it exists
        if device.endpoint_arn:
            try:
                sns_client.set_endpoint_attributes(
                    EndpointArn=device.endpoint_arn,
                    Attributes={'Enabled': 'false'}
                )
                logger.info(f"Disabled SNS endpoint: {device.endpoint_arn}")
            except Exception as e:
                logger.error(f"Failed to disable SNS endpoint: {e}")
        
        # Soft delete (mark as inactive)
        device.is_active = False
        device.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Device unregistered'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error("Error unregistering device: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# ADD THIS: Test endpoint to verify push notifications work
@device_bp.route('/test-notification/<uuid:user_id>', methods=['POST'])
def send_test_notification(user_id):
    """Send a test push notification to all user's devices"""
    try:
        # Get all active devices for the user
        devices = Device.query.filter_by(
            user_id=user_id,
            is_active=True
        ).all()
        
        if not devices:
            return jsonify({
                'success': False,
                'error': 'No active devices found for user'
            }), 404
        
        success_count = 0
        failures = []
        
        for device in devices:
            if not device.endpoint_arn:
                failures.append(f"Device {device.device_id} has no endpoint ARN")
                continue
            
            try:
                # Prepare message for both APNS and APNS_SANDBOX
                apns_message = json.dumps({
                    "aps": {
                        "alert": {
                            "title": "Test Notification 🧪",
                            "body": f"Hello! This is a test for {device.device_name or device.device_id}"
                        },
                        "sound": "default",
                        "badge": 1
                    },
                    "customData": {
                        "test": True,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                })
                
                # Send test notification
                message = {
                    "default": "Test notification from your IR app",
                    "APNS": apns_message,
                    "APNS_SANDBOX": apns_message
                }
                
                response = sns_client.publish(
                    TargetArn=device.endpoint_arn,
                    Message=json.dumps(message),
                    MessageStructure='json'
                )
                
                success_count += 1
                logger.info(f"✅ Sent notification to {device.device_name}: MessageId={response['MessageId']}")
                
            except ClientError as e:
                error_msg = f"Failed to send to {device.device_name or device.device_id}: {str(e)}"
                failures.append(error_msg)
                logger.error(error_msg)
                
                # If endpoint is disabled or deleted, mark device as inactive
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code in ['EndpointDisabled', 'InvalidParameter']:
                    device.is_active = False
                    db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Sent notifications to {success_count}/{len(devices)} devices',
            'successes': success_count,
            'total_devices': len(devices),
            'failures': failures if failures else None
        }), 200
        
    except Exception as e:
        logger.error("Error sending test notification: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500