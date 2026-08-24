"""Raw Snowflake stage payloads, as the per-schema listing returns them."""

from typing import Any

# The buckets and storage account the external stages point at. The integration tests
# seed these as AWS / GCP / Azure nodes so the BACKED_BY edges have something to
# resolve against, the way they would in a real graph where the aws, gcp and azure
# modules ran first.
SNOWFLAKE_STAGE_S3_BUCKET = "springfield-reactor-logs"
SNOWFLAKE_STAGE_GCS_BUCKET = "springfield-donut-archive"
SNOWFLAKE_STAGE_AZURE_STORAGE_ACCOUNT = "springfieldkwikemart"

SNOWFLAKE_STAGES: list[dict[str, Any]] = [
    {
        "name": "REACTOR_LOG_STAGE",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "kind": "PERMANENT",
        "url": f"s3://{SNOWFLAKE_STAGE_S3_BUCKET}/telemetry/",
        "endpoint": None,
        "storage_integration": "PLANT_S3_INTEGRATION",
        "cloud": "AWS",
        "region": "us-east-2",
        "has_credentials": False,
        "has_encryption_key": False,
        "directory_table": True,
        "owner": "SYSADMIN",
        "owner_role_type": "ROLE",
        "comment": "Reactor telemetry drop",
        "created_on": "2026-08-03T16:40:00.000+00:00",
    },
    # An internal stage: no url, so it is Snowflake-managed file storage rather than a
    # handle on a customer bucket.
    {
        "name": "SCRATCH_STAGE",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "kind": "TEMPORARY",
        "url": "",
        "endpoint": None,
        "storage_integration": None,
        "cloud": None,
        "region": None,
        "has_credentials": False,
        "has_encryption_key": False,
        "directory_table": False,
        "owner": "HOMER",
        "owner_role_type": "ROLE",
        "comment": None,
        "created_on": "2026-08-03T16:41:00.000+00:00",
    },
    # An external stage with embedded credentials instead of a storage integration:
    # a long-lived cloud secret sitting in the stage definition.
    {
        "name": "DONUT_ARCHIVE_STAGE",
        "database_name": "SPRINGFIELD",
        "schema_name": "KWIK_E_MART",
        "kind": "PERMANENT",
        "url": f"gcs://{SNOWFLAKE_STAGE_GCS_BUCKET}/donuts/",
        "endpoint": None,
        "storage_integration": None,
        "cloud": "GCP",
        "region": "us-central1",
        "has_credentials": True,
        "has_encryption_key": True,
        "directory_table": False,
        "owner": "SHOPKEEPER",
        "owner_role_type": "ROLE",
        "comment": None,
        "created_on": "2026-08-03T16:42:00.000+00:00",
    },
    {
        "name": "SQUISHEE_BLOB_STAGE",
        "database_name": "MONORAIL",
        "schema_name": "PUBLIC",
        "kind": "PERMANENT",
        "url": (
            f"azure://{SNOWFLAKE_STAGE_AZURE_STORAGE_ACCOUNT}"
            ".blob.core.windows.net/squishee/sales/"
        ),
        "endpoint": None,
        "storage_integration": None,
        "cloud": "AZURE",
        "region": "westus2",
        "has_credentials": False,
        "has_encryption_key": False,
        "directory_table": False,
        "owner": "PLANT_ENGINEER",
        "owner_role_type": "ROLE",
        "comment": None,
        "created_on": "2026-08-03T16:43:00.000+00:00",
    },
]
