from collections.abc import Generator
from unittest.mock import Mock, patch

import pytest

from top_assist.utils.cypher import Cypher


@pytest.fixture(autouse=True)
def _auto_mock_cypher() -> Generator:
    def encrypt(raw_data: str) -> str:
        return f"fake_encrypted_{raw_data}"

    def decrypt(encrypted_data: str) -> str:
        assert encrypted_data.startswith("fake_encrypted_")
        return encrypted_data.removeprefix("fake_encrypted_")

    fake_cypher = Mock(
        Cypher,
        encrypt=Mock(Cypher.encrypt, side_effect=encrypt),
        decrypt=Mock(Cypher.decrypt, side_effect=decrypt),
    )
    with (
        patch("top_assist.auth.provider._cypher", new=fake_cypher),
        patch("top_assist.auth.sign_in_flow._cypher", new=fake_cypher),
        patch("top_assist.auth._sign_in_context._cypher", new=fake_cypher),
    ):
        yield
