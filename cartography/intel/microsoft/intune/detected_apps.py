import logging
from typing import Any
from typing import AsyncGenerator

import neo4j
from kiota_abstractions.api_error import APIError
from msgraph import GraphServiceClient
from msgraph.generated.models.detected_app import DetectedApp

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.microsoft.client import get_api_error_response_header
from cartography.models.microsoft.intune.detected_app import IntuneDetectedAppSchema
from cartography.models.microsoft.intune.detected_app import (
    IntuneManagedDeviceToDetectedAppMatchLink,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

DETECTED_APPS_PAGE_SIZE = 50
DETECTED_APP_MANAGED_DEVICES_PAGE_SIZE = 100
APP_NODE_BATCH_SIZE = 100
APP_RELATIONSHIP_BATCH_SIZE = 500
DETECTED_APP_SELECT_FIELDS = [
    "id",
    "displayName",
    "version",
    "sizeInByte",
    "deviceCount",
    "publisher",
    "platform",
]


@timeit
async def get_detected_apps(
    client: GraphServiceClient,
) -> AsyncGenerator[DetectedApp, None]:
    """
    Get all Intune detected apps using lightweight pages.
    https://learn.microsoft.com/en-us/graph/api/intune-devices-detectedapp-list
    Permissions: DeviceManagementManagedDevices.Read.All
    """
    request_config = client.device_management.detected_apps.DetectedAppsRequestBuilderGetRequestConfiguration(
        query_parameters=client.device_management.detected_apps.DetectedAppsRequestBuilderGetQueryParameters(
            select=DETECTED_APP_SELECT_FIELDS,
            top=DETECTED_APPS_PAGE_SIZE,
        ),
    )

    page = await client.device_management.detected_apps.get(
        request_configuration=request_config,
    )
    while page:
        if page.value:
            for app in page.value:
                yield app
        if not page.odata_next_link:
            break

        next_page_url = page.odata_next_link
        page.value = None
        page = await client.device_management.detected_apps.with_url(
            next_page_url,
        ).get()


@timeit
async def get_managed_device_ids_for_detected_app(
    client: GraphServiceClient,
    detected_app_id: str,
) -> AsyncGenerator[str, None]:
    """
    Stream managed device IDs for a specific detected app.
    """
    managed_devices_builder = client.device_management.detected_apps.by_detected_app_id(
        detected_app_id,
    ).managed_devices
    request_config = managed_devices_builder.ManagedDevicesRequestBuilderGetRequestConfiguration(
        query_parameters=managed_devices_builder.ManagedDevicesRequestBuilderGetQueryParameters(
            select=["id"],
            top=DETECTED_APP_MANAGED_DEVICES_PAGE_SIZE,
        ),
    )

    page = await managed_devices_builder.get(request_configuration=request_config)
    while page:
        if page.value:
            for device in page.value:
                if device.id:
                    yield device.id
        if not page.odata_next_link:
            break

        next_page_url = page.odata_next_link
        page.value = None
        page = await managed_devices_builder.with_url(next_page_url).get()


def transform_detected_app(app: DetectedApp) -> dict[str, Any]:
    return {
        "id": app.id,
        "display_name": app.display_name,
        "version": app.version,
        "size_in_byte": app.size_in_byte,
        "device_count": app.device_count,
        "publisher": app.publisher,
        "platform": app.platform.value if app.platform else None,
    }


def transform_detected_app_relationship(
    app_id: str,
    device_id: str,
) -> dict[str, str]:
    return {
        "app_id": app_id,
        "device_id": device_id,
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
    app_nodes_batch: list[dict[str, Any]] = []
    app_relationships_batch: list[dict[str, str]] = []
    app_count = 0
    relationship_count = 0

    async for app in get_detected_apps(client):
        app_nodes_batch.append(transform_detected_app(app))
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

        if app.id and (app.device_count or 0) > 0:
            try:
                async for device_id in get_managed_device_ids_for_detected_app(
                    client,
                    app.id,
                ):
                    app_relationships_batch.append(
                        transform_detected_app_relationship(app.id, device_id),
                    )
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
            except APIError as e:
                logger.error(
                    "Failed managed-device lookup for detected app %s "
                    "(status=%s, retry_after=%s, request_id=%s, "
                    "client_request_id=%s, throttle_scope=%s, "
                    "throttle_information=%s); aborting Intune detected-app "
                    "sync to avoid partial HAS_APP cleanup.",
                    app.id,
                    e.response_status_code,
                    get_api_error_response_header(e, "Retry-After"),
                    get_api_error_response_header(e, "request-id"),
                    get_api_error_response_header(e, "client-request-id"),
                    get_api_error_response_header(e, "x-ms-throttle-scope"),
                    get_api_error_response_header(e, "x-ms-throttle-information"),
                )
                raise

    if app_nodes_batch:
        load_detected_app_nodes(
            neo4j_session,
            app_nodes_batch,
            tenant_id,
            update_tag,
        )

    if app_relationships_batch:
        load_detected_app_relationships(
            neo4j_session,
            app_relationships_batch,
            tenant_id,
            update_tag,
        )
        relationship_count += len(app_relationships_batch)

    logger.info(
        "sync_detected_apps: finished — %d apps and %d HAS_APP relationships",
        app_count,
        relationship_count,
    )

    cleanup_detected_app_nodes(neo4j_session, common_job_parameters)
    cleanup_detected_app_relationships(neo4j_session, common_job_parameters)
