from fixtures.payloads import invalid_pr_discount_payload
from test_utils.api.response_validator import assert_status, assert_error_message


def test_pr_discount_more_than_10_percent_is_rejected(api_client, auth_token):
    api_client.set_token(auth_token)
    payload = invalid_pr_discount_payload()

    response = api_client.post("/promotion/discount", json=payload)

    assert_status(response, 400)
    assert_error_message(response, "The discount amount is more than %10")