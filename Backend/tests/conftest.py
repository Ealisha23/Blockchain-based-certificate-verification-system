import os
import pytest

# Dedicated test DB: BCV_ENV=test drops all tables on startup (only allowed
# when the database name contains "test").
os.environ.setdefault("BCV_MYSQL_USER", "BCV_test")
os.environ.setdefault("BCV_MYSQL_PWD", "BCV_test_pwd")
os.environ.setdefault("BCV_MYSQL_HOST", "localhost")
os.environ.setdefault("BCV_MYSQL_DB", "BCV_test_db")
os.environ["BCV_ENV"] = "test"
os.environ["BCV_TYPE_STORAGE"] = "db"
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("BCV_CONTRACT_ADDRESS", "0x5FbDB2315678afecb367f032d93F642f64180aa3")  # first Hardhat deploy


@pytest.fixture(scope="session")
def client():
    from app.api.v1.app import app
    app.config["TESTING"] = True
    return app.test_client()
