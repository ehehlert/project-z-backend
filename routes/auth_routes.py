import os
import json
import logging
import boto3
import hashlib
import hmac
import base64
from flask import Blueprint, request, jsonify
from functools import wraps
from jose import jwt, JWTError
from botocore.exceptions import ClientError
import urllib.request
from dotenv import load_dotenv
from models.User import User
from models.db import db

load_dotenv()

logger = logging.getLogger(__name__)

# AWS Cognito Configuration
COGNITO_REGION = os.getenv('COGNITO_REGION', 'us-east-2')
COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID', 'us-east-2_zdUPoPij8')
COGNITO_CLIENT_ID = os.getenv('COGNITO_CLIENT_ID', '1spmv6ngivgbe7ldi3j1ksaoph')
COGNITO_CLIENT_SECRET = os.getenv('COGNITO_CLIENT_SECRET')  # Add this to your .env file

# Initialize Cognito client
cognito_client = boto3.client('cognito-idp', region_name=COGNITO_REGION)

# JWT Configuration
COGNITO_JWKS_URL = f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json'

# Cache for JWKS keys
_jwks_cache = None

auth_bp = Blueprint('auth', __name__)


def calculate_secret_hash(username):
    """Calculate the SECRET_HASH for Cognito requests when using a client secret"""
    if not COGNITO_CLIENT_SECRET:
        return None
    
    message = bytes(username + COGNITO_CLIENT_ID, 'utf-8')
    key = bytes(COGNITO_CLIENT_SECRET, 'utf-8')
    secret_hash = base64.b64encode(
        hmac.new(key, message, digestmod=hashlib.sha256).digest()
    ).decode()
    return secret_hash


def get_jwks():
    """Fetch and cache JWKS from Cognito"""
    global _jwks_cache
    if _jwks_cache is None:
        try:
            with urllib.request.urlopen(COGNITO_JWKS_URL) as response:
                _jwks_cache = json.loads(response.read())
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            raise
    return _jwks_cache


def verify_token(token):
    """Verify a JWT token from Cognito"""
    try:
        # Get the JWKS
        jwks = get_jwks()
        
        # Decode token header to get the key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')
        
        # Find the matching key
        key = None
        for k in jwks.get('keys', []):
            if k.get('kid') == kid:
                key = k
                break
        
        if not key:
            raise ValueError('Public key not found')
        
        # Verify and decode the token
        decoded = jwt.decode(
            token,
            key,
            algorithms=['RS256'],
            audience=COGNITO_CLIENT_ID,
            issuer=f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}'
        )
        
        return decoded
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise


def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        try:
            # Extract token from "Bearer <token>" format
            parts = auth_header.split()
            if parts[0].lower() != 'bearer' or len(parts) != 2:
                return jsonify({'error': 'Invalid authorization header format'}), 401
            
            token = parts[1]
            
            # Try to decode as access token first
            try:
                decoded = verify_token(token)
                # Access tokens have limited claims, so we'll use what's available
                request.cognito_user = decoded
                request.token_type = 'access'
            except:
                # If access token verification fails, try as ID token
                # ID tokens contain full user attributes
                decoded = jwt.decode(token, options={"verify_signature": False})
                request.cognito_user = decoded
                request.token_type = 'id'
            
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return jsonify({'error': 'Authentication failed'}), 401
    
    return decorated_function


@auth_bp.route('/auth/register', methods=['POST'])
def register():
    """Register a new user with Cognito"""
    try:
        data = request.get_json()
        logger.info(f"Registration attempt - Received data: {json.dumps({k: v for k, v in data.items() if k != 'password'}, default=str)}")
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            logger.warning(f"Registration failed - Missing required fields. Email provided: {bool(email)}, Password provided: {bool(password)}")
            return jsonify({'error': 'Email and password required'}), 400
        
        logger.info(f"Processing registration for email: {email}")
        
        # Additional user attributes (customize as needed)
        user_attributes = [
            {'Name': 'email', 'Value': email}
        ]
        
        # Add required attributes
        given_name = data.get('given_name', data.get('name', 'User').split()[0])
        family_name = data.get('family_name', data.get('name', 'User').split()[-1] if len(data.get('name', 'User').split()) > 1 else 'User')
        timezone = data.get('timezone', 'America/New_York')
        company_id = data.get('company_id')
        
        logger.info(f"User attributes - given_name: {given_name}, family_name: {family_name}, timezone: {timezone}, company_id: {company_id}")
        
        user_attributes.extend([
            {'Name': 'given_name', 'Value': given_name},
            {'Name': 'family_name', 'Value': family_name}
        ])
        
        # Only add timezone if it's actually configured as a custom attribute
        if timezone:
            user_attributes.append({'Name': 'zoneinfo', 'Value': timezone})
        
        # Add company_id as a custom attribute if provided
        if company_id:
            user_attributes.append({'Name': 'custom:company_id', 'Value': str(company_id)})
            logger.info(f"Adding company_id to Cognito attributes: {company_id}")
        
        # Add optional attributes if provided
        if data.get('name'):
            user_attributes.append({'Name': 'name', 'Value': data['name']})
        
        logger.info(f"Final user attributes being sent to Cognito: {user_attributes}")
        
        # Build the sign_up parameters
        sign_up_params = {
            'ClientId': COGNITO_CLIENT_ID,
            'Username': email,
            'Password': password,
            'UserAttributes': user_attributes
        }
        
        # Add SECRET_HASH if client secret is configured
        secret_hash = calculate_secret_hash(email)
        if secret_hash:
            sign_up_params['SecretHash'] = secret_hash
            logger.info("SECRET_HASH added to sign_up parameters")
        
        logger.info("Calling Cognito sign_up...")
        response = cognito_client.sign_up(**sign_up_params)
        logger.info(f"Cognito sign_up successful - UserSub: {response.get('UserSub')}, UserConfirmed: {response.get('UserConfirmed')}")
        
        # Create user record in database
        logger.info("Starting database user creation process...")
        try:
            # Only create user in database if company_id is provided and valid
            if company_id:
                logger.info(f"Company ID provided: {company_id}, attempting to create database user record")
                import uuid
                try:
                    # Validate company_id is a valid UUID
                    company_uuid = uuid.UUID(str(company_id))
                    logger.info(f"Company ID validated as UUID: {company_uuid}")
                    
                    # Check if user already exists
                    existing_user = User.query.get(response['UserSub'])
                    if existing_user:
                        logger.warning(f"User {email} with sub {response['UserSub']} already exists in database")
                    else:
                        new_user = User(
                            id=response['UserSub'],
                            username=email,
                            company_id=company_uuid
                        )
                        logger.info(f"Creating new User object - id: {response['UserSub']}, username: {email}, company_id: {company_uuid}")
                        
                        db.session.add(new_user)
                        logger.info("User added to session, attempting to commit...")
                        
                        db.session.commit()
                        logger.info(f"SUCCESS: User {email} created in database with company_id {company_uuid}")
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid company_id format: {company_id} - Error: {e}")
                    logger.error(f"Company ID type: {type(company_id)}")
                    db.session.rollback()
                except Exception as db_specific_error:
                    logger.error(f"Database-specific error while creating user: {db_specific_error}")
                    logger.error(f"Error type: {type(db_specific_error).__name__}")
                    db.session.rollback()
            else:
                logger.warning(f"No company_id provided in registration data - User {email} created in Cognito only, NOT in database")
        except Exception as db_error:
            logger.error(f"Unexpected error in database user creation block: {db_error}")
            logger.error(f"Error type: {type(db_error).__name__}")
            logger.error(f"Error details: {str(db_error)}")
            # Continue anyway - user is created in Cognito
        
        return jsonify({
            'message': 'User registered successfully',
            'user_sub': response['UserSub'],
            'confirmation_required': response.get('UserConfirmed', False) == False
        }), 201
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'UsernameExistsException':
            return jsonify({'error': 'User already exists'}), 409
        elif error_code == 'InvalidPasswordException':
            return jsonify({'error': 'Invalid password format'}), 400
        else:
            logger.error(f"Registration failed: {error_code} - {error_message}")
            return jsonify({'error': error_message}), 400
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/auth/confirm', methods=['POST'])
def confirm_registration():
    """Confirm user registration with verification code"""
    try:
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')
        
        if not email or not code:
            return jsonify({'error': 'Email and confirmation code required'}), 400
        
        # Build confirm_sign_up parameters
        confirm_params = {
            'ClientId': COGNITO_CLIENT_ID,
            'Username': email,
            'ConfirmationCode': code
        }
        
        # Add SECRET_HASH if client secret is configured
        secret_hash = calculate_secret_hash(email)
        if secret_hash:
            confirm_params['SecretHash'] = secret_hash
        
        response = cognito_client.confirm_sign_up(**confirm_params)
        
        return jsonify({'message': 'Email confirmed successfully'}), 200
        
    except ClientError as e:
        error_message = e.response['Error']['Message']
        logger.error(f"Confirmation failed: {error_message}")
        return jsonify({'error': error_message}), 400
    except Exception as e:
        logger.error(f"Confirmation error: {e}")
        return jsonify({'error': 'Confirmation failed'}), 500


@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """Authenticate user and return tokens"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        # Build auth parameters
        auth_params = {
            'USERNAME': email,
            'PASSWORD': password
        }
        
        # Add SECRET_HASH if client secret is configured
        secret_hash = calculate_secret_hash(email)
        if secret_hash:
            auth_params['SECRET_HASH'] = secret_hash
        
        response = cognito_client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters=auth_params
        )
        
        if 'ChallengeName' in response:
            return jsonify({
                'challenge': response['ChallengeName'],
                'session': response.get('Session'),
                'challenge_parameters': response.get('ChallengeParameters', {})
            }), 200
        
        # Return tokens
        return jsonify({
            'access_token': response['AuthenticationResult']['AccessToken'],
            'id_token': response['AuthenticationResult']['IdToken'],
            'refresh_token': response['AuthenticationResult']['RefreshToken'],
            'expires_in': response['AuthenticationResult']['ExpiresIn']
        }), 200
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'NotAuthorizedException':
            return jsonify({'error': 'Invalid credentials'}), 401
        elif error_code == 'UserNotConfirmedException':
            return jsonify({'error': 'User not confirmed'}), 403
        else:
            logger.error(f"Login failed: {error_code} - {error_message}")
            return jsonify({'error': error_message}), 400
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500


@auth_bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token using refresh token"""
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token required'}), 400
        
        # For refresh token, we don't have the username, so we can't calculate SECRET_HASH
        # Cognito doesn't require SECRET_HASH for REFRESH_TOKEN_AUTH flow
        response = cognito_client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refresh_token
            }
        )
        
        return jsonify({
            'access_token': response['AuthenticationResult']['AccessToken'],
            'id_token': response['AuthenticationResult']['IdToken'],
            'expires_in': response['AuthenticationResult']['ExpiresIn']
        }), 200
        
    except ClientError as e:
        error_message = e.response['Error']['Message']
        logger.error(f"Token refresh failed: {error_message}")
        return jsonify({'error': 'Invalid refresh token'}), 401
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        return jsonify({'error': 'Token refresh failed'}), 500


@auth_bp.route('/auth/logout', methods=['POST'])
@require_auth
def logout():
    """Sign out user from Cognito"""
    try:
        # Get the access token from the request
        auth_header = request.headers.get('Authorization')
        token = auth_header.split()[1]
        
        cognito_client.global_sign_out(
            AccessToken=token
        )
        
        return jsonify({'message': 'Logged out successfully'}), 200
        
    except ClientError as e:
        error_message = e.response['Error']['Message']
        logger.error(f"Logout failed: {error_message}")
        return jsonify({'error': error_message}), 400
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500


@auth_bp.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Initiate password reset flow"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        # Build forgot_password parameters
        forgot_params = {
            'ClientId': COGNITO_CLIENT_ID,
            'Username': email
        }
        
        # Add SECRET_HASH if client secret is configured
        secret_hash = calculate_secret_hash(email)
        if secret_hash:
            forgot_params['SecretHash'] = secret_hash
        
        response = cognito_client.forgot_password(**forgot_params)
        
        return jsonify({
            'message': 'Password reset code sent',
            'delivery': response.get('CodeDeliveryDetails', {})
        }), 200
        
    except ClientError as e:
        error_message = e.response['Error']['Message']
        logger.error(f"Forgot password failed: {error_message}")
        return jsonify({'error': error_message}), 400
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        return jsonify({'error': 'Failed to initiate password reset'}), 500


@auth_bp.route('/auth/respond-to-challenge', methods=['POST'])
def respond_to_challenge():
    """Respond to authentication challenges like NEW_PASSWORD_REQUIRED"""
    try:
        data = request.get_json()
        challenge_name = data.get('challenge_name')
        session = data.get('session')
        
        if not challenge_name or not session:
            return jsonify({'error': 'Challenge name and session required'}), 400
        
        if challenge_name == 'NEW_PASSWORD_REQUIRED':
            new_password = data.get('new_password')
            email = data.get('email')
            
            if not new_password or not email:
                return jsonify({'error': 'New password and email required'}), 400
            
            # Build challenge response
            challenge_responses = {
                'USERNAME': email,
                'NEW_PASSWORD': new_password
            }
            
            # Add required attributes if provided
            if data.get('given_name'):
                challenge_responses['userAttributes.given_name'] = data['given_name']
            if data.get('family_name'):
                challenge_responses['userAttributes.family_name'] = data['family_name']
            if data.get('timezone'):
                challenge_responses['userAttributes.zoneinfo'] = data['timezone']
            if data.get('company_id'):
                challenge_responses['userAttributes.custom:company_id'] = str(data['company_id'])
            
            # Add SECRET_HASH if client secret is configured
            secret_hash = calculate_secret_hash(email)
            if secret_hash:
                challenge_responses['SECRET_HASH'] = secret_hash
            
            response = cognito_client.respond_to_auth_challenge(
                ClientId=COGNITO_CLIENT_ID,
                ChallengeName='NEW_PASSWORD_REQUIRED',
                Session=session,
                ChallengeResponses=challenge_responses
            )
            
            # Check if authentication is complete
            if 'AuthenticationResult' in response:
                # Decode the ID token to get the user's sub
                id_token = response['AuthenticationResult']['IdToken']
                try:
                    decoded_token = jwt.decode(id_token, options={"verify_signature": False})
                    user_sub = decoded_token.get('sub')
                    
                    # Create user record in database if it doesn't exist
                    if user_sub and data.get('company_id'):
                        existing_user = User.query.get(user_sub)
                        if not existing_user:
                            new_user = User(
                                id=user_sub,
                                username=email,
                                company_id=data['company_id']
                            )
                            db.session.add(new_user)
                            db.session.commit()
                except Exception as db_error:
                    logger.error(f"Failed to create/check user in database: {db_error}")
                    # Continue anyway - authentication succeeded
                
                return jsonify({
                    'access_token': response['AuthenticationResult']['AccessToken'],
                    'id_token': response['AuthenticationResult']['IdToken'],
                    'refresh_token': response['AuthenticationResult']['RefreshToken'],
                    'expires_in': response['AuthenticationResult']['ExpiresIn']
                }), 200
            else:
                return jsonify({
                    'challenge': response.get('ChallengeName'),
                    'session': response.get('Session'),
                    'challenge_parameters': response.get('ChallengeParameters', {})
                }), 200
        
        return jsonify({'error': f'Challenge {challenge_name} not supported'}), 400
        
    except ClientError as e:
        error_message = e.response['Error']['Message']
        logger.error(f"Challenge response failed: {error_message}")
        return jsonify({'error': error_message}), 400
    except Exception as e:
        logger.error(f"Challenge response error: {e}")
        return jsonify({'error': 'Failed to respond to challenge'}), 500


@auth_bp.route('/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset password with confirmation code"""
    try:
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')
        new_password = data.get('new_password')
        
        if not all([email, code, new_password]):
            return jsonify({'error': 'Email, code, and new password required'}), 400
        
        # Build confirm_forgot_password parameters
        confirm_params = {
            'ClientId': COGNITO_CLIENT_ID,
            'Username': email,
            'ConfirmationCode': code,
            'Password': new_password
        }
        
        # Add SECRET_HASH if client secret is configured
        secret_hash = calculate_secret_hash(email)
        if secret_hash:
            confirm_params['SecretHash'] = secret_hash
        
        response = cognito_client.confirm_forgot_password(**confirm_params)
        
        return jsonify({'message': 'Password reset successfully'}), 200
        
    except ClientError as e:
        error_message = e.response['Error']['Message']
        logger.error(f"Password reset failed: {error_message}")
        return jsonify({'error': error_message}), 400
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        return jsonify({'error': 'Failed to reset password'}), 500


@auth_bp.route('/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user information"""
    try:
        # User info is added to request by require_auth decorator
        user_info = request.cognito_user
        
        return jsonify({
            'sub': user_info.get('sub'),
            'email': user_info.get('email'),
            'email_verified': user_info.get('email_verified'),
            'name': user_info.get('name'),
            'given_name': user_info.get('given_name'),
            'family_name': user_info.get('family_name'),
            'company_id': user_info.get('custom:company_id'),
            'timezone': user_info.get('zoneinfo'),
            'cognito_username': user_info.get('cognito:username')
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        return jsonify({'error': 'Failed to retrieve user information'}), 500