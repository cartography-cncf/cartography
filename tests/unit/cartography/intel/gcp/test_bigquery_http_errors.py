import json
from types import ModuleType
from typing import Any
from typing import Callable
from unittest.mock import MagicMock

import pytest
from googleapiclient.errors import HttpError

from cartography.intel.gcp import bigquery_connection
from cartography.intel.gcp import bigquery_dataset
from cartography.intel.gcp import bigquery_routine
from cartography.intel.gcp import bigquery_table
from cartography.intel.gcp.bigquery_connection import get_bigquery_connections
from cartography.intel.gcp.bigquery_dataset import get_bigquery_dataset_detail
from cartography.intel.gcp.bigquery_dataset import get_bigquery_datasets
from cartography.intel.gcp.bigquery_routine import get_bigquery_routines
from cartography.intel.gcp.bigquery_table import get_bigquery_table_detail
from cartography.intel.gcp.bigquery_table import get_bigquery_tables


def _make_http_error(status: int = 403, reason: str | None = None) -> HttpError:
    resp = MagicMock()
    resp.status = status
    payload: dict = {"error": {"code": status}}
    if reason:
        payload["error"]["errors"] = [{"reason": reason}]
    return HttpError(resp=resp, content=json.dumps(payload).encode("utf-8"))


BIGQUERY_HANDLER_CASES: list[
    tuple[ModuleType, Callable[..., Any], tuple[str, ...], list[Any] | None]
] = [
    (bigquery_dataset, get_bigquery_datasets, ("test-project",), None),
    (
        bigquery_dataset,
        get_bigquery_dataset_detail,
        ("test-project", "dataset-1"),
        None,
    ),
    (bigquery_table, get_bigquery_tables, ("test-project", "dataset-1"), None),
    (
        bigquery_table,
        get_bigquery_table_detail,
        ("test-project", "dataset-1", "table-1"),
        None,
    ),
    (bigquery_routine, get_bigquery_routines, ("test-project", "dataset-1"), None),
    (bigquery_connection, get_bigquery_connections, ("test-project",), []),
]


@pytest.mark.parametrize("module,func,args,expected", BIGQUERY_HANDLER_CASES)
@pytest.mark.parametrize(
    "reason",
    [
        "BILLING_DISABLED",
        "rateLimitExceeded",
    ],
)
def test_bigquery_handlers_skip_legacy_403_errors(
    monkeypatch,
    module,
    func,
    args,
    expected,
    reason,
):
    client = MagicMock()
    error = _make_http_error(403, reason)

    monkeypatch.setattr(
        module,
        "gcp_api_execute_with_retry",
        lambda _request: (_ for _ in ()).throw(error),
    )

    assert func(client, *args) == expected


# These three return the parent object regardless of the detail/list call's own
# outcome (table/dataset stays loaded either way), or their cleanup is gated behind
# the same success check as the call itself, so skipping on an "invalid" 400 can't
# cause previously-synced data to be wiped out.
BIGQUERY_INVALID_400_TOLERANT_CASES: list[
    tuple[ModuleType, Callable[..., Any], tuple[str, ...], list[Any] | None]
] = [
    (bigquery_dataset, get_bigquery_datasets, ("test-project",), None),
    (
        bigquery_dataset,
        get_bigquery_dataset_detail,
        ("test-project", "dataset-1"),
        None,
    ),
    (
        bigquery_table,
        get_bigquery_table_detail,
        ("test-project", "dataset-1", "table-1"),
        None,
    ),
]

# These three feed a cleanup job that runs unconditionally and is scoped only to
# PROJECT_ID (not per-dataset/location), so they must keep raising on an "invalid"
# 400 instead of skipping - otherwise one bad dataset/location would make cleanup
# delete tables/routines/connections that are still valid in sibling datasets.
BIGQUERY_INVALID_400_RAISING_CASES: list[
    tuple[ModuleType, Callable[..., Any], tuple[str, ...]]
] = [
    (bigquery_table, get_bigquery_tables, ("test-project", "dataset-1")),
    (bigquery_routine, get_bigquery_routines, ("test-project", "dataset-1")),
    (bigquery_connection, get_bigquery_connections, ("test-project",)),
]


@pytest.mark.parametrize(
    "module,func,args,expected",
    BIGQUERY_INVALID_400_TOLERANT_CASES,
)
def test_bigquery_handlers_skip_invalid_400_errors(
    monkeypatch,
    module,
    func,
    args,
    expected,
):
    client = MagicMock()
    error = _make_http_error(400, "invalidQuery")

    monkeypatch.setattr(
        module,
        "gcp_api_execute_with_retry",
        lambda _request: (_ for _ in ()).throw(error),
    )

    assert func(client, *args) == expected


@pytest.mark.parametrize("module,func,args", BIGQUERY_INVALID_400_RAISING_CASES)
def test_bigquery_list_handlers_reraise_invalid_400_errors(
    monkeypatch,
    module,
    func,
    args,
):
    client = MagicMock()
    error = _make_http_error(400, "invalidQuery")

    monkeypatch.setattr(
        module,
        "gcp_api_execute_with_retry",
        lambda _request: (_ for _ in ()).throw(error),
    )

    with pytest.raises(HttpError):
        func(client, *args)


def test_bigquery_handlers_reraise_non_403_transient(monkeypatch):
    client = MagicMock()
    error = _make_http_error(503, "backendError")

    monkeypatch.setattr(
        bigquery_dataset,
        "gcp_api_execute_with_retry",
        lambda _request: (_ for _ in ()).throw(error),
    )

    with pytest.raises(HttpError):
        get_bigquery_datasets(client, "test-project")
