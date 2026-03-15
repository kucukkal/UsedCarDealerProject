import pytest
from test_utils.api.api_client import ApiClient
from fixtures.payloads import valid_login_payload


@pytest.fixture(scope="session")
def api_client():
    return ApiClient()


@pytest.fixture(scope="session")
def auth_token(api_client):
    payload = valid_login_payload()
    response = api_client.post("/auth/login", json=payload)

    assert response.status_code == 200, f"Login failed: {response.text}"

    body = response.json()
    token = body.get("access_token")
    assert token, f"No access_token found in response: {body}"
    return token