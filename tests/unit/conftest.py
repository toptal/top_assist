import os
import typing

import pook
import pytest


@pytest.fixture(autouse=True)
def _disable_external_sockets() -> typing.Generator:
    pook.on()

    try:
        yield
    finally:
        pook.off()


def pytest_sessionstart() -> None:
    os.environ["WEAVIATE_CLIENT_SKIP_INIT_CHECKS"] = "true"
