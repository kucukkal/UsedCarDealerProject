# test/DB/features/steps/inventory_count_steps.py
from behave import given, when, then

from DB.queries.inventory_queries import (
    COUNT_ALL_INVENTORY,
    COUNT_INVENTORY_BY_LOCATION,
    GET_INVENTORY_BY_DETAILS,
)
from test_utils.db.db_assertions import (
    assert_count_equals,
    assert_record_exists,
)


@given('total inventory records is "{expected_total}"')
def step_total_inventory_records(context, expected_total):
    context.total_inventory_count = context.db.fetch_value(COUNT_ALL_INVENTORY)
    context.expected_total_inventory_count = int(expected_total)


@when('there are "{expected_count}" inventory records with location "{location}"')
def step_inventory_count_by_location(context, expected_count, location):
    if not hasattr(context, "location_counts"):
        context.location_counts = {}

    actual_count = context.db.fetch_value(COUNT_INVENTORY_BY_LOCATION, (location,))
    context.location_counts[location] = {
        "expected": int(expected_count),
        "actual": actual_count,
    }


@then('inventory record exists with the following details:')
def step_inventory_records_should_exist(context):
    # First validate total inventory count
    assert_count_equals(
        context.total_inventory_count,
        context.expected_total_inventory_count,
        "total inventory count",
    )

    # Then validate each location count
    for location, counts in context.location_counts.items():
        assert_count_equals(
            counts["actual"],
            counts["expected"],
            f'inventory count for location "{location}"',
        )

    # Then validate specific records from the Gherkin table
    for row in context.table:
        make = row["make"]
        model = row["model"]
        year = int(row["year"])
        location = row["location"]

        record = context.db.fetch_one(
            GET_INVENTORY_BY_DETAILS,
            (make, model, year, location),
        )

        assert_record_exists(
            record,
            f'inventory record ({make}, {model}, {year}, {location})',
        )