Feature: Admin user actions
in
  Scenario: Admin user logins
    Given User navigates to Login page
    When User enters "admin" credentials
    And User is at Home page
    Then User logs out

  @admin1
  Scenario: Network routing
    Given User navigates to Login page
    When User enters "admin" credentials
    And User is at Home page
    And I click the "Inventory" link
#    And I used the following values to reroute the api call
#      | make       | model     | sub_model | year | mileage | vehicle_type | color   | antique | condition_type | cost  | sale_price | location  |
#      | Toyota     | Camry     | SE        | 2019 | 42000   | Sedan        | White   | No      | Good           | 12000 | 16500      | Rockville |
    And I enter the values using the following values
      | make       | model     | sub_model | year | mileage | vehicle_type | color   | antique | condition_type | cost  | sale_price | location  |
      | BMW        | Z4        | SE        | 2009 | 24000   | Sedan        |Red      | No      | Good           | 14500 | 19500      | Charlotte |
#    And I reroute the inventory API call with my saved payload
    And I mock the inventory API call with the values above
    Then I submit the vehicle form


  @admin
  Scenario: Admin uploads a file to add cars to the inventory
    Given User navigates to Login page
    When User enters "admin" credentials
    And User is at Home page
    And I click the "Inventory" link
    And I upload the inventory Excel file "Japanese_German_Used_Car_Inventory.xlsx"
    Then I should see "4" cars for location "Rockville"
    And I should see "1" cars for location "Charlotte"