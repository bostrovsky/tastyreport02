import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
import uuid
import os
from dotenv import load_dotenv
from unittest.mock import patch
from app.api.v1.endpoints import tastytrade as tastytrade_module

# Helper to generate unique emails/usernames

def unique_email(prefix="user"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"

def unique_username(prefix="user"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

@pytest.mark.asyncio
async def test_tastytrade_account_crud():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        email = unique_email("tastytest")
        username = unique_username("tastyuser")
        # Register user
        resp = await ac.post("/api/v1/auth/register-user", json={
            "email": email,
            "password": "TestPassword123!",
            "role": "user"
        })
        assert resp.status_code == 201, resp.text
        # Login
        resp = await ac.post("/api/v1/auth/login", json={
            "email": email,
            "password": "TestPassword123!"
        })
        assert resp.status_code == 200, resp.text
        tokens = resp.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Create TastyTrade account
        resp = await ac.post("/api/v1/tastytrade/accounts/", json={
            "tasty_username": username,
            "tasty_password": "test_tasty_pass"
        }, headers=headers)
        assert resp.status_code == 201, resp.text
        account = resp.json()
        assert account["tasty_username"] == username
        account_id = account["id"]

        # List TastyTrade accounts
        resp = await ac.get("/api/v1/tastytrade/accounts/", headers=headers)
        assert resp.status_code == 200, resp.text
        accounts = resp.json()
        assert len(accounts) == 1
        assert accounts[0]["id"] == account_id

        # Sync TastyTrade account (should fail with 401 or 500 due to fake credentials)
        resp = await ac.post(f"/api/v1/tastytrade/accounts/sync/{account_id}", headers=headers)
        assert resp.status_code in (401, 500)

        # Try to retrieve balances (should be empty or error due to failed sync)
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/balances", headers=headers)
        assert resp.status_code == 200, resp.text
        balances = resp.json()
        assert isinstance(balances, list)

        # Try to retrieve positions (should be empty or error due to failed sync)
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/positions", headers=headers)
        assert resp.status_code == 200, resp.text
        positions = resp.json()
        assert isinstance(positions, list)

        # Try to retrieve transactions (should be empty or error due to failed sync)
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/transactions", headers=headers)
        assert resp.status_code == 200, resp.text
        transactions = resp.json()
        assert isinstance(transactions, list)

        # Delete TastyTrade account
        resp = await ac.delete(f"/api/v1/tastytrade/accounts/{account_id}", headers=headers)
        assert resp.status_code == 204

        # List again, should be empty
        resp = await ac.get("/api/v1/tastytrade/accounts/", headers=headers)
        assert resp.status_code == 200
        accounts = resp.json()
        assert len(accounts) == 0

@pytest.mark.asyncio
async def test_tastytrade_pagination_and_permissions():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        email_a = unique_email("usera")
        email_b = unique_email("userb")
        username_a = unique_username("usera_tasty")
        # Register user A
        resp = await ac.post("/api/v1/auth/register-user", json={
            "email": email_a,
            "password": "PasswordA123!",
            "role": "user"
        })
        assert resp.status_code == 201
        resp = await ac.post("/api/v1/auth/login", json={
            "email": email_a,
            "password": "PasswordA123!"
        })
        tokens_a = resp.json()
        headers_a = {"Authorization": f"Bearer {tokens_a['access_token']}"}

        # Register user B
        resp = await ac.post("/api/v1/auth/register-user", json={
            "email": email_b,
            "password": "PasswordB123!",
            "role": "user"
        })
        assert resp.status_code == 201
        resp = await ac.post("/api/v1/auth/login", json={
            "email": email_b,
            "password": "PasswordB123!"
        })
        tokens_b = resp.json()
        headers_b = {"Authorization": f"Bearer {tokens_b['access_token']}"}

        # User A creates an account
        resp = await ac.post("/api/v1/tastytrade/accounts/", json={
            "tasty_username": username_a,
            "tasty_password": "fakepass"
        }, headers=headers_a)
        assert resp.status_code == 201
        account_id = resp.json()["id"]

        # User B cannot access User A's account data (403)
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/balances", headers=headers_b)
        assert resp.status_code == 403
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/positions", headers=headers_b)
        assert resp.status_code == 403
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/transactions", headers=headers_b)
        assert resp.status_code == 403

        # User A: test pagination and X-Total-Count header
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/balances?limit=1&offset=0", headers=headers_a)
        assert resp.status_code == 200
        assert "X-Total-Count" in resp.headers
        assert isinstance(resp.json(), list)

        # 404 for non-existent account
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{fake_id}/balances", headers=headers_a)
        assert resp.status_code == 404

        # 401 for missing auth
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/balances")
        assert resp.status_code == 401

        # 400 for invalid params
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/balances?limit=-1", headers=headers_a)
        assert resp.status_code == 422  # FastAPI returns 422 for validation errors

        # Clean up
        await ac.delete(f"/api/v1/tastytrade/accounts/{account_id}", headers=headers_a)

@pytest.mark.asyncio
async def test_tastytrade_real_sync_and_data():
    load_dotenv()
    tasty_username = os.getenv("TASTYTRADE_USERNAME")
    tasty_password = os.getenv("TASTY_PASSWORD")
    if not tasty_username or not tasty_password:
        pytest.skip("TastyTrade credentials not set in .env")
    print("DEBUG: TASTYTRADE_USERNAME=", tasty_username)
    print("DEBUG: TASTY_PASSWORD=", tasty_password)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        email = unique_email("realuser")
        # Register user
        resp = await ac.post("/api/v1/auth/register-user", json={
            "email": email,
            "password": "RealTestPassword123!",
            "role": "user"
        })
        assert resp.status_code == 201, resp.text
        # Login
        resp = await ac.post("/api/v1/auth/login", json={
            "email": email,
            "password": "RealTestPassword123!"
        })
        assert resp.status_code == 200, resp.text
        tokens = resp.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Add TastyTrade account
        resp = await ac.post("/api/v1/tastytrade/accounts/", json={
            "tasty_username": tasty_username,
            "tasty_password": tasty_password
        }, headers=headers)
        assert resp.status_code == 201, resp.text
        account_id = resp.json()["id"]

        # Sync
        resp = await ac.post(f"/api/v1/tastytrade/accounts/sync/{account_id}", headers=headers)
        assert resp.status_code == 202, resp.text

        # Retrieve balances
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/balances", headers=headers)
        assert resp.status_code == 200, resp.text
        balances = resp.json()

        # Retrieve positions
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/positions", headers=headers)
        assert resp.status_code == 200, resp.text
        positions = resp.json()

        # Retrieve transactions
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/transactions", headers=headers)
        assert resp.status_code == 200, resp.text
        transactions = resp.json()

        # At least one of the lists should be non-empty
        assert balances or positions or transactions, "No data returned from sync!"

        # Clean up
        await ac.delete(f"/api/v1/tastytrade/accounts/{account_id}", headers=headers)

# --- Edge Case: Empty Data ---
@pytest.mark.asyncio
async def test_tastytrade_empty_data():
    """Test sync and retrieval for an account with no positions or transactions."""
    load_dotenv()
    tasty_username = os.getenv("TASTYTRADE_EMPTY_USERNAME")
    tasty_password = os.getenv("TASTYTRADE_EMPTY_PASSWORD")
    if not tasty_username or not tasty_password:
        pytest.skip("TastyTrade empty account credentials not set in .env")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        email = unique_email("emptyuser")
        # Register user
        resp = await ac.post("/api/v1/auth/register-user", json={
            "email": email,
            "password": "EmptyTestPassword123!",
            "role": "user"
        })
        assert resp.status_code == 201, resp.text
        # Login
        resp = await ac.post("/api/v1/auth/login", json={
            "email": email,
            "password": "EmptyTestPassword123!"
        })
        tokens = resp.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        # Add TastyTrade account
        resp = await ac.post("/api/v1/tastytrade/accounts/", json={
            "tasty_username": tasty_username,
            "tasty_password": tasty_password
        }, headers=headers)
        assert resp.status_code == 201, resp.text
        account_id = resp.json()["id"]
        # Sync
        resp = await ac.post(f"/api/v1/tastytrade/accounts/sync/{account_id}", headers=headers)
        assert resp.status_code == 202, resp.text
        # Retrieve balances
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/balances", headers=headers)
        assert resp.status_code == 200, resp.text
        # Retrieve positions
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/positions", headers=headers)
        assert resp.status_code == 200, resp.text
        assert resp.json() == []
        # Retrieve transactions
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/transactions", headers=headers)
        assert resp.status_code == 200, resp.text
        assert resp.json() == []
        # Clean up
        await ac.delete(f"/api/v1/tastytrade/accounts/{account_id}", headers=headers)

# --- Edge Case: Pagination ---
@pytest.mark.asyncio
async def test_tastytrade_pagination():
    """Test pagination on balances, positions, and transactions endpoints."""
    load_dotenv()
    tasty_username = os.getenv("TASTYTRADE_USERNAME")
    tasty_password = os.getenv("TASTY_PASSWORD")
    if not tasty_username or not tasty_password:
        pytest.skip("TastyTrade credentials not set in .env")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        email = unique_email("paguser")
        # Register user
        resp = await ac.post("/api/v1/auth/register-user", json={
            "email": email,
            "password": "PagTestPassword123!",
            "role": "user"
        })
        assert resp.status_code == 201, resp.text
        # Login
        resp = await ac.post("/api/v1/auth/login", json={
            "email": email,
            "password": "PagTestPassword123!"
        })
        tokens = resp.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        # Add TastyTrade account
        resp = await ac.post("/api/v1/tastytrade/accounts/", json={
            "tasty_username": tasty_username,
            "tasty_password": tasty_password
        }, headers=headers)
        assert resp.status_code == 201, resp.text
        account_id = resp.json()["id"]
        # Sync
        resp = await ac.post(f"/api/v1/tastytrade/accounts/sync/{account_id}", headers=headers)
        assert resp.status_code == 202, resp.text
        # Retrieve positions with pagination
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/positions?limit=1&offset=0", headers=headers)
        assert resp.status_code == 200, resp.text
        positions = resp.json()
        assert isinstance(positions, list)
        # If more than one position, test offset
        if len(positions) > 0:
            resp2 = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/positions?limit=1&offset=1", headers=headers)
            assert resp2.status_code == 200, resp2.text
            positions2 = resp2.json()
            assert isinstance(positions2, list)
        # Clean up
        await ac.delete(f"/api/v1/tastytrade/accounts/{account_id}", headers=headers)

# --- Edge Case: Unusual Symbols ---
@pytest.mark.asyncio
async def test_tastytrade_unusual_symbols():
    """Test handling of positions/transactions with special characters in symbols."""
    # This would require mocking the TastyTrade API or using a test account with such data
    # Placeholder: pass for now
    pass

# --- Rate Limiting (Placeholder) ---
@pytest.mark.asyncio
async def test_tastytrade_rate_limiting():
    """Test rate limiting by rapidly calling sync or data endpoints."""
    # If not implemented, expect 200/202; if implemented, expect 429
    # Placeholder: pass for now
    pass

# --- Error Handling: Invalid Credentials ---
@pytest.mark.asyncio
async def test_tastytrade_invalid_credentials():
    """Test sync with invalid TastyTrade credentials returns 401 or 500."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        email = unique_email("badcreds")
        # Register user
        resp = await ac.post("/api/v1/auth/register-user", json={
            "email": email,
            "password": "BadCredsTestPassword123!",
            "role": "user"
        })
        assert resp.status_code == 201, resp.text
        # Login
        resp = await ac.post("/api/v1/auth/login", json={
            "email": email,
            "password": "BadCredsTestPassword123!"
        })
        tokens = resp.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        # Add TastyTrade account with fake credentials
        resp = await ac.post("/api/v1/tastytrade/accounts/", json={
            "tasty_username": "fakeuser",
            "tasty_password": "fakepassword"
        }, headers=headers)
        assert resp.status_code == 201, resp.text
        account_id = resp.json()["id"]
        # Sync (should fail)
        resp = await ac.post(f"/api/v1/tastytrade/accounts/sync/{account_id}", headers=headers)
        assert resp.status_code in (401, 500), resp.text
        # Clean up
        await ac.delete(f"/api/v1/tastytrade/accounts/{account_id}", headers=headers)

# --- Error Handling: Simulated Downtime ---
@pytest.mark.asyncio
async def test_tastytrade_api_downtime():
    """Test sync when TastyTrade API is unreachable (simulate network error)."""
    load_dotenv()
    tasty_username = os.getenv("TASTYTRADE_USERNAME")
    tasty_password = os.getenv("TASTY_PASSWORD")
    if not tasty_username or not tasty_password:
        pytest.skip("TastyTrade credentials not set in .env")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        email = unique_email("downtime")
        # Register user
        resp = await ac.post("/api/v1/auth/register-user", json={
            "email": email,
            "password": "DowntimeTestPassword123!",
            "role": "user"
        })
        assert resp.status_code == 201, resp.text
        # Login
        resp = await ac.post("/api/v1/auth/login", json={
            "email": email,
            "password": "DowntimeTestPassword123!"
        })
        tokens = resp.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        # Add TastyTrade account
        resp = await ac.post("/api/v1/tastytrade/accounts/", json={
            "tasty_username": tasty_username,
            "tasty_password": tasty_password
        }, headers=headers)
        assert resp.status_code == 201, resp.text
        account_id = resp.json()["id"]
        # Patch tastytrade.Session to raise an exception
        with patch.object(tastytrade_module.tastytrade, "Session", side_effect=Exception("Simulated downtime")):
            resp = await ac.post(f"/api/v1/tastytrade/accounts/sync/{account_id}", headers=headers)
            assert resp.status_code == 500, resp.text
        # Clean up
        await ac.delete(f"/api/v1/tastytrade/accounts/{account_id}", headers=headers)

# --- Security: Cross-User Access ---
@pytest.mark.asyncio
async def test_tastytrade_cross_user_access():
    """Test that one user cannot access another user's TastyTrade data (403)."""
    load_dotenv()
    tasty_username = os.getenv("TASTYTRADE_USERNAME")
    tasty_password = os.getenv("TASTY_PASSWORD")
    if not tasty_username or not tasty_password:
        pytest.skip("TastyTrade credentials not set in .env")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register user A
        email_a = unique_email("usera")
        resp = await ac.post("/api/v1/auth/register-user", json={
            "email": email_a,
            "password": "UserATestPassword123!",
            "role": "user"
        })
        assert resp.status_code == 201, resp.text
        resp = await ac.post("/api/v1/auth/login", json={
            "email": email_a,
            "password": "UserATestPassword123!"
        })
        tokens_a = resp.json()
        headers_a = {"Authorization": f"Bearer {tokens_a['access_token']}"}
        # Register user B
        email_b = unique_email("userb")
        resp = await ac.post("/api/v1/auth/register-user", json={
            "email": email_b,
            "password": "UserBTestPassword123!",
            "role": "user"
        })
        assert resp.status_code == 201, resp.text
        resp = await ac.post("/api/v1/auth/login", json={
            "email": email_b,
            "password": "UserBTestPassword123!"
        })
        tokens_b = resp.json()
        headers_b = {"Authorization": f"Bearer {tokens_b['access_token']}"}
        # User A creates an account
        resp = await ac.post("/api/v1/tastytrade/accounts/", json={
            "tasty_username": tasty_username,
            "tasty_password": tasty_password
        }, headers=headers_a)
        assert resp.status_code == 201, resp.text
        account_id = resp.json()["id"]
        # User B cannot access User A's account data (403)
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/balances", headers=headers_b)
        assert resp.status_code == 403
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/positions", headers=headers_b)
        assert resp.status_code == 403
        resp = await ac.get(f"/api/v1/tastytrade/accounts/{account_id}/transactions", headers=headers_b)
        assert resp.status_code == 403
        # Clean up
        await ac.delete(f"/api/v1/tastytrade/accounts/{account_id}", headers=headers_a)

# NOTE: Run each test individually to avoid event loop and DB state issues.
# Example: .venv/bin/python -m pytest app/tests/test_tastytrade_account.py -k "test_tastytrade_pagination" | cat
