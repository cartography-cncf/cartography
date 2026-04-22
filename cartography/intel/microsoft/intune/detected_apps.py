import logging
from typing import Any
from typing import Mapping

import neo4j
from msgraph import GraphServiceClient

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.microsoft.intune.reports import export_report_rows
from cartography.intel.microsoft.intune.reports import ExportedReportRows
from cartography.models.microsoft.intune.detected_app import IntuneDetectedAppSchema
from cartography.models.microsoft.intune.detected_app import (
    IntuneManagedDeviceToDetectedAppMatchLink,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

APP_NODE_BATCH_SIZE = 100
APP_RELATIONSHIP_BATCH_SIZE = 500
APPINVAGGREGATE_REPORT_NAME = "AppInvAggregate"
APPINVRAWDATA_REPORT_NAME = "AppInvRawData"
APPINVAGGREGATE_COLUMNS = [
    "ApplicationKey",
    "ApplicationId",
    "ApplicationName",
    "ApplicationPublisher",
    "ApplicationVersion",
    "DeviceCount",
    "Platform",
]
APPINVRAWDATA_COLUMNS = [
    "ApplicationKey",
    "DeviceId",
]


async def get_detected_app_aggregate_rows(
    client: GraphServiceClient,
) -> ExportedReportRows:
    return await export_report_rows(
        client,
        APPINVAGGREGATE_REPORT_NAME,
        APPINVAGGREGATE_COLUMNS,
    )


async def get_detected_app_raw_rows(
    client: GraphServiceClient,
) -> ExportedReportRows:
    return await export_report_rows(
        client,
        APPINVRAWDATA_REPORT_NAME,
        APPINVRAWDATA_COLUMNS,
    )


def transform_detected_app(row: Mapping[str, str]) -> dict[str, Any]:
    return {
        "id": _get_required_value(row, "ApplicationKey", APPINVAGGREGATE_REPORT_NAME),
        "application_id": _get_optional_value(row, "ApplicationId"),
        "display_name": _get_optional_value(row, "ApplicationName"),
        "version": _get_optional_value(row, "ApplicationVersion"),
        "size_in_byte": None,
        "device_count": _parse_optional_int(row.get("DeviceCount")),
        "publisher": _get_optional_value(row, "ApplicationPublisher"),
        "platform": _get_optional_value(row, "Platform"),
    }


def transform_detected_app_relationship(row: Mapping[str, str]) -> dict[str, str]:
    return {
        "app_id": _get_required_value(row, "ApplicationKey", APPINVRAWDATA_REPORT_NAME),
        "device_id": _get_required_value(row, "DeviceId", APPINVRAWDATA_REPORT_NAME),
    }


@timeit
def load_detected_app_nodes(
    neo4j_session: neo4j.Session,
    apps: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        IntuneDetectedAppSchema(),
        apps,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def load_detected_app_relationships(
    neo4j_session: neo4j.Session,
    app_relationships: list[dict[str, str]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load_matchlinks(
        neo4j_session,
        IntuneManagedDeviceToDetectedAppMatchLink(),
        app_relationships,
        lastupdated=update_tag,
        _sub_resource_label="EntraTenant",
        _sub_resource_id=tenant_id,
    )


@timeit
def cleanup_detected_app_nodes(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        IntuneDetectedAppSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def cleanup_detected_app_relationships(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_matchlink(
        IntuneManagedDeviceToDetectedAppMatchLink(),
        "EntraTenant",
        common_job_parameters["TENANT_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)


@timeit
async def sync_detected_apps(
    neo4j_session: neo4j.Session,
    client: GraphServiceClient,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    aggregate_report = await get_detected_app_aggregate_rows(client)
    _validate_report_columns(
        aggregate_report.fieldnames,
        APPINVAGGREGATE_COLUMNS,
        APPINVAGGREGATE_REPORT_NAME,
    )

    app_nodes_batch: list[dict[str, Any]] = []
    app_count = 0
    for row in aggregate_report.rows:
        app_nodes_batch.append(transform_detected_app(row))
        app_count += 1
        if len(app_nodes_batch) >= APP_NODE_BATCH_SIZE:
            load_detected_app_nodes(
                neo4j_session,
                app_nodes_batch,
                tenant_id,
                update_tag,
            )
            logger.info("sync_detected_apps: loaded %d app nodes so far", app_count)
            app_nodes_batch.clear()

    if app_nodes_batch:
        load_detected_app_nodes(
            neo4j_session,
            app_nodes_batch,
            tenant_id,
            update_tag,
        )

    raw_report = await get_detected_app_raw_rows(client)
    _validate_report_columns(
        raw_report.fieldnames,
        APPINVRAWDATA_COLUMNS,
        APPINVRAWDATA_REPORT_NAME,
    )

    app_relationships_batch: list[dict[str, str]] = []
    relationship_count = 0
    for row in raw_report.rows:
        app_relationships_batch.append(transform_detected_app_relationship(row))
        if len(app_relationships_batch) >= APP_RELATIONSHIP_BATCH_SIZE:
            load_detected_app_relationships(
                neo4j_session,
                app_relationships_batch,
                tenant_id,
                update_tag,
            )
            relationship_count += len(app_relationships_batch)
            logger.info(
                "sync_detected_apps: loaded %d HAS_APP relationships so far",
                relationship_count,
            )
            app_relationships_batch.clear()

    if app_relationships_batch:
        load_detected_app_relationships(
            neo4j_session,
            app_relationships_batch,
            tenant_id,
            update_tag,
        )
        relationship_count += len(app_relationships_batch)

    logger.info(
        "sync_detected_apps: finished - %d apps and %d HAS_APP relationships",
        app_count,
        relationship_count,
    )

    cleanup_detected_app_nodes(neo4j_session, common_job_parameters)
    cleanup_detected_app_relationships(neo4j_session, common_job_parameters)


def _validate_report_columns(
    fieldnames: tuple[str, ...],
    required_columns: list[str],
    report_name: str,
) -> None:
    missing = [column for column in required_columns if column not in fieldnames]
    if missing:
        raise ValueError(
            f"{report_name} export is missing required columns: {', '.join(missing)}"
        )


def _get_required_value(
    row: Mapping[str, str],
    field_name: str,
    report_name: str,
) -> str:
    value = row.get(field_name, "").strip()
    if not value:
        raise ValueError(
            f"{report_name} row is missing required value for {field_name}: {row}"
        )
    return value


def _get_optional_value(row: Mapping[str, str], field_name: str) -> str | None:
    value = row.get(field_name, "").strip()
    return value or None


def _parse_optional_int(value: str | None) -> int | None:
    if not value:
        return None
    return int(value)
