Feature: User Management API

  Scenario: Admin creates a new user successfully
    Given an admin login payload
    When I log in as admin
    Given a valid new user payload
    When I send a POST request to "/auth/create-user" with admin authorization
    Then the response status should be 200
    And the response should contain the created username
    And the response should contain the created role
    And the response should contain the created location