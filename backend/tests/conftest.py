import os
import sys
from pathlib import Path
import pytest

# Add backend folder to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Use test database before app is imported
os.environ["DB_NAME"] = "time_tracker_test"

from app import app


@pytest.fixture(scope="module")
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client