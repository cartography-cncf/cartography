from itertools import repeat
from unittest.mock import MagicMock

import pytest

import cartography.intel.cloudflare.accounts as accounts
from cartography.config import Config
from cartography.intel.cloudflare import start_cloudflare_ingestion
from tests.data.cloudflare.accounts import CLOUDFLARE_ACCOUNTS


def _page(records, total_count):
    # Mimic SyncV4PagePaginationArray: exposes .result and .result_info, and is
    # iterable. Iteration is unbounded (repeats the first item) to reproduce the
    # /accounts paginator hang - get() must NOT iterate it.
    objs = [MagicMock(to_dict=lambda r=r: r) for r in records]
    page = MagicMock()
    page.result = objs
    page.result_info = MagicMock(total_count=total_count)
    page.__iter__ = lambda self: repeat(objs[0])
    return page


def test_start_cloudflare_ingestion_requires_token():
    config = Config(neo4j_uri="bolt://localhost:7687")

    with pytest.raises(RuntimeError, match="Cloudflare import is not configured"):
        start_cloudflare_ingestion(None, config)


def test_get_accounts_reads_single_page_not_paginator() -> None:
    # Regression: the /accounts endpoint ignores `page` and echoes the same
    # non-empty page forever, and the SDK paginator stops only on an empty page
    # -> iterating it never terminates. get() must read a single page (at the
    # max page size) via .result. See cloudflare/cloudflare-python#2584.
    client = MagicMock()
    client.accounts.list.return_value = _page(
        CLOUDFLARE_ACCOUNTS, total_count=len(CLOUDFLARE_ACCOUNTS)
    )

    result = accounts.get(client)

    assert result == CLOUDFLARE_ACCOUNTS
    client.accounts.list.assert_called_once_with(
        per_page=accounts.MAX_ACCOUNTS_PER_PAGE
    )


def test_get_accounts_raises_when_accounts_exceed_one_page() -> None:
    # >MAX_ACCOUNTS_PER_PAGE accounts are unreachable via /accounts (page is
    # ignored, no cursor). get() must fail loudly rather than silently drop the
    # overflow.
    client = MagicMock()
    client.accounts.list.return_value = _page(
        CLOUDFLARE_ACCOUNTS, total_count=len(CLOUDFLARE_ACCOUNTS) + 60
    )

    with pytest.raises(RuntimeError, match="partial account set"):
        accounts.get(client)
