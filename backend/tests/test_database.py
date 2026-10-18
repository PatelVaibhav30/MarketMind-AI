from sqlalchemy import create_engine, text

from app.core.config import settings


def test_database_connection():
    engine = create_engine(settings.test_database_url)

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        assert result.scalar() == 1

    engine.dispose()