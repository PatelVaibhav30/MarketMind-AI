import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.main import app


@pytest.fixture
def db_session():
    engine = create_engine(settings.test_database_url)

    with Session(engine) as session:
        yield session

    engine.dispose()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clean_test_database():
    engine = create_engine(settings.test_database_url)

    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE TABLE stocks RESTART IDENTITY CASCADE")
        )

    engine.dispose()

    yield