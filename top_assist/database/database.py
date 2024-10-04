import logging
import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, exc
from sqlalchemy.orm import Session, sessionmaker

from top_assist.configuration import DB_URL

engine = create_engine(DB_URL, pool_pre_ping=True)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)  # echo SQL queries


# Following two event listeners are needed to prevent sharing connections between processes
# See: https://docs.sqlalchemy.org/en/20/core/pooling.html#using-connection-pools-with-multiprocessing-or-os-fork
@event.listens_for(engine, "connect")
def connect(_dbapi_connection, connection_record) -> None:  # noqa: ANN001
    connection_record.info["pid"] = os.getpid()


@event.listens_for(engine, "checkout")
def checkout(_dbapi_connection, connection_record, connection_proxy) -> None:  # noqa: ANN001
    pid = os.getpid()
    if connection_record.info["pid"] != pid:
        connection_record.dbapi_connection = connection_proxy.dbapi_connection = None
        raise exc.DisconnectionError(
            "Connection record belongs to pid %s, "  # noqa: UP031
            "attempting to check out in pid %s" % (connection_record.info["pid"], pid)
        )


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        logging.critical("DB session error", exc_info=True)
        raise
    finally:
        session.close()
