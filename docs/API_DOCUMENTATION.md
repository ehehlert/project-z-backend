# Authentication API Documentation

## Overview
This API uses AWS Cognito for user authentication and authorization. All protected endpoints require a valid JWT token in the Authorization header.

## Base URL
- Development: `http://localhost:5001`
- Production: `https://your-domain.com`

## Authentication
For protected endpoints, include the access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## Authentication Endpoints

### 1. User Registration
**Endpoint:** `POST /auth/register`

Creates a new user account. Email confirmation is required before the user can login.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!",
  "given_name": "John",
  "family_name": "Doe",
  "timezone": "America/New_York",
  "company_id": "company-123"
}
```

**Required Fields:**
- `email` (string): User's email address (used as username)
- `password` (string): Must meet Cognito password requirements:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one number
  - At least one special character
- `given_name` (string): User's first name
- `family_name` (string): User's last name

**Optional Fields:**
- `timezone` (string): User's timezone (defaults to "America/New_York")
- `company_id` (string): User's company identifier
- `name` (string): Full name (optional additional field)

**Success Response (201):**
```json
{
  "message": "User registered successfully",
  "user_sub": "123e4567-e89b-12d3-a456-426614174000",
  "confirmation_required": true
}
```

**Error Responses:**
- `400 Bad Request`: Missing required fields or invalid password format
- `409 Conflict`: User already exists

**Example:**
```bash
curl -X POST http://localhost:5001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "given_name": "Jane",
    "family_name": "Smith",
    "timezone": "America/Chicago",
    "company_id": "company-456"
  }'
```

---

### 2. User Login
**Endpoint:** `POST /auth/login`

Authenticates a user and returns JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "UserPassword123!"
}
```

**Required Fields:**
- `email` (string): User's email address
- `password` (string): User's password

**Success Response (200):**
```json
{
  "access_token": "eyJraWQiOiJJXC9ETnAyZk05...",
  "id_token": "eyJraWQiOiJoOGM0cVNIM1JhYm1a...",
  "refresh_token": "eyJjdHkiOiJKV1QiLCJlbmMiOi...",
  "expires_in": 3600
}
```

**Challenge Response (200):**
If the user needs to complete a challenge (e.g., set a new password):
```json
{
  "challenge": "NEW_PASSWORD_REQUIRED",
  "session": "AYABeN2NMwiHCiZ7hPvppYLospk...",
  "challenge_parameters": {
    "USER_ID_FOR_SRP": "916be5f0-00a1-7079-0310-e888fdc35924",
    "requiredAttributes": "[\"userAttributes.zoneinfo\",\"userAttributes.family_name\",\"userAttributes.given_name\"]",
    "userAttributes": "{\"email\":\"user@example.com\",\"email_verified\":\"true\"}"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Missing email or password
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: User not confirmed

**Example:**
```bash
curl -X POST http://localhost:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "UserPassword123!"
  }'
```

---

### 3. Respond to Authentication Challenge
**Endpoint:** `POST /auth/respond-to-challenge`

Handles authentication challenges, particularly the NEW_PASSWORD_REQUIRED challenge when a user needs to set their permanent password.

**Request Body for NEW_PASSWORD_REQUIRED:**
```json
{
  "challenge_name": "NEW_PASSWORD_REQUIRED",
  "session": "AYABeN2NMwiHCiZ7hPvppYLospk...",
  "email": "user@example.com",
  "new_password": "NewSecurePass123!",
  "given_name": "John",
  "family_name": "Doe",
  "timezone": "America/Chicago",
  "company_id": "company-123"
}
```

**Required Fields:**
- `challenge_name` (string): The type of challenge (e.g., "NEW_PASSWORD_REQUIRED")
- `session` (string): Session token from the login response
- `email` (string): User's email address
- `new_password` (string): The new password to set

**Required Fields for NEW_PASSWORD_REQUIRED (if not already set):**
- `given_name` (string): User's first name
- `family_name` (string): User's last name
- `timezone` (string): User's timezone

**Optional Fields:**
- `company_id` (string): User's company identifier

**Success Response (200):**
```json
{
  "access_token": "eyJraWQiOiJJXC9ETnAyZk05...",
  "id_token": "eyJraWQiOiJoOGM0cVNIM1JhYm1a...",
  "refresh_token": "eyJjdHkiOiJKV1QiLCJlbmMiOi...",
  "expires_in": 3600
}
```

**Error Responses:**
- `400 Bad Request`: Missing required fields or unsupported challenge type

**Example:**
```bash
# First, get the session from login
LOGIN_RESPONSE=$(curl -X POST http://localhost:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "TempPassword123!"
  }')

SESSION=$(echo $LOGIN_RESPONSE | jq -r '.session')

# Then respond to the challenge
curl -X POST http://localhost:5001/auth/respond-to-challenge \
  -H "Content-Type: application/json" \
  -d "{
    \"challenge_name\": \"NEW_PASSWORD_REQUIRED\",
    \"session\": \"$SESSION\",
    \"email\": \"user@example.com\",
    \"new_password\": \"NewSecurePass123!\",
    \"given_name\": \"John\",
    \"family_name\": \"Doe\",
    \"timezone\": \"America/Chicago\"
  }"
```

---

### 4. Confirm Registration
**Endpoint:** `POST /auth/confirm`

Confirms user registration with the verification code sent to their email.

**Request Body:**
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**Success Response (200):**
```json
{
  "message": "Email confirmed successfully"
}
```

---

### 5. Refresh Access Token
**Endpoint:** `POST /auth/refresh`

Refreshes an expired access token using a refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJjdHkiOiJKV1QiLCJlbmMiOi..."
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJraWQiOiJJXC9ETnAyZk05...",
  "id_token": "eyJraWQiOiJoOGM0cVNIM1JhYm1a...",
  "expires_in": 3600
}
```

---

### 6. Get Current User Info
**Endpoint:** `GET /auth/me`

**Authorization Required:** Yes

Returns information about the currently authenticated user.

**Success Response (200):**
```json
{
  "sub": "916be5f0-00a1-7079-0310-e888fdc35924",
  "email": "user@example.com",
  "email_verified": true,
  "name": "John Doe",
  "given_name": "John",
  "family_name": "Doe",
  "company_id": "company-123",
  "timezone": "America/Chicago",
  "cognito_username": "916be5f0-00a1-7079-0310-e888fdc35924"
}
```

**Example:**
```bash
curl -X GET http://localhost:5001/auth/me \
  -H "Authorization: Bearer <access_token>"
```

---

### 7. Logout
**Endpoint:** `POST /auth/logout`

**Authorization Required:** Yes

Signs out the user from all devices.

**Success Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

---

### 8. Forgot Password
**Endpoint:** `POST /auth/forgot-password`

Initiates the password reset flow by sending a verification code to the user's email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200):**
```json
{
  "message": "Password reset code sent",
  "delivery": {
    "DeliveryMedium": "EMAIL",
    "Destination": "u***@example.com"
  }
}
```

---

### 9. Reset Password
**Endpoint:** `POST /auth/reset-password`

Completes the password reset using the verification code.

**Request Body:**
```json
{
  "email": "user@example.com",
  "code": "123456",
  "new_password": "NewSecurePass123!"
}
```

**Success Response (200):**
```json
{
  "message": "Password reset successfully"
}
```

---

## Token Information

### Token Types
1. **Access Token**: Used for API authorization (expires in 1 hour)
2. **ID Token**: Contains user identity information
3. **Refresh Token**: Used to obtain new access tokens (long-lived)

### Token Expiration
- Access tokens expire after 1 hour (3600 seconds)
- Use the refresh token to obtain a new access token without re-authentication
- Store refresh tokens securely as they have a longer lifetime

### Protected Endpoints
To protect any endpoint in your application, use the `@require_auth` decorator:

```python
from routes.auth_routes import require_auth

@app.route('/protected-endpoint')
@require_auth
def protected_endpoint():
    # Access user info via request.cognito_user
    user = request.cognito_user
    return jsonify({'user_id': user['sub']})
```

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: User not confirmed or lacks permissions
- `409 Conflict`: Resource already exists
- `500 Internal Server Error`: Server error

---

## Testing with cURL

### Complete Registration Flow
```bash
# 1. Register a new user
curl -X POST http://localhost:5001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "given_name": "Test",
    "family_name": "User",
    "timezone": "America/New_York"
  }'

# 2. Confirm email (with code from email)
curl -X POST http://localhost:5001/auth/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "code": "123456"
  }'

# 3. Login
curl -X POST http://localhost:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'

# 4. Use access token for protected endpoints
ACCESS_TOKEN="<token_from_login_response>"
curl -X GET http://localhost:5001/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### Handle NEW_PASSWORD_REQUIRED Challenge
```bash
# 1. Login with temporary password
RESPONSE=$(curl -X POST http://localhost:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "TempPassword123!"
  }')

# 2. Extract session
SESSION=$(echo $RESPONSE | jq -r '.session')

# 3. Set new password
curl -X POST http://localhost:5001/auth/respond-to-challenge \
  -H "Content-Type: application/json" \
  -d "{
    \"challenge_name\": \"NEW_PASSWORD_REQUIRED\",
    \"session\": \"$SESSION\",
    \"email\": \"admin@example.com\",
    \"new_password\": \"NewPassword123!\",
    \"given_name\": \"Admin\",
    \"family_name\": \"User\",
    \"timezone\": \"America/Chicago\"
  }"
```