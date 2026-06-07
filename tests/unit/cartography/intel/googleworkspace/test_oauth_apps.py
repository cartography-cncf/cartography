import logging
from unittest.mock import MagicMock

from googleapiclient.errors import HttpError

from cartography.intel.googleworkspace.oauth_apps import get_oauth_tokens_for_user


def _make_http_error(status: int) -> HttpError:
    resp = MagicMock()
    resp.status = status
    resp.reason = "Unauthorized"
    return HttpError(resp=resp, content=b'{"error": "unauthorized"}')


def test_get_oauth_tokens_for_user_skips_401(caplog):
    admin = MagicMock()
    admin.tokens.return_value.list.return_value.execute.side_effect = _make_http_error(
        401
    )

    with caplog.at_level(
        logging.DEBUG, logger="cartography.intel.googleworkspace.oauth_apps"
    ):
        result = get_oauth_tokens_for_user(admin, "suspended-user")

    assert result == []
    warning_records = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert warning_records == []
    debug_messages = [
        r.getMessage() for r in caplog.records if r.levelno == logging.DEBUG
    ]
    assert any("suspended-user" in m and "401" in m for m in debug_messages)


def test_get_oauth_tokens_for_user_returns_empty_on_404():
    admin = MagicMock()
    admin.tokens.return_value.list.return_value.execute.side_effect = _make_http_error(
        404
    )

    assert get_oauth_tokens_for_user(admin, "no-tokens-user") == []
