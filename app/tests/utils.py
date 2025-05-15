import uuid
import random
import string

# Generate a unique email for each test run

def unique_email(prefix: str = "test") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"

# Create a test TastyTrade account via the API
async def create_test_account(ac, headers) -> str:
    resp = await ac.post(
        "/api/v1/tastytrade-accounts",
        json={
            "broker": "tastytrade",
            "account_number": "ACCT" + ''.join(random.choices(string.digits, k=6)),
            "nickname": "Test Account",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]

# Create a test TastyTrade transaction via the API
async def create_test_transaction(ac, headers, account_id) -> dict:
    resp = await ac.post(
        "/api/v1/tastytrade-transactions",
        json={
            "account_id": account_id,
            "symbol": "AAPL",
            "quantity": 1,
            "price": 100.0,
            "side": "buy",
            "date": "2024-01-01T00:00:00Z",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
