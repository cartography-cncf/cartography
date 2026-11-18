import logging
import re
from collections.abc import Iterable
from collections.abc import Iterator
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentra import api
from cartography.models.sentra.data_store import SentraDataStoreSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# arn:<partition>:<service>:<region>:<account>:<resource>. S3 bucket ARNs leave the
# region and account empty.
_AWS_ARN_RE = re.compile(
    r"^arn:aws(?:-[a-z]+)*:(?P<service>[a-z0-9-]+):[a-z0-9-]*:\d*:(?P<resource>.+)$",
)
AWS_RESOURCE_ID_FIELDS = (
    "aws_s3_bucket_name",
    "aws_rds_instance_arn",
    "aws_rds_cluster_arn",
    "aws_dynamodb_table_arn",
    "aws_redshift_cluster_arn",
)


@timeit
def get(session: requests.Session, api_url: str) -> Iterator[list[dict[str, Any]]]:
    yield from api.iter_search_pages(session, api_url, api.DATA_STORES_SEARCH_PATH)


def aws_resource_ids(
    native_unique_id: str | None,
    account_type: str,
    hosting_service: str | None,
    name: str,
) -> dict[str, str | None]:
    """
    Return the ID of the AWS resource a Sentra data store is, keyed by resource type.

    Each ID is set only when its shape proves the resource type: an ARN names its
    service and resource type, and an S3 bucket name is globally unique. Every other
    field stays `None`, so the store never links to a resource of a different kind.
    """
    ids: dict[str, str | None] = dict.fromkeys(AWS_RESOURCE_ID_FIELDS)
    arn = _AWS_ARN_RE.match(native_unique_id) if native_unique_id else None
    if arn:
        service = arn["service"]
        resource = arn["resource"]
        if service == "s3" and "/" not in resource:
            ids["aws_s3_bucket_name"] = resource
        elif service == "rds" and resource.startswith("db:"):
            ids["aws_rds_instance_arn"] = native_unique_id
        elif service == "rds" and resource.startswith("cluster:"):
            ids["aws_rds_cluster_arn"] = native_unique_id
        elif service == "dynamodb" and re.fullmatch(r"table/[^/]+", resource):
            ids["aws_dynamodb_table_arn"] = native_unique_id
        elif service == "redshift" and resource.startswith("cluster:"):
            ids["aws_redshift_cluster_arn"] = native_unique_id
    elif account_type == "AWS" and (hosting_service or "").lower() == "s3":
        # Without an ARN, an S3 store is named after its bucket. Bucket names are
        # globally unique, so a bucket that matches the name is this store's bucket.
        ids["aws_s3_bucket_name"] = name
    return ids


def transform(raw_stores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for store in raw_stores:
        account_type = store["Connector__account_type"]
        result.append(
            {
                "id": store["id"],
                "name": store["name"],
                "description": store.get("description"),
                "native_unique_id": store.get("native_unique_id"),
                "category": store.get("category"),
                "hosting_service": store.get("hosting_service"),
                "database_engine": store.get("database_engine"),
                "database_engine_version": store.get("database_engine_version"),
                "region": store.get("region"),
                "storage_account": store.get("storage_account"),
                "connector_id": store["connector_id"],
                "connector_name": store["Connector__name"],
                "connector_account_id": store["Connector__account_id"],
                "connector_account_type": account_type,
                "connector_environment": store.get("Connector__environment"),
                "sensitivity_level": store["sensitivity_level"],
                "sensitivity_score": store.get("sensitivity_score"),
                "public_access_level": store.get("public_access_level"),
                "is_encrypted": store.get("is_encrypted"),
                "is_encrypted_in_transit": store.get("is_encrypted_in_transit"),
                "encryption_method": store.get("encryption_method"),
                "is_backed_up": store.get("is_backed_up"),
                "is_logging_enabled": store.get("is_logging_enabled"),
                "is_managed": store.get("is_managed"),
                "scan_status": store["scan_status"],
                "last_scan_status": store.get("last_scan_status"),
                "last_scanned": store.get("last_scanned"),
                "last_classified": store.get("last_classified"),
                "last_activity": store.get("last_activity"),
                "last_modified": store.get("last_modified"),
                "created_at": store.get("created_at"),
                "used_storage": store.get("used_storage"),
                "findings_count": store.get("findings_count"),
                "alerts_count": store.get("alerts_count"),
                "data_class_ids": [
                    data_class["id"] for data_class in store.get("data_classes") or []
                ],
                **aws_resource_ids(
                    store.get("native_unique_id"),
                    account_type,
                    store.get("hosting_service"),
                    store["name"],
                ),
            },
        )
    return result


@timeit
def load_data_stores(
    neo4j_session: neo4j.Session,
    data: Iterable[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SentraDataStoreSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SentraDataStoreSchema(), common_job_parameters).run(
        neo4j_session,
    )


def _record_aws_ids(
    stores: Iterable[dict[str, Any]],
    aws_ids_by_store: dict[str, dict[str, str]],
) -> Iterator[dict[str, Any]]:
    """
    Yield each transformed store unchanged, and record its AWS resource IDs.

    Recording the IDs while the loader streams the stores keeps only the small ID
    map in memory, not every store.
    """
    for store in stores:
        aws_ids = {
            field: store[field] for field in AWS_RESOURCE_ID_FIELDS if store[field]
        }
        if aws_ids:
            aws_ids_by_store[store["id"]] = aws_ids
        yield store


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    api_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> dict[str, dict[str, str]]:
    """
    Sync data stores and return the AWS resource IDs of each one, keyed by store ID.

    Alerts use the IDs to link to the AWS resources that they affect. A store that
    represents no AWS resource is left out.
    """
    logger.info("Syncing Sentra data stores for organization %s", tenant_id)
    aws_ids_by_store: dict[str, dict[str, str]] = {}
    data_stores = _record_aws_ids(
        (store for page in get(session, api_url) for store in transform(page)),
        aws_ids_by_store,
    )
    load_data_stores(neo4j_session, data_stores, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return aws_ids_by_store
