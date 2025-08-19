# Authentication Quick Start Guide

## Overview
You can use these APIs directly without Cognito's hosted UI. This gives you full control over the authentication flow and user experience.

## Token Types Explained

After login, you receive three tokens:

| Token | Purpose | Contains | Use For |
|-------|---------|----------|---------|
| **access_token** | API Authorization | Minimal (just user ID) | Protecting API endpoints |
| **id_token** | User Identity | Full user attributes (name, email, company_id, etc.) | Getting user profile info |
| **refresh_token** | Token Renewal | No user data | Getting new tokens without re-login |

## Basic Flow

### 1. Register New User
```javascript
const response = await fetch('http://api.example.com/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePass123!',
    given_name: 'John',
    family_name: 'Doe',
    timezone: 'America/Chicago',
    company_id: 'company-123'
  })
});
```

### 2. Confirm Email
```javascript
// User receives email with 6-digit code
const response = await fetch('http://api.example.com/auth/confirm', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    code: '123456'
  })
});
```

### 3. Login
```javascript
const response = await fetch('http://api.example.com/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePass123!'
  })
});

const tokens = await response.json();
// Save these tokens:
localStorage.setItem('id_token', tokens.id_token);
localStorage.setItem('access_token', tokens.access_token);
localStorage.setItem('refresh_token', tokens.refresh_token);
```

### 4. Get User Info
```javascript
// IMPORTANT: Use ID token for user profile data
const idToken = localStorage.getItem('id_token');

const response = await fetch('http://api.example.com/auth/me', {
  headers: {
    'Authorization': `Bearer ${idToken}`  // Use id_token, NOT access_token
  }
});

const userInfo = await response.json();
// Returns: { email, given_name, family_name, company_id, timezone, etc. }
```

### 5. Call Protected APIs
```javascript
// For other API endpoints, you can use either token
const accessToken = localStorage.getItem('access_token');

const response = await fetch('http://api.example.com/sld/123', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
```

## Common Mistakes

### ❌ Wrong: Using access_token for user info
```javascript
// This returns mostly null values
fetch('/auth/me', {
  headers: { 'Authorization': `Bearer ${accessToken}` }
});
```

### ✅ Correct: Using id_token for user info
```javascript
// This returns all user attributes
fetch('/auth/me', {
  headers: { 'Authorization': `Bearer ${idToken}` }
});
```

## Token Expiration

- Tokens expire after 1 hour
- Check for 401 responses and refresh:

```javascript
async function refreshTokens() {
  const refreshToken = localStorage.getItem('refresh_token');
  
  const response = await fetch('http://api.example.com/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      refresh_token: refreshToken
    })
  });
  
  const newTokens = await response.json();
  localStorage.setItem('id_token', newTokens.id_token);
  localStorage.setItem('access_token', newTokens.access_token);
  // Note: refresh_token doesn't change
}
```

## Password Reset Flow

### 1. Request Reset Code
```javascript
await fetch('http://api.example.com/auth/forgot-password', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com'
  })
});
```

### 2. Reset with Code
```javascript
await fetch('http://api.example.com/auth/reset-password', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    code: '123456',
    new_password: 'NewSecurePass123!'
  })
});
```

## Admin-Created Users

If a user was created by an admin, they'll need to set a permanent password on first login:

```javascript
// 1. Initial login returns challenge
const loginResponse = await fetch('/auth/login', {...});
const challenge = await loginResponse.json();

if (challenge.challenge === 'NEW_PASSWORD_REQUIRED') {
  // 2. Respond to challenge
  const response = await fetch('/auth/respond-to-challenge', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      challenge_name: 'NEW_PASSWORD_REQUIRED',
      session: challenge.session,
      email: 'user@example.com',
      new_password: 'NewPassword123!',
      given_name: 'John',
      family_name: 'Doe',
      timezone: 'America/Chicago',
      company_id: 'company-123'
    })
  });
  
  const tokens = await response.json();
  // Save tokens as usual
}
```

## No Hosted UI Needed!

You don't need Cognito's hosted UI at all. These APIs provide everything you need:
- ✅ User registration
- ✅ Email confirmation
- ✅ Login/logout
- ✅ Password reset
- ✅ Token refresh
- ✅ User profile management

Build your own UI and call these endpoints directly for complete control over the user experience.