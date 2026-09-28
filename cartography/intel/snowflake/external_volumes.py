"""Snowflake external volumes and their storage locations.

An external volume is one object with a list of storage locations, and it is the
locations that carry the cloud coordinates: the bucket, the IAM role Snowflake
assumes and the KMS key. They are therefore emitted as separate child nodes so each
one can point at the concrete S3 / GCS / Azure resource and IAM role it uses.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import parse_stage_url
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.external_volume import SnowflakeExternalVolumeSchema
from cartography.models.snowflake.external_volume import (
    SnowflakeExternalVolumeStorageLocationSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]]:
    return client.list_all("/api/v2/external-volumes")


def transform(
    volumes: list[dict[str, Any]],
    account_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return ``(volumes, storage locations)``.

    The storage locations are flattened out of each volume's ``storage_locations``
    list into their own records, keyed on volume name plus location name.
    """
    transformed_volumes: list[dict[str, Any]] = []
    transformed_locations: list[dict[str, Any]] = []

    for volume in volumes:
        volume_name = volume["name"]
        volume_id = sf_id(account_id, "external_volume", sf_fqn(volume_name))
        storage_locations = volume.get("storage_locations") or []
        transformed_volumes.append(
            {
                "id": volume_id,
                "name": volume_name,
                "allow_writes": volume.get("allow_writes"),
                "storage_location_count": len(storage_locations),
                "owner": volume.get("owner"),
                "owner_role_type": volume.get("owner_role_type"),
                "comment": volume.get("comment"),
                "created_on": iso_to_datetime(volume.get("created_on")),
            },
        )

        for location in storage_locations:
            location_name = location["name"]
            base_url = location.get("storage_base_url") or None
            scheme, container = parse_stage_url(base_url)
            encryption = location.get("encryption") or {}
            transformed_locations.append(
                {
                    "id": sf_id(
                        account_id,
                        "external_volume_storage_location",
                        sf_fqn(volume_name, location_name),
                    ),
                    "name": location_name,
                    "volume_name": volume_name,
                    "parent_volume_id": volume_id,
                    "storage_provider": location.get("storage_provider"),
                    "storage_base_url": base_url,
                    "storage_aws_role_arn": location.get("storage_aws_role_arn"),
                    "storage_aws_iam_user_arn": location.get(
                        "storage_aws_iam_user_arn"
                    ),
                    "storage_aws_external_id": location.get("storage_aws_external_id"),
                    "azure_tenant_id": location.get("azure_tenant_id"),
                    "encryption_type": encryption.get("type"),
                    "kms_key_id": encryption.get("kms_key_id"),
                    "s3_bucket": container if scheme in ("s3", "s3gov") else None,
                    "gcs_bucket": container if scheme == "gcs" else None,
                    "azure_storage_account": (
                        container if scheme in ("azure", "azures") else None
                    ),
                },
            )

    return transformed_volumes, transformed_locations


def load_external_volumes(
    neo4j_session: neo4j.Session,
    volumes: list[dict[str, Any]],
    storage_locations: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeExternalVolumeSchema(),
        volumes,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )
    load(
        neo4j_session,
        SnowflakeExternalVolumeStorageLocationSchema(),
        storage_locations,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeExternalVolumeStorageLocationSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        SnowflakeExternalVolumeSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake external volumes and their cloud storage locations."""
    volumes, storage_locations = transform(get(client), client.account_id)
    logger.info(
        "Loading %d Snowflake external volumes and %d storage locations for "
        "account %s.",
        len(volumes),
        len(storage_locations),
        client.account_id,
    )
    load_external_volumes(
        neo4j_session,
        volumes,
        storage_locations,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return True
