import sys
from pathlib import Path

# add project root to Python path
TEST_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TEST_DIR))

from test_utils.api.api_client import ApiClient

def before_all(context):
    context.api_client = ApiClient()


def before_scenario(context, scenario):
    context.response = None
    context.payload = None
    context.token = None