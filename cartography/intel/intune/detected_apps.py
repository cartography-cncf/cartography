import logging
from typing import Any
from typing import AsyncGenerator

import neo4j
from msgraph import GraphServiceClient
from msgraph.generated.models.detected_app import DetectedApp

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.intune.detected_app import IntuneDetectedAppSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get_detected_apps(
    client: GraphServiceClient,
) -> AsyncGenerator[DetectedApp, None]:
    """
    Get all Intune detected apps with their associated managed devices expanded inline.
    https://learn.microsoft.com/en-us/graph/api/intune-devices-detectedapp-list
    Permissions: DeviceManagementManagedDevices.Read.All

    Uses $expand=managedDevices($select=id) to fetch device associations in a
    single paginated request rather than making a separate call per app.
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
                yield app
        if not page.odata_next_link:
            break

        try:
            page = await client.device_management.detected_apps.with_url(
                page.odata_next_link,
            ).get()
        except Exception as e:
            logger.error(
                "Failed to fetch next page of Intune detected apps "
                "– stopping pagination early: %s",
                e,
            )
            break


@timeit
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


@timeit
def load_detected_apps(
    neo4j_session: neo4j.Session,
    apps: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(apps)} Intune detected app entries")
    load(
        neo4j_session,
        IntuneDetectedAppSchema(),
        apps,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


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
    apps_batch: list[DetectedApp] = []
    batch_size = 500

    async for app in get_detected_apps(client):
        apps_batch.append(app)

        if len(apps_batch) >= batch_size:
            transformed = transform_detected_apps(apps_batch)
            load_detected_apps(neo4j_session, transformed, tenant_id, update_tag)
            apps_batch.clear()

    if apps_batch:
        transformed = transform_detected_apps(apps_batch)
        load_detected_apps(neo4j_session, transformed, tenant_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
