from behave import given, when, then
from fixtures.payloads import valid_login_payload, invalid_pr_discount_payload


@given("I am authenticated")
def step_authenticated(context):
    login_response = context.api_client.post("/auth/login", json=valid_login_payload())
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"

    body = login_response.json()
    context.token = body["access_token"]
    context.api_client.set_token(context.token)


@given("an invalid promotion discount payload over 10 percent")
def step_invalid_discount_payload(context):
    context.payload = invalid_pr_discount_payload()


@when('I send an authenticated POST request to "{path}"')
def step_authenticated_post(context, path):
    context.response = context.api_client.post(path, json=context.payload)


@then('the error message should contain "{message}"')
def step_error_message(context, message):
    body = context.response.json()
    actual_message = body.get("detail") or body.get("message") or str(body)
    assert message in actual_message, f"Expected '{message}', got '{actual_message}'"