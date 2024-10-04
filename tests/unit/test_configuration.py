import os
from importlib import reload

from top_assist import configuration


def test_confluence_ignore_labels() -> None:
    env_key = "CONFLUENCE_IGNORE_LABELS"
    original_value = os.environ.get(env_key)

    try:
        os.environ[env_key] = "top-assist-ignore"
        reload(configuration)
        assert configuration.confluence_ignore_labels == ['"top-assist-ignore"']

        os.environ[env_key] = ""
        reload(configuration)
        assert configuration.confluence_ignore_labels == []

        del os.environ[env_key]
        reload(configuration)
        assert configuration.confluence_ignore_labels == ['"top-assist-ignore"']

        os.environ[env_key] = "top-assist-ignore,archived"
        reload(configuration)
        assert configuration.confluence_ignore_labels == ['"top-assist-ignore"', '"archived"']

    finally:
        if original_value is None:
            del os.environ[env_key]
        else:
            os.environ[env_key] = original_value


def test_configuration_methods() -> None:
    env_key = "TOP_ASSIST_ADMIN_EXTRA_LINKS"
    original_value = os.environ.get(env_key)

    try:
        os.environ[env_key] = '[{ "name": "Docs", "url": "/docs"}, { "name": "ReDocs", "url": "/redocs"}]'
        reload(configuration)
        assert configuration.admin_extra_links == [
            {"name": "Docs", "url": "/docs"},
            {"name": "ReDocs", "url": "/redocs"},
        ]

        os.environ[env_key] = ""
        reload(configuration)
        assert configuration.admin_extra_links == []

    finally:
        if original_value is None:
            del os.environ[env_key]
        else:
            os.environ[env_key] = original_value
