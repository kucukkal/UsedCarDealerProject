from fixtures.payloads import valid_login_payload
from test_utils.api.response_validator import assert_status


def test_login_success_returns_jwt_token(api_client):
    payload = valid_login_payload()

    response = api_client.post("/auth/login", json=payload)

    assert_status(response, 200)

    body = response.json()
    assert "access_token" in body, f"Expected access_token in response, got: {body}"
    assert body["access_token"], "Expected non-empty access_token"