from behave import given, when, then
from DB.queries.sales_queries import GET_SALE_BY_VIN
from DB.queries.inventory_queries import GET_INVENTORY_BY_VIN
from test_utils.db.db_assertions import assert_record_not_exists
from test_utils.db.db_seed_helper import insert_sales_record, delete_inventory_by_vin, delete_sales_by_vin

@given('a sold sale record exists for VIN "{vin}"')
def step_sale_exists(context, vin):
    delete_sales_by_vin(context.db, vin)
    delete_inventory_by_vin(context.db, vin)
    insert_sales_record(context.db, "102120251", vin, 16000, "Cash", 0, None, None, None, "Sold")

@when('I query the inventory table by VIN "{vin}"')
def step_query_inventory(context, vin):
    context.record = context.db.fetch_one(GET_INVENTORY_BY_VIN, (vin,))

@then("the inventory record should not exist")
def step_inventory_should_not_exist(context):
    assert_record_not_exists(context.record, "inventory record")
