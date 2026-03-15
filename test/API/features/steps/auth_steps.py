from behave import given, when, then
from fixtures.payloads import valid_login_payload


@given("a valid login payload")
def step_valid_login_payload(context):
    context.payload = valid_login_payload()


@when('I send a POST request to "{path}"')
def step_send_post(context, path):
    context.response = context.api_client.post(path, json=context.payload)


@then("the response status should be {status_code:d}")
def step_check_status(context, status_code):
    assert context.response.status_code == status_code, (
        f"Expected {status_code}, got {context.response.status_code}. "
        f"Body: {context.response.text}"
    )


@then("the response should contain an access token")
def step_check_access_token(context):
    body = context.response.json()
    assert "access_token" in body, f"No access_token in response: {body}"
    assert body["access_token"], "access_token is empty"