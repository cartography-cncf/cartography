import logging
from collections import defaultdict
from collections.abc import Sequence
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
    "ApplicationName",
    "ApplicationPublisher",
    "ApplicationVersion",
    "Platform",
    "DeviceId",
]


@timeit
async def get_detected_app_aggregate_rows(
    client: GraphServiceClient,
) -> ExportedReportRows:
    return await export_report_rows(
        client,
        APPINVAGGREGATE_REPORT_NAME,
        APPINVAGGREGATE_COLUMNS,
    )


@timeit
async def get_detected_app_raw_rows(
    client: GraphServiceClient,
) -> ExportedReportRows:
    return await export_report_rows(
        client,
        APPINVRAWDATA_REPORT_NAME,
        APPINVRAWDATA_COLUMNS,
    )


def transform_detected_app(row: Mapping[str, str | None]) -> dict[str, Any]:
    return {
        "id": _get_required_value(row, "ApplicationKey", APPINVAGGREGATE_REPORT_NAME),
        "application_id": _get_optional_value(row, "ApplicationId"),
        "display_name": _get_optional_value(row, "ApplicationName"),
        "version": _get_optional_value(row, "ApplicationVersion"),
        "device_count": _parse_optional_int(row.get("DeviceCount")),
        "publisher": _get_optional_value(row, "ApplicationPublisher"),
        "platform": _get_optional_value(row, "Platform"),
    }


def transform_detected_app_from_raw(row: Mapping[str, str | None]) -> dict[str, Any]:
    return {
        "id": _get_required_value(row, "ApplicationKey", APPINVRAWDATA_REPORT_NAME),
        "application_id": None,
        "display_name": _get_optional_value(row, "ApplicationName"),
        "version": _get_optional_value(row, "ApplicationVersion"),
        "device_count": None,
        "publisher": _get_optional_value(row, "ApplicationPublisher"),
        "platform": _get_optional_value(row, "Platform"),
    }


def transform_detected_app_relationship(
    row: Mapping[str, str | None],
) -> dict[str, str]:
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


def build_detected_app_export_rows(
    aggregate_rows: Sequence[Mapping[str, str | None]],
    raw_rows: Sequence[Mapping[str, str | None]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """
    Build node and relationship payloads from the Intune discovered-app exports.

    Intune does not guarantee that AppInvAggregate and AppInvRawData have the same
    keyset. In live tenant data, some apps are present only in aggregate and some
    only in raw. We therefore treat the reports as complementary:
    - app nodes come from the union of ApplicationKey across both exports
    - HAS_APP relationships come only from AppInvRawData

    Aggregate is still the preferred node source because it carries ApplicationId
    and the report-level device count. Raw is used to backfill app nodes that are
    missing from aggregate and to supply a distinct-device fallback count.
    """
    aggregate_apps_by_id: dict[str, dict[str, Any]] = {}
    for row in aggregate_rows:
        app = transform_detected_app(row)
        aggregate_apps_by_id[app["id"]] = app

    raw_apps_by_id: dict[str, dict[str, Any]] = {}
    raw_device_ids_by_app_id: dict[str, set[str]] = defaultdict(set)
    relationships: list[dict[str, str]] = []
    seen_relationships: set[tuple[str, str]] = set()
    for row in raw_rows:
        relationship = transform_detected_app_relationship(row)
        pair = (relationship["app_id"], relationship["device_id"])
        if pair in seen_relationships:
            continue
        seen_relationships.add(pair)
        relationships.append(relationship)
        raw_device_ids_by_app_id[relationship["app_id"]].add(relationship["device_id"])
        raw_apps_by_id.setdefault(
            relationship["app_id"],
            transform_detected_app_from_raw(row),
        )

    apps: list[dict[str, Any]] = []
    for app_id in sorted(aggregate_apps_by_id.keys() | raw_apps_by_id.keys()):
        aggregate_app = aggregate_apps_by_id.get(app_id)
        raw_app = raw_apps_by_id.get(app_id)
        raw_device_count = len(raw_device_ids_by_app_id.get(app_id, ()))
        apps.append(
            _merge_detected_app_payloads(
                app_id,
                aggregate_app=aggregate_app,
                raw_app=raw_app,
                raw_device_count=raw_device_count,
            ),
        )

    return apps, relationships


def _merge_detected_app_payloads(
    app_id: str,
    *,
    aggregate_app: dict[str, Any] | None,
    raw_app: dict[str, Any] | None,
    raw_device_count: int,
) -> dict[str, Any]:
    if aggregate_app is None and raw_app is None:
        raise ValueError(f"Detected app {app_id} must come from aggregate or raw data.")

    preferred = aggregate_app or raw_app
    assert preferred is not None

    # Prefer aggregate metadata when it exists, but backfill missing fields from
    # raw so the node remains useful even when the aggregate row is sparse.
    return {
        "id": app_id,
        "application_id": _coalesce_field(aggregate_app, raw_app, "application_id"),
        "display_name": _coalesce_field(aggregate_app, raw_app, "display_name"),
        "version": _coalesce_field(aggregate_app, raw_app, "version"),
        "device_count": (
            preferred["device_count"]
            if preferred.get("device_count") is not None
            else raw_device_count
        ),
        "publisher": _coalesce_field(aggregate_app, raw_app, "publisher"),
        "platform": _coalesce_field(aggregate_app, raw_app, "platform"),
    }


def _coalesce_field(
    primary: Mapping[str, Any] | None,
    secondary: Mapping[str, Any] | None,
    field_name: str,
) -> Any:
    if primary is not None:
        value = primary.get(field_name)
        if value is not None:
            return value
    if secondary is not None:
        return secondary.get(field_name)
    return None


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

    raw_report = await get_detected_app_raw_rows(client)
    _validate_report_columns(
        raw_report.fieldnames,
        APPINVRAWDATA_COLUMNS,
        APPINVRAWDATA_REPORT_NAME,
    )

    apps, relationships = build_detected_app_export_rows(
        aggregate_report.rows,
        raw_report.rows,
    )

    app_relationships_batch: list[dict[str, str]] = []
    app_nodes_batch: list[dict[str, Any]] = []
    app_count = 0
    for app in apps:
        app_nodes_batch.append(app)
        if len(app_nodes_batch) >= APP_NODE_BATCH_SIZE:
            load_detected_app_nodes(
                neo4j_session,
                app_nodes_batch,
                tenant_id,
                update_tag,
            )
            app_count += len(app_nodes_batch)
            logger.info("sync_detected_apps: loaded %d app nodes so far", app_count)
            app_nodes_batch.clear()

    if app_nodes_batch:
        load_detected_app_nodes(
            neo4j_session,
            app_nodes_batch,
            tenant_id,
            update_tag,
        )
        app_count += len(app_nodes_batch)

    relationship_count = 0
    for relationship in relationships:
        app_relationships_batch.append(relationship)
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
        len(apps),
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
    row: Mapping[str, str | None],
    field_name: str,
    report_name: str,
) -> str:
    value = row.get(field_name)
    if value is None:
        value = ""
    value = value.strip()
    if not value:
        raise ValueError(
            f"{report_name} row is missing required value for {field_name}: {row}"
        )
    return value


def _get_optional_value(
    row: Mapping[str, str | None],
    field_name: str,
) -> str | None:
    value = row.get(field_name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _parse_optional_int(value: str | None) -> int | None:
    if not value:
        return None
    return int(value)
