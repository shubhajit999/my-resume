import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Create dedicated test engine connected ONLY to TEST_DATABASE_URL
connect_args = {"check_same_thread": False} if settings.TEST_DATABASE_URL.startswith("sqlite") else {}

# Strict assertion to guarantee test engine does not point to development database
assert "resumeforge_dev.db" not in settings.TEST_DATABASE_URL, "TEST_DATABASE_URL must not point to development database!"
assert "resumeforge_test.db" in settings.TEST_DATABASE_URL, "TEST_DATABASE_URL must point to resumeforge_test.db!"

test_engine = create_engine(
    settings.TEST_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_database():
    """
    Autouse fixture managing isolated test database tables on TEST_DATABASE_URL (resumeforge_test.db) only.
    Guarantees development database (resumeforge_dev.db) is NEVER modified or dropped during test runs.
    """
    assert "resumeforge_dev.db" not in str(test_engine.url), "Safety Check Failed: test_engine is pointing to resumeforge_dev.db!"
    assert "resumeforge_test.db" in str(test_engine.url), "Safety Check Failed: test_engine is not pointing to resumeforge_test.db!"

    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
