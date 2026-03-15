Feature: Admin user actions
in
  Scenario: Admin user logins
    Given User navigates to Login page
    When User enters "admin" credentials
    And User is at Home page
    Then User logs out

  @admin
  Scenario: Admin uploads a file to add cars to the inventory
    Given User navigates to Login page
    When User enters "admin" credentials
    And User is at Home page
    And I click the "Inventory" link
    And I upload the inventory Excel file "Japanese_German_Used_Car_Inventory.xlsx"
    Then I should see "4" cars for location "Rockville"
    And I should see "1" cars for location "Charlotte"