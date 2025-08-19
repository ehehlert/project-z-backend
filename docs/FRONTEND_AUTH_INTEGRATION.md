# Frontend Authentication Integration Guide

## React/Next.js Example Implementation

### Auth Service Class
```javascript
// services/authService.js
class AuthService {
  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
  }

  // Store tokens securely
  saveTokens(tokens) {
    localStorage.setItem('id_token', tokens.id_token);
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
    localStorage.setItem('token_expiry', Date.now() + (tokens.expires_in * 1000));
  }

  // Get appropriate token for different uses
  getIdToken() {
    return localStorage.getItem('id_token');
  }

  getAccessToken() {
    return localStorage.getItem('access_token');
  }

  // Check if tokens are expired
  isTokenExpired() {
    const expiry = localStorage.getItem('token_expiry');
    return !expiry || Date.now() > parseInt(expiry);
  }

  // Clear all tokens
  clearTokens() {
    localStorage.removeItem('id_token');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_expiry');
  }

  // Register new user
  async register(userData) {
    const response = await fetch(`${this.baseURL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Registration failed');
    }

    return response.json();
  }

  // Confirm email
  async confirmEmail(email, code) {
    const response = await fetch(`${this.baseURL}/auth/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, code })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Confirmation failed');
    }

    return response.json();
  }

  // Login
  async login(email, password) {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    // Check if it's a challenge response
    if (data.challenge) {
      return { needsChallenge: true, ...data };
    }

    // Save tokens if login successful
    if (data.access_token) {
      this.saveTokens(data);
    }

    return data;
  }

  // Handle password challenge for admin-created users
  async respondToChallenge(challengeData) {
    const response = await fetch(`${this.baseURL}/auth/respond-to-challenge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(challengeData)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Challenge response failed');
    }

    const data = await response.json();
    
    // Save tokens after successful challenge
    if (data.access_token) {
      this.saveTokens(data);
    }

    return data;
  }

  // Get current user info - USES ID TOKEN
  async getCurrentUser() {
    const idToken = this.getIdToken();
    
    if (!idToken) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${this.baseURL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${idToken}`  // IMPORTANT: Use ID token here
      }
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token expired, try to refresh
        await this.refreshTokens();
        return this.getCurrentUser(); // Retry with new token
      }
      throw new Error('Failed to get user info');
    }

    return response.json();
  }

  // Refresh tokens
  async refreshTokens() {
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch(`${this.baseURL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    if (!response.ok) {
      this.clearTokens();
      throw new Error('Failed to refresh tokens');
    }

    const data = await response.json();
    this.saveTokens({ ...data, refresh_token: refreshToken });
    return data;
  }

  // Logout
  async logout() {
    const accessToken = this.getAccessToken();
    
    if (accessToken) {
      try {
        await fetch(`${this.baseURL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`
          }
        });
      } catch (error) {
        console.error('Logout error:', error);
      }
    }
    
    this.clearTokens();
  }

  // Make authenticated API calls - USES ACCESS TOKEN
  async authenticatedFetch(url, options = {}) {
    const accessToken = this.getAccessToken();
    
    if (!accessToken) {
      throw new Error('No authentication token found');
    }

    // Check if token is expired
    if (this.isTokenExpired()) {
      await this.refreshTokens();
    }

    const response = await fetch(`${this.baseURL}${url}`, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${this.getAccessToken()}`,
        'Content-Type': 'application/json'
      }
    });

    if (response.status === 401) {
      // Token expired, refresh and retry
      await this.refreshTokens();
      return this.authenticatedFetch(url, options);
    }

    return response;
  }
}

export default new AuthService();
```

### React Components

#### Login Component
```jsx
// components/Login.jsx
import { useState } from 'react';
import authService from '../services/authService';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [challenge, setChallenge] = useState(null);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const result = await authService.login(email, password);
      
      if (result.needsChallenge) {
        // Handle NEW_PASSWORD_REQUIRED challenge
        setChallenge(result);
      } else {
        // Login successful, redirect
        window.location.href = '/dashboard';
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleChallengeResponse = async (newPassword, attributes) => {
    try {
      await authService.respondToChallenge({
        challenge_name: challenge.challenge,
        session: challenge.session,
        email,
        new_password: newPassword,
        ...attributes
      });
      
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err.message);
    }
  };

  if (challenge) {
    return (
      <ChallengeForm 
        onSubmit={handleChallengeResponse}
        error={error}
      />
    );
  }

  return (
    <form onSubmit={handleLogin}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      {error && <p className="error">{error}</p>}
      <button type="submit">Login</button>
    </form>
  );
}
```

#### User Profile Component
```jsx
// components/UserProfile.jsx
import { useState, useEffect } from 'react';
import authService from '../services/authService';

export default function UserProfile() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const userData = await authService.getCurrentUser();
      setUser(userData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!user) return <div>No user data</div>;

  return (
    <div>
      <h2>User Profile</h2>
      <p>Email: {user.email}</p>
      <p>Name: {user.given_name} {user.family_name}</p>
      <p>Company: {user.company_id}</p>
      <p>Timezone: {user.timezone}</p>
      <p>Email Verified: {user.email_verified ? 'Yes' : 'No'}</p>
    </div>
  );
}
```

#### Protected Route Wrapper
```jsx
// components/ProtectedRoute.jsx
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import authService from '../services/authService';

export default function ProtectedRoute({ children }) {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = authService.getIdToken();
      
      if (!token) {
        router.push('/login');
        return;
      }

      // Verify token by getting user info
      await authService.getCurrentUser();
      setIsAuthenticated(true);
    } catch (error) {
      console.error('Auth check failed:', error);
      authService.clearTokens();
      router.push('/login');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return isAuthenticated ? children : null;
}
```

### API Interceptor for Axios
```javascript
// utils/axiosConfig.js
import axios from 'axios';
import authService from '../services/authService';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL
});

// Request interceptor to add token
apiClient.interceptors.request.use(
  async (config) => {
    // Use ID token for /auth/me, access token for everything else
    const token = config.url.includes('/auth/me') 
      ? authService.getIdToken()
      : authService.getAccessToken();
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        await authService.refreshTokens();
        
        // Retry with new token
        const token = originalRequest.url.includes('/auth/me')
          ? authService.getIdToken()
          : authService.getAccessToken();
        
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        authService.clearTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
```

## Common Issues and Solutions

### Issue: Getting null values from /auth/me
**Cause:** Using access_token instead of id_token
**Solution:** 
```javascript
// Wrong
fetch('/auth/me', {
  headers: { 'Authorization': `Bearer ${accessToken}` }
});

// Correct
fetch('/auth/me', {
  headers: { 'Authorization': `Bearer ${idToken}` }
});
```

### Issue: Token expired errors
**Solution:** Implement automatic token refresh
```javascript
// Check before making requests
if (authService.isTokenExpired()) {
  await authService.refreshTokens();
}
```

### Issue: Lost authentication after page refresh
**Solution:** Tokens are stored in localStorage and persist across refreshes. Check on app initialization:
```javascript
// In your app initialization
useEffect(() => {
  const token = authService.getIdToken();
  if (token && !authService.isTokenExpired()) {
    // User is still logged in
    setAuthenticated(true);
  }
}, []);
```

## Security Best Practices

1. **Never store tokens in cookies** if your API is on a different domain (CORS issues)
2. **Use HTTPS** in production to prevent token interception
3. **Clear tokens on logout** to prevent unauthorized access
4. **Implement token refresh** to minimize exposure of long-lived tokens
5. **Validate tokens on the backend** for every protected request
6. **Store company_id in Cognito** rather than locally to prevent tampering

## Testing Tips

```javascript
// Test registration flow
const testUser = {
  email: `test${Date.now()}@example.com`,
  password: 'TestPass123!',
  given_name: 'Test',
  family_name: 'User',
  timezone: 'America/New_York',
  company_id: 'test-company'
};

// Test the flow
await authService.register(testUser);
// Check email for code
await authService.confirmEmail(testUser.email, '123456');
await authService.login(testUser.email, testUser.password);
const user = await authService.getCurrentUser();
console.log('User data:', user);
```