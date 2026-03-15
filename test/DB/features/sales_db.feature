@skip
Feature: Sales and inventory database consistency

  Scenario: Sold car is removed from inventory
    Given a sold sale record exists for VIN "1020251"
    When I query the inventory table by VIN "1020251"
    Then the inventory record should not exist
