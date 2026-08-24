"""Raw Snowflake external volume payloads, as `GET /api/v2/external-volumes` returns them."""

from typing import Any

# The cloud resources the storage locations point at, seeded by the integration test so
# the BACKED_BY, ENCRYPTED_BY and ASSUMES_ROLE edges have something to resolve against.
SNOWFLAKE_VOLUME_S3_BUCKET = "springfield-iceberg"
SNOWFLAKE_VOLUME_GCS_BUCKET = "springfield-iceberg-gcs"
SNOWFLAKE_VOLUME_ROLE_ARN = "arn:aws:iam::000000000000:role/SnowflakeIcebergRole"
SNOWFLAKE_VOLUME_KMS_KEY_ARN = (
    "arn:aws:kms:us-east-2:000000000000:key/11111111-2222-3333-4444-555555555555"
)

SNOWFLAKE_EXTERNAL_VOLUMES: list[dict[str, Any]] = [
    {
        "name": "MONORAIL_VOLUME",
        "allow_writes": True,
        "owner": "SYSADMIN",
        "owner_role_type": "ROLE",
        "created_on": "2026-08-03T16:50:00.000+00:00",
        "comment": "Iceberg storage for monorail telemetry",
        "storage_locations": [
            {
                "name": "PRIMARY_S3",
                "storage_provider": "S3",
                "storage_base_url": f"s3://{SNOWFLAKE_VOLUME_S3_BUCKET}/iceberg/",
                "storage_aws_role_arn": SNOWFLAKE_VOLUME_ROLE_ARN,
                "storage_aws_external_id": "SPRINGFIELD_NUCLEAR_SFCRole=2_abcdef==",
                "storage_aws_iam_user_arn": (
                    "arn:aws:iam::999999999999:user/snowflake-iceberg"
                ),
                "azure_tenant_id": None,
                "encryption": {
                    "type": "AWS_SSE_KMS",
                    "kms_key_id": SNOWFLAKE_VOLUME_KMS_KEY_ARN,
                },
            },
            # A second location on another cloud, unencrypted by a customer key.
            {
                "name": "SECONDARY_GCS",
                "storage_provider": "GCS",
                "storage_base_url": f"gcs://{SNOWFLAKE_VOLUME_GCS_BUCKET}/iceberg/",
                "storage_aws_role_arn": None,
                "storage_aws_external_id": None,
                "storage_aws_iam_user_arn": None,
                "azure_tenant_id": None,
                "encryption": {"type": "NONE", "kms_key_id": None},
            },
        ],
    },
    # A read-only volume with no storage locations reported: the volume exists but the
    # role cannot see where it points.
    {
        "name": "DUFF_VOLUME",
        "allow_writes": False,
        "owner": "HOMER",
        "owner_role_type": "ROLE",
        "created_on": "2026-08-03T16:52:00.000+00:00",
        "comment": None,
        "storage_locations": [],
    },
]
