Feature: Inventory database validation

  Scenario: Inventory record exists with expected location after insertion
    Given total inventory records is "5"
    When there are "4" inventory records with location "Rockville"
    And  there are "1" inventory records with location "Charlotte"
    Then inventory record exists with the following details:
      | make     | model   | year | location  |
      | Audi     | Q5      | 2006 | Rockville |
      | Mercedes | GLK 450 | 2025 | Charlotte |

