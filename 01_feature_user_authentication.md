# Feature 1: User Authentication

**Feature Goal:**
To provide a secure mechanism for users to register (if applicable, though likely admin-created for initial MVP), log in, and log out of the application. User sessions must be managed effectively, and protected routes should only be accessible to authenticated users. The system must be designed with scalability and security in mind to support hundreds to thousands of users reliably.

**API Relationships:**

*   **Backend API Endpoints (FastAPI - `/api/v1/auth/`):**
    *   `POST /login`:
        *   Request Body Schema: `OAuth2PasswordRequestForm` (FastAPI utility for `username` and `password`). Username will be email.
        *   Response Schema: `TokenSchema` (e.g., `access_token`, `refresh_token`, `token_type`).
    *   `POST /logout`: (Optional, if server-side session invalidation is implemented for refresh tokens, or if a denylist is used for JWTs).
        *   Request: Requires authenticated user (access token).
        *   Response: Success/failure message.
    *   `POST /refresh-token`:
        *   Request Body Schema: `RefreshTokenSchema` (e.g., `refresh_token`).
        *   Response Schema: `TokenSchema` (new `access_token`, potentially new `refresh_token`).
    *   `GET /me`: (To verify token and get current user info, useful for frontend to confirm auth state).
        *   Request: Requires authenticated user (access token).
        *   Response Schema: `UserReadSchema` (e.g., `id`, `email`, `role`).

**Detailed Feature Requirements:**

1.  **User Login:**
    *   Users must be able to log in using their registered email and password.
    *   Upon successful login, the backend should issue an access token and a refresh token (JWTs).
    *   Incorrect login attempts should result in a generic error message (to avoid user enumeration).
    *   Implement robust protection against brute-force attacks (e.g., rate limiting on login attempts per IP and per user, account lockout after multiple failed attempts).
2.  **User Logout:**
    *   Users must be able to log out.
    *   Client-side: Access and refresh tokens should be cleared from storage.
    *   Server-side (Recommended for refresh tokens): Implement a mechanism to invalidate refresh tokens (e.g., denylist, or tracking active refresh tokens per user and removing on logout).
3.  **Session Management & Token Handling:**
    *   **Access Tokens:** Short-lived JWTs (e.g., 15-60 minutes) used to authenticate API requests to protected routes. Should contain necessary claims like `user_id`, `role`, `exp`.
    *   **Refresh Tokens:** Longer-lived JWTs (e.g., 7-30 days) used to obtain new access tokens without requiring the user to re-enter credentials. Refresh tokens should be stored securely (e.g., HttpOnly, Secure, SameSite=Strict cookie for web clients).
    *   The system must handle token expiration and renewal gracefully. If an access token expires, the client should use the refresh token to get a new one. If the refresh token expires or is invalid, the user must re-authenticate.
    *   Consider refresh token rotation for enhanced security (issuing a new refresh token along with a new access token).
4.  **Password Security:**
    *   Passwords must be securely hashed using a strong, modern algorithm (e.g., Argon2id or bcrypt with a sufficient cost factor) before being stored in the database. Plaintext passwords must never be stored.
    *   Enforce strong password policies (minimum length, complexity including uppercase, lowercase, numbers, special characters).
5.  **Protected Routes:**
    *   All application features beyond login (e.g., dashboard, data sync, reports) must be protected and require a valid access token with appropriate permissions/roles if role-based access control (RBAC) is implemented.
    *   Unauthorized access attempts should result in a 401 Unauthorized error. Forbidden access (valid token, insufficient permissions) should result in a 403 Forbidden error.
6.  **User Data & Roles:**
    *   Basic user information (ID, email, hashed password, role (e.g., 'user', 'admin'), `is_active`, `created_at`, `last_login_at`) should be stored in the database.
    *   For initial MVP, user creation might be handled by an administrator. Self-registration can be a future enhancement.
7.  **Security Best Practices:**
    *   Use HTTPS for all communication.
    *   Protect against common web vulnerabilities (XSS, CSRF - especially if using cookies for tokens, SQLi - ORM helps but validate inputs).
    *   Regularly update dependencies to patch known vulnerabilities.
    *   Implement comprehensive logging for security events (logins, failed logins, token issuance).
8.  **Testing:**
    *   Unit tests for authentication logic, token generation/validation, password hashing.
    *   Integration tests for login/logout/refresh flows and protected route access.

**Detailed Implementation Guide:**

*   **Backend (FastAPI):**
    1.  **Core Security (`app/core/security.py`):**
        *   Functions for password hashing and verification (e.g., `get_password_hash`, `verify_password` using `passlib`).
        *   Functions for creating access tokens and refresh tokens (JWTs using `python-jose`), including setting expiration times and necessary claims.
        *   Functions to decode and validate JWTs, checking signature, expiration, and potentially issuer/audience.
        *   Configuration for `SECRET_KEY` (strong, random), `REFRESH_SECRET_KEY` (if different), `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` in `app/core/config.py` (loaded from environment variables).
    2.  **Database Models (`app/db/models/user.py`):**
        *   `User` model: `id` (UUID preferred), `email` (unique, indexed), `hashed_password` (string), `role` (string, e.g., Enum), `is_active` (boolean, default True), `created_at`, `updated_at`, `last_login_at` (nullable).
    3.  **CRUD Operations (`app/crud/crud_user.py`):**
        *   `get_user_by_email(db: Session, email: str) -> Optional[User]`.
        *   `create_user(db: Session, user_in: UserCreateSchema) -> User` (for admin creation or future self-registration).
        *   `update_user_last_login(db: Session, user: User) -> User`.
    4.  **Schemas (`app/schemas/user.py`, `app/schemas/token.py`):**
        *   `UserCreateSchema` (email, password, role), `UserUpdateSchema`.
        *   `UserReadSchema` (id, email, role, is_active).
        *   `TokenSchema` (access_token, refresh_token, token_type).
        *   `TokenPayloadSchema` (for JWT payload, e.g., `sub` (user_id or email), `exp`, `iat`, `role`).
        *   `RefreshTokenSchema` (for refresh token request body).
    5.  **API Endpoints (`app/api/v1/endpoints/auth.py`):**
        *   Implement login endpoint using `OAuth2PasswordBearer` and `OAuth2PasswordRequestForm`. Authenticate user, generate tokens. Set refresh token in an HttpOnly cookie if applicable.
        *   Implement refresh token endpoint: validate refresh token (from HttpOnly cookie or request body), issue new tokens.
        *   Implement `/me` endpoint using a dependency to get the current user from the access token.
        *   Implement logout endpoint: if using a denylist, add current access token (JTI claim) and/or refresh token to it. Clear HttpOnly cookie for refresh token.
    6.  **Dependencies (`app/api/v1/deps.py`):**
        *   `get_current_active_user`: Dependency that verifies the JWT in the `Authorization` header (or from cookie if preferred for access token in some setups), checks if the user is active, and returns the authenticated user model.
    7.  **Rate Limiting & Security Headers:**
        *   Use a library like `slowapi` for rate limiting.
        *   Implement security headers (e.g., `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`) via middleware.
*   **Frontend (Next.js):**
    1.  **Authentication Context/Store (`src/contexts/AuthContext.tsx` or Zustand/Redux store):**
        *   Manage authentication state (current user object, loading status, error messages).
        *   Provide functions for login, logout, and potentially handling token refresh implicitly.
        *   Store access token in memory. Refresh token would ideally be handled by the browser via HttpOnly cookie set by the backend.
    2.  **API Service Calls (`src/services/authService.ts`):**
        *   Functions to call backend auth endpoints (`loginUser(email, password)`, `logoutUser()`, `refreshToken()`, `fetchCurrentUser()`).
        *   Use an HTTP client (e.g., Axios) configured with `withCredentials: true` if using HttpOnly cookies for refresh tokens.
    3.  **Login Page/Component (`src/app/(auth)/login/page.tsx`):**
        *   Secure login form (email, password) with proper input validation.
        *   Call login function from AuthContext/service.
        *   Handle loading states and display appropriate error messages.
        *   Redirect to the dashboard or intended page upon successful login.
    4.  **Route Protection/Guards:**
        *   Use Next.js middleware or client-side checks in layouts/pages to protect routes that require authentication. Redirect unauthenticated users to the login page.
        *   The `fetchCurrentUser` call on app load can establish initial auth state.
    5.  **Token Interceptor for API Client (e.g., Axios):**
        *   Automatically add the access token (from memory/AuthContext) to `Authorization` header of outgoing requests to protected backend endpoints.
        *   Implement logic to handle 401 errors: if a refresh token mechanism is managed client-side (less ideal than HttpOnly cookie), attempt to call the refresh token endpoint, update the access token, and retry the original request. If HttpOnly cookies are used for refresh, the browser handles sending it, and the backend handles refresh transparently or the client gets a 401 to trigger re-login.

**Testing Considerations:**

*   **Backend:**
    *   Test password hashing and verification with known vectors.
    *   Test JWT generation with correct claims and expiration.
    *   Test JWT validation (valid, invalid, expired tokens).
    *   Test login endpoint with valid/invalid credentials, and against locked accounts.
    *   Test refresh token endpoint with valid/invalid/expired refresh tokens.
    *   Test `/me` endpoint with valid/invalid tokens.
    *   Test rate limiting on login.
*   **Frontend:**
    *   Test login form submission and error handling.
    *   Test successful login and redirection.
    *   Test logout functionality.
    *   Test protected route access (authenticated vs. unauthenticated).
    *   Test automatic token refresh flow if applicable client-side.

This comprehensive approach to user authentication will provide a secure and scalable foundation for the application.

