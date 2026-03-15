GET_INVENTORY_BY_VIN = """
        SELECT vin_number, make, model, year, mileage, condition_type, cost, sale_price,
       profit_percent, status, location
       FROM inventory
       WHERE vin_number = %s;
"""
# test/DB/queries/inventory_queries.py

COUNT_ALL_INVENTORY = """
                      SELECT COUNT(*) AS count
                      FROM inventory \
                      """

COUNT_INVENTORY_BY_LOCATION = """
                              SELECT COUNT(*) AS count
                              FROM inventory
                              WHERE location = %s \
                              """

GET_INVENTORY_BY_DETAILS = """
                           SELECT *
                           FROM inventory
                           WHERE make = %s
                                     AND model = %s
                                     AND year = %s
                             AND location = %s
                               LIMIT 1 \
                           """