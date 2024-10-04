import os
import typing
from unittest.mock import patch

import pook
import pytest


@pytest.fixture(autouse=True)
def _disable_external_sockets() -> typing.Generator:
    pook.on()
    pook.enable_network("localhost")

    try:
        yield
    finally:
        pook.off()


@pytest.fixture()
def db_session() -> typing.Generator:
    from top_assist.database.database import Session, engine

    connection = engine.connect()
    transaction = connection.begin()

    session = Session(bind=connection)

    with patch("top_assist.database.database.SessionLocal", return_value=session):
        try:
            yield session
        finally:
            session.rollback()
            connection.close()
            transaction.rollback()


def pytest_sessionstart() -> None:
    os.environ["WEAVIATE_CLIENT_SKIP_INIT_CHECKS"] = "true"

    if os.environ.get("ENV") == "development":
        os.environ["DB_NAME"] += "_test"
        os.environ["VECTOR_COLLECTIONS_PREFIX"] += "_test"
