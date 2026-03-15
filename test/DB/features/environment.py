# test/DB/features/environment.py
import sys
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TEST_DIR))

from test_utils.db.db_client import DBClient


def before_all(context):
    context.db = DBClient()


def before_scenario(context, scenario):
    context.total_inventory_count = None
    context.expected_total_inventory_count = None
    context.location_counts = {}


def after_scenario(context, scenario):
    try:
        context.db.rollback()
    except Exception:
        pass


def after_all(context):
    context.db.close()