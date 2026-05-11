from __future__ import annotations

from sqlalchemy import create_engine, text

from app.config import settings


engine = create_engine(
    settings.sqlalchemy_database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "connect_timeout": 10,
        "read_timeout": 10,
        "write_timeout": 10,
    },
)


def check_database_connection() -> dict[str, str]:
    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT
                    DATABASE() AS database_name,
                    VERSION() AS server_version
                """
            )
        ).mappings().one()

    return {
        "status": "connected",
        "database_name": str(row["database_name"]),
        "server_version": str(row["server_version"]),
    }
