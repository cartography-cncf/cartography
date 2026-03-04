import logging

from cartography.intel.pagination import DEFAULT_MAX_PAGINATION_ITEMS
from cartography.intel.pagination import DEFAULT_MAX_PAGINATION_PAGES
from cartography.intel.pagination import ENV_MAX_PAGINATION_ITEMS
from cartography.intel.pagination import ENV_MAX_PAGINATION_PAGES
from cartography.intel.pagination import get_pagination_limits


def test_get_pagination_limits_defaults(monkeypatch) -> None:
    monkeypatch.delenv(ENV_MAX_PAGINATION_PAGES, raising=False)
    monkeypatch.delenv(ENV_MAX_PAGINATION_ITEMS, raising=False)

    pages, items = get_pagination_limits()

    assert pages == DEFAULT_MAX_PAGINATION_PAGES
    assert items == DEFAULT_MAX_PAGINATION_ITEMS


def test_get_pagination_limits_valid_env(monkeypatch) -> None:
    monkeypatch.setenv(ENV_MAX_PAGINATION_PAGES, "123")
    monkeypatch.setenv(ENV_MAX_PAGINATION_ITEMS, "456")

    pages, items = get_pagination_limits()

    assert pages == 123
    assert items == 456


def test_get_pagination_limits_empty_env(monkeypatch) -> None:
    monkeypatch.setenv(ENV_MAX_PAGINATION_PAGES, "")
    monkeypatch.setenv(ENV_MAX_PAGINATION_ITEMS, "")

    pages, items = get_pagination_limits()

    assert pages == DEFAULT_MAX_PAGINATION_PAGES
    assert items == DEFAULT_MAX_PAGINATION_ITEMS


def test_get_pagination_limits_invalid_env(monkeypatch, caplog) -> None:
    monkeypatch.setenv(ENV_MAX_PAGINATION_PAGES, "not-a-number")
    monkeypatch.setenv(ENV_MAX_PAGINATION_ITEMS, "-5")

    with caplog.at_level(logging.WARNING):
        pages, items = get_pagination_limits(logging.getLogger("test"))

    assert pages == DEFAULT_MAX_PAGINATION_PAGES
    assert items == DEFAULT_MAX_PAGINATION_ITEMS
    assert f"Invalid {ENV_MAX_PAGINATION_PAGES}" in caplog.text
    assert f"Non-positive {ENV_MAX_PAGINATION_ITEMS}" in caplog.text
