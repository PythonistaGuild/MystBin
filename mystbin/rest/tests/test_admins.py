

# requires:
# pytest
# pytest-asyncio
# httpx


import pytest
try:
    from common import client
except ModuleNotFoundError:
    from utils.common import client

@pytest.mark.asyncio
async def test_root():
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Tomato"}