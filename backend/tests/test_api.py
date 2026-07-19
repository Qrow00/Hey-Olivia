import pytest


@pytest.mark.anyio
async def test_root(client):
    r = await client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "J.A.R.V.I.S."
    assert data["status"] == "online"
    assert data["api_version"] == "v1"


@pytest.mark.anyio
async def test_api_root(client):
    r = await client.get("/api/v1")
    assert r.status_code == 200
    data = r.json()
    assert data["version"] == "v1"
    assert "devices" in data["endpoints"]
    assert "vision" in data["endpoints"]


@pytest.mark.anyio
async def test_get_devices(client):
    r = await client.get("/api/v1/devices")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.anyio
async def test_get_creameras(client):
    r = await client.get("/api/v1/cameras")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.anyio
async def test_get_wearables(client):
    r = await client.get("/api/v1/wearables")
    assert r.status_code == 200


@pytest.mark.anyio
async def test_get_smart_home(client):
    r = await client.get("/api/v1/smart-home")
    assert r.status_code == 200


@pytest.mark.anyio
async def test_get_commands(client):
    r = await client.get("/api/v1/commands")
    assert r.status_code == 200


@pytest.mark.anyio
async def test_get_plugins(client):
    r = await client.get("/api/v1/plugins")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.anyio
async def test_get_plugin_capabilities(client):
    r = await client.get("/api/v1/plugins/capabilities")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)
