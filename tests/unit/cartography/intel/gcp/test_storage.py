import json
import logging
from unittest.mock import MagicMock

import pytest
from googleapiclient.errors import HttpError

import cartography.intel.gcp.storage
from tests.data.gcp.storage import STORAGE_RESPONSE


def test_transform_gcp_buckets():
    buckets, labels = cartography.intel.gcp.storage.transform_gcp_buckets_and_labels(
        STORAGE_RESPONSE
    )

    # Test buckets
    assert len(buckets) == 1
    bucket = buckets[0]
    assert bucket["project_number"] == 123456789012
    assert bucket["id"] == "bucket_name"
    assert bucket["self_link"] == "https://www.googleapis.com/storage/v1/b/bucket_name"
    assert bucket["retention_period"] is None
    assert bucket["iam_config_bucket_policy_only"] is False
    assert bucket["location"] == "US"
    assert bucket["location_type"] == "multi-region"
    assert bucket["storage_class"] == "STANDARD"
    # `allUsers` reader in `acl` -> ACL-based public exposure
    assert bucket["acl_public"] is True

    # Test labels
    assert len(labels) == 2
    label_keys = [label["key"] for label in labels]
    label_values = [label["value"] for label in labels]
    assert "label_key_1" in label_keys
    assert "label_key_2" in label_keys
    assert "label_value_1" in label_values
    assert "label_value_2" in label_values

    # Check that all labels have the correct bucket_id
    for label in labels:
        assert label["bucket_id"] == "bucket_name"
        assert label["id"].startswith("GCPBucket_")


def test_get_gcp_buckets_permission_denied_logs_concisely(monkeypatch, caplog):
    storage = MagicMock()
    request = MagicMock()
    storage.buckets.return_value.list.return_value = request

    resp = MagicMock()
    resp.status = 403
    error = HttpError(
        resp=resp,
        content=json.dumps(
            {
                "error": {
                    "message": "User lacks storage.buckets.list permission",
                    "errors": [{"reason": "insufficientPermissions"}],
                }
            }
        ).encode("utf-8"),
    )

    monkeypatch.setattr(
        "cartography.intel.gcp.storage.gcp_api_execute_with_retry",
        lambda _request: (_ for _ in ()).throw(error),
    )

    with caplog.at_level(logging.WARNING):
        buckets = cartography.intel.gcp.storage.get_gcp_buckets(storage, "test-project")

    assert buckets == {}
    assert "HTTP 403 insufficientPermissions" in caplog.text
    assert "googleapiclient.errors.HttpError" not in caplog.text


def test_get_gcp_buckets_reraises_generic_403(monkeypatch):
    storage = MagicMock()
    request = MagicMock()
    storage.buckets.return_value.list.return_value = request

    resp = MagicMock()
    resp.status = 403
    error = HttpError(
        resp=resp,
        content=json.dumps({"error": {"message": "Forbidden"}}).encode("utf-8"),
    )

    monkeypatch.setattr(
        "cartography.intel.gcp.storage.gcp_api_execute_with_retry",
        lambda _request: (_ for _ in ()).throw(error),
    )

    with pytest.raises(HttpError):
        cartography.intel.gcp.storage.get_gcp_buckets(storage, "test-project")


def test_get_gcp_buckets_paginates_through_next_page_token(monkeypatch):
    """`projection=full` caps `buckets.list` responses at 200 items, so we must
    follow `nextPageToken`. Without pagination, anything beyond the first page
    would be dropped and cleanup would prune valid buckets.
    """
    storage = MagicMock()
    page1_req = MagicMock(name="page1_req")
    page2_req = MagicMock(name="page2_req")
    storage.buckets.return_value.list.return_value = page1_req
    # Two responses: first carries `nextPageToken`, second closes the iterator.
    page1 = {
        "kind": "storage#buckets",
        "items": [{"id": "bucket-1"}, {"id": "bucket-2"}],
        "nextPageToken": "tok",
    }
    page2 = {"kind": "storage#buckets", "items": [{"id": "bucket-3"}]}

    storage.buckets.return_value.list_next.side_effect = [page2_req, None]

    execute_calls = []

    def fake_execute(request):
        execute_calls.append(request)
        return page1 if request is page1_req else page2

    monkeypatch.setattr(
        "cartography.intel.gcp.storage.gcp_api_execute_with_retry",
        fake_execute,
    )

    result = cartography.intel.gcp.storage.get_gcp_buckets(storage, "test-project")

    assert [b["id"] for b in result["items"]] == ["bucket-1", "bucket-2", "bucket-3"]
    # `nextPageToken` must not leak into the aggregated result.
    assert "nextPageToken" not in result
    # Both pages must actually have been fetched.
    assert execute_calls == [page1_req, page2_req]
