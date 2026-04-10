import gc
import logging
from typing import Any
from typing import AsyncGenerator
from typing import Iterator

import neo4j
from kiota_abstractions.api_error import APIError
from msgraph import GraphServiceClient
from msgraph.generated.models.detected_app import DetectedApp
from msgraph.generated.models.managed_device import ManagedDevice

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.microsoft.intune.detected_app import IntuneDetectedAppSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

DETECTED_APP_ROW_BATCH_SIZE = 1000


@timeit
async def get_detected_apps(
    client: GraphServiceClient,
) -> AsyncGenerator[DetectedApp, None]:
    """
    Get all Intune detected apps with their associated managed devices expanded inline.
    https://learn.microsoft.com/en-us/graph/api/intune-devices-detectedapp-list
    Permissions: DeviceManagementManagedDevices.Read.All

    Uses $expand=managedDevices($select=id) as the fast path, but falls back to
    per-app managedDevices lookups when Graph returns empty managedDevices
    collections despite a non-zero deviceCount.
    """
    request_config = client.device_management.detected_apps.DetectedAppsRequestBuilderGetRequestConfiguration(
        query_parameters=client.device_management.detected_apps.DetectedAppsRequestBuilderGetQueryParameters(
            expand=["managedDevices($select=id)"],
        ),
    )

    page = await client.device_management.detected_apps.get(
        request_configuration=request_config,
    )
    while page:
        if page.value:
            for app in page.value:
                if app.id and (app.device_count or 0) > 0 and not app.managed_devices:
                    logger.debug(
                        "Detected app %s returned no expanded managedDevices despite "
                        "device_count=%s; falling back to per-app lookup.",
                        app.id,
                        app.device_count,
                    )
                    try:
                        app.managed_devices = (
                            await get_managed_devices_for_detected_app(
                                client,
                                app.id,
                            )
                        )
                    except APIError as e:
                        logger.warning(
                            "Failed fallback managed-device lookup for detected app %s "
                            "(status=%s); continuing without HAS_APP relationships for "
                            "this app.",
                            app.id,
                            e.response_status_code,
                        )
                yield app
        if not page.odata_next_link:
            break

        page = await client.device_management.detected_apps.with_url(
            page.odata_next_link,
        ).get()


@timeit
async def get_managed_devices_for_detected_app(
    client: GraphServiceClient,
    detected_app_id: str,
) -> list[ManagedDevice]:
    """
    Fetch the managed devices for a specific detected app.

    Microsoft Graph documents the managedDevices relationship on detectedApp,
    but in practice the list endpoint can return empty expanded collections
    even when deviceCount is non-zero. This fallback keeps HAS_APP edges
    accurate without requiring per-app lookups in the common case.
    """
    managed_devices_builder = client.device_management.detected_apps.by_detected_app_id(
        detected_app_id,
    ).managed_devices
    request_config = managed_devices_builder.ManagedDevicesRequestBuilderGetRequestConfiguration(
        query_parameters=managed_devices_builder.ManagedDevicesRequestBuilderGetQueryParameters(
            select=["id"],
        ),
    )

    devices: list[ManagedDevice] = []
    page = await managed_devices_builder.get(request_configuration=request_config)
    while page:
        if page.value:
            devices.extend(page.value)
        if not page.odata_next_link:
            break

        page = await managed_devices_builder.with_url(page.odata_next_link).get()

    return devices


def transform_detected_apps(
    apps: list[DetectedApp],
) -> list[dict[str, Any]]:
    """
    Transform detected apps into dicts matching IntuneDetectedAppSchema.
    Denormalizes the app-to-device relationship: one row per (app, device) pair.
    Apps with no associated devices still produce one row with device_id=None.
    """
    result: list[dict[str, Any]] = []
    for app in apps:
        base: dict[str, Any] = {
            "id": app.id,
            "display_name": app.display_name,
            "version": app.version,
            "size_in_byte": app.size_in_byte,
            "device_count": app.device_count,
            "publisher": app.publisher,
            "platform": app.platform.value if app.platform else None,
        }
        if app.managed_devices:
            for device in app.managed_devices:
                result.append({**base, "device_id": device.id})
        else:
            result.append({**base, "device_id": None})
    return result


def iter_detected_app_rows(
    app: DetectedApp,
) -> Iterator[dict[str, Any]]:
    """
    Yield rows matching IntuneDetectedAppSchema for a single detected app.

    This avoids materializing a large intermediate list for batches of apps that
    may each expand to many managed-device relationships.
    """
    base: dict[str, Any] = {
        "id": app.id,
        "display_name": app.display_name,
        "version": app.version,
        "size_in_byte": app.size_in_byte,
        "device_count": app.device_count,
        "publisher": app.publisher,
        "platform": app.platform.value if app.platform else None,
    }

    if app.managed_devices:
        for device in app.managed_devices:
            yield {**base, "device_id": device.id}
    else:
        yield {**base, "device_id": None}


@timeit
def load_detected_apps(
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
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        IntuneDetectedAppSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
async def sync_detected_apps(
    neo4j_session: neo4j.Session,
    client: GraphServiceClient,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    row_batch: list[dict[str, Any]] = []
    apps_processed = 0
    rows_processed = 0

    async for app in get_detected_apps(client):
        apps_processed += 1

        for row in iter_detected_app_rows(app):
            row_batch.append(row)
            rows_processed += 1

            if len(row_batch) >= DETECTED_APP_ROW_BATCH_SIZE:
                current_batch_size = len(row_batch)
                load_detected_apps(neo4j_session, row_batch, tenant_id, update_tag)
                logger.info(
                    "Loaded batch of %d detected app rows "
                    "(apps processed: %d, total rows: %d)",
                    current_batch_size,
                    apps_processed,
                    rows_processed,
                )
                row_batch.clear()
                gc.collect()

        # Expanded managed-device lists can be large; release them as soon as the
        # corresponding rows have been flushed into the current row batch.
        app.managed_devices = None

    if row_batch:
        current_batch_size = len(row_batch)
        load_detected_apps(neo4j_session, row_batch, tenant_id, update_tag)
        logger.info(
            "Loaded final batch of %d detected app rows "
            "(apps processed: %d, total rows: %d)",
            current_batch_size,
            apps_processed,
            rows_processed,
        )
        row_batch.clear()
        gc.collect()

    cleanup(neo4j_session, common_job_parameters)
    logger.info(
        "Completed syncing %d detected apps into %d rows",
        apps_processed,
        rows_processed,
    )
