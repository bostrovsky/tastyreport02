import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings

@pytest.mark.asyncio
async def test_strategy_crud_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # List strategies (should include defaults)
        resp = await ac.get(f"{settings.API_V1_STR}/strategies/")
        assert resp.status_code == 200
        strategies = resp.json()
        default_names = {s["name"] for s in strategies if s["is_default"]}
        assert "Naked Put" in default_names

        # Create a custom strategy
        resp = await ac.post(f"{settings.API_V1_STR}/strategies/", json={"name": "Test Custom", "description": "My custom strat"})
        assert resp.status_code == 201
        custom = resp.json()
        assert custom["name"] == "Test Custom"
        custom_id = custom["id"]

        # Update the custom strategy
        resp = await ac.patch(f"{settings.API_V1_STR}/strategies/{custom_id}/", json={"description": "Updated desc"})
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated desc"

        # Delete the custom strategy
        resp = await ac.delete(f"{settings.API_V1_STR}/strategies/{custom_id}/")
        assert resp.status_code == 204

        # Try to update a default strategy (should fail)
        default_id = next(s["id"] for s in strategies if s["is_default"])
        resp = await ac.patch(f"{settings.API_V1_STR}/strategies/{default_id}/", json={"description": "Should fail"})
        assert resp.status_code == 404 or resp.status_code == 403

        # Try to delete a default strategy (should fail)
        resp = await ac.delete(f"{settings.API_V1_STR}/strategies/{default_id}/")
        assert resp.status_code == 404 or resp.status_code == 403
