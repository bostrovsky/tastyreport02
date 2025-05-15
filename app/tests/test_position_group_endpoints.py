import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.tests.utils import create_test_account, create_test_transaction

@pytest.mark.asyncio
async def test_position_group_crud_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create a test account
        account_id = await create_test_account(ac, headers=None)
        # Create two test transactions
        tx1 = await create_test_transaction(ac, headers=None, account_id=account_id)
        tx2 = await create_test_transaction(ac, headers=None, account_id=account_id)
        tx_ids = [tx1["id"], tx2["id"]]

        # List position groups (should be empty)
        resp = await ac.get(f"{settings.API_V1_STR}/position-groups")
        assert resp.status_code == 200
        assert resp.json() == []

        # Create a position group
        resp = await ac.post(f"{settings.API_V1_STR}/position-groups", json={
            "account_id": account_id,
            "name": "Test Group",
            "transaction_ids": tx_ids
        })
        assert resp.status_code == 201
        group = resp.json()
        group_id = group["id"]
        assert set(group["transaction_ids"]) == set(tx_ids)

        # Update the position group (change name, remove one transaction)
        resp = await ac.patch(f"{settings.API_V1_STR}/position-groups/{group_id}", json={
            "name": "Updated Group",
            "transaction_ids": [tx1["id"]]
        })
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["name"] == "Updated Group"
        assert updated["transaction_ids"] == [tx1["id"]]

        # Delete the position group
        resp = await ac.delete(f"{settings.API_V1_STR}/position-groups/{group_id}")
        assert resp.status_code == 204

        # List again (should be empty)
        resp = await ac.get(f"{settings.API_V1_STR}/position-groups")
        assert resp.status_code == 200
        assert resp.json() == []
