def assert_record_not_exists(record, entity_name="record"):
    assert record is None, f"Expected {entity_name} not to exist, but found: {record}"

def assert_field_value(record, field_name, expected_value):
    actual_value = record.get(field_name)
    assert str(actual_value) == str(expected_value), (
        f"Expected field '{field_name}' to be '{expected_value}', but got '{actual_value}'."
    )
# test/test_utils/db/db_assertions.py

def assert_record_exists(record, record_name="record"):
    assert record is not None, f"Expected {record_name} to exist, but no record was found."


def assert_count_equals(actual_count, expected_count, label="count"):
    assert int(actual_count) == int(expected_count), (
        f"Expected {label} to be {expected_count}, but got {actual_count}."
    )