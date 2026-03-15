Feature: Authentication API

  Scenario: Successful login returns JWT token
    Given a valid login payload
    When I send a POST request to "/auth/login"
    Then the response status should be 200
    And the response should contain an access token