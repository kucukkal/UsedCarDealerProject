import os
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Resolve backend .env path
ENV_PATH = Path(__file__).resolve().parents[2] / "app" / "backend" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

def valid_create_user_payload():
    unique_suffix = uuid.uuid4().hex[:8]
    return {
        "username": f"buyer_{unique_suffix}",
        "password": "Buyer123!",
        "role": "BuyerRep",
        "location": "Rockville"
    }

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


def valid_login_payload():
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")

    if not username or not password:
        raise RuntimeError(
            f"ADMIN_USERNAME or ADMIN_PASSWORD is missing. Checked env file: {ENV_PATH}"
        )

    return {
        "username": username,
        "password": password
    }


def invalid_pr_discount_payload():
    return {
        "vin_number": "1020251",
        "discount_percent": 15,
        "location": "Fairfax"
    }