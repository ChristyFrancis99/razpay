from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_openapi_is_public():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Risk Intelligence Platform API"


def test_demo_endpoint_bypasses_auth_middleware_in_development():
    response = client.post("/api/auth/demo")
    # CI does not provide DEFAULT_ADMIN_PASSWORD, so 503 is expected there.
    # A 401 would mean the authentication middleware blocked the bootstrap route.
    assert response.status_code != 401
