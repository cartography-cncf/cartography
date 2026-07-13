from datetime import timezone

from cartography.intel.databricks.util import iso_to_datetime
from cartography.intel.databricks.util import parse_storage_url


def test_iso_to_datetime():
    # Trailing Z (RFC-3339) and explicit offsets both parse to aware datetimes.
    dt = iso_to_datetime("2026-07-01T23:27:40Z")
    assert dt is not None
    assert dt.tzinfo is not None
    assert dt.astimezone(timezone.utc).hour == 23
    # Fractional seconds (Lakeview) parse too.
    assert iso_to_datetime("2026-07-01T23:29:14.783Z") is not None
    # Empty / missing values are dropped.
    assert iso_to_datetime(None) is None
    assert iso_to_datetime("") is None


def test_parse_storage_url():
    assert parse_storage_url("s3://my-bucket/uc/path") == ("s3", "my-bucket")
    assert parse_storage_url("gs://my-bucket/path") == ("gs", "my-bucket")
    assert parse_storage_url("abfss://container@acct.dfs.core.windows.net/path") == (
        "abfss",
        "container",
    )
    assert parse_storage_url(None) == (None, None)
    assert parse_storage_url("") == (None, None)
    assert parse_storage_url("not-a-url") == (None, None)
