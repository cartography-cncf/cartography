from cartography.intel.databricks.util import parse_storage_url


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
