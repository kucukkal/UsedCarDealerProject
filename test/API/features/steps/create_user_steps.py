from behave import given, when, then
from fixtures.payloads import valid_login_payload, valid_create_user_payload


@given("an admin login payload")
def step_admin_login_payload(context):
    context.payload = valid_login_payload()


@when("I log in as admin")
def step_login_as_admin(context):
    response = context.api_client.post("/auth/login", json=context.payload)
    context.response = response

    assert response.status_code == 200, (
        f"Admin login failed. "
        f"Expected 200, got {response.status_code}. "
        f"Body: {response.text}"
    )

    body = response.json()
    token = body.get("access_token")
    assert token, f"No access_token found in login response: {body}"

    context.token = token


@given("a valid new user payload")
def step_valid_new_user_payload(context):
    context.payload = valid_create_user_payload()


@when('I send a POST request to "{path}" with admin authorization')
def step_post_with_admin_auth(context, path):
    headers = {
        "Authorization": f"Bearer {context.token}"
    }
    context.response = context.api_client.post(path, json=context.payload, headers=headers)


# @then("the response status should be 200")
# def step_check_status_200(context):
#     assert context.response.status_code == 200, (
#         f"Expected 200, got {context.response.status_code}. "
#         f"Body: {context.response.text}"
#     )


@then("the response should contain the created username")
def step_check_created_username(context):
    body = context.response.json()
    assert body["username"] == context.payload["username"], (
        f"Expected username '{context.payload['username']}', got '{body.get('username')}'. "
        f"Body: {body}"
    )


@then("the response should contain the created role")
def step_check_created_role(context):
    body = context.response.json()
    assert body["role"] == context.payload["role"], (
        f"Expected role '{context.payload['role']}', got '{body.get('role')}'. "
        f"Body: {body}"
    )


@then("the response should contain the created location")
def step_check_created_location(context):
    body = context.response.json()
    assert body["location"] == context.payload["location"], (
        f"Expected location '{context.payload['location']}', got '{body.get('location')}'. "
        f"Body: {body}"
    )