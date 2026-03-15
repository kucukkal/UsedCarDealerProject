def assert_status(response, expected_status):
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}. "
        f"Response body: {response.text}"
    )


def assert_error_message(response, expected_message):
    body = response.json()
    actual_message = body.get("detail") or body.get("message") or str(body)
    assert expected_message in actual_message, (
        f"Expected error message containing '{expected_message}', got '{actual_message}'"
    )