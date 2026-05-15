import logging
import re
from typing import Any

import neo4j
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.mgmt.web import WebSiteManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.azure.util.tag import transform_tags
from cartography.intel.container_arch import normalize_architecture
from cartography.intel.container_image import parse_image_uri
from cartography.models.azure.function_app import AzureFunctionAppSchema
from cartography.models.azure.tags.function_app_tag import AzureFunctionAppTagsSchema
from cartography.util import timeit

from .util.credentials import Credentials

# Resource ID pattern:
# /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Web/sites/{name}
_RESOURCE_ID_RE = re.compile(
    r"/subscriptions/[^/]+/resourceGroups/(?P<rg>[^/]+)/providers/Microsoft\.Web/sites/(?P<name>[^/]+)",
    re.IGNORECASE,
)

logger = logging.getLogger(__name__)


@timeit
def get_function_apps(credentials: Credentials, subscription_id: str) -> list[dict]:
    """
    Get a list of Function Apps from the given Azure subscription.
    """
    try:
        client = WebSiteManagementClient(credentials.credential, subscription_id)
        # Note: Function Apps are a type of Web App, so we list all web apps
        # and then filter them in the transform stage.
        return [app.as_dict() for app in client.web_apps.list()]

    except ClientAuthenticationError as e:
        logger.warning(
            (
                "Failed to authenticate to get function apps for subscription '%s'. "
                "Please check your credentials. Error: %s"
            ),
            subscription_id,
            e,
        )
        return []

    except HttpResponseError as e:
        logger.warning(
            (
                "Failed to get function apps for subscription '%s' due to an API error. "
                "Status code: %s. Message: %s"
            ),
            subscription_id,
            e.status_code,
            str(e),
        )
        return []


def _parse_resource_id(resource_id: str | None) -> tuple[str | None, str | None]:
    if not resource_id:
        return None, None
    match = _RESOURCE_ID_RE.match(resource_id)
    if not match:
        return None, None
    return match.group("rg"), match.group("name")


def _linux_fx_version_is_container(linux_fx_version: str | None) -> bool:
    # Function Apps advertise a container deployment via a DOCKER|... prefix on
    # linuxFxVersion. Code-based apps use runtime tokens (e.g. PYTHON|3.11).
    if not linux_fx_version:
        return False
    return linux_fx_version.upper().startswith("DOCKER|")


@timeit
def fetch_function_app_configurations(
    client: WebSiteManagementClient, apps: list[dict]
) -> dict[str, dict[str, Any]]:
    """
    For each function app, fetch its site configuration to read linuxFxVersion
    (where container image references live). Returns a map keyed by the app's
    resource id. Apps whose config cannot be fetched are skipped rather than
    failing the whole sync; their image fields will simply be absent.
    """
    configurations: dict[str, dict[str, Any]] = {}
    for app in apps:
        resource_id = app.get("id")
        if not isinstance(resource_id, str):
            continue
        resource_group, name = _parse_resource_id(resource_id)
        if not resource_group or not name:
            continue
        try:
            config = client.web_apps.get_configuration(resource_group, name)
            configurations[resource_id] = config.as_dict()
        except (ClientAuthenticationError, HttpResponseError) as e:
            logger.warning(
                "Failed to get site configuration for function app '%s': %s",
                resource_id,
                e,
            )
    return configurations


@timeit
def transform_function_apps(
    function_apps_response: list[dict],
    configurations: dict[str, dict[str, Any]] | None = None,
) -> list[dict]:
    """
    Transform the raw API response to the dictionary structure that the model expects.
    """
    configurations = configurations or {}
    transformed_apps: list[dict[str, Any]] = []
    for app in function_apps_response:
        # We only want to ingest resources that are explicitly function apps.
        if "functionapp" in app.get("kind", ""):
            app_id = app.get("id")
            # Distinguish "config fetched and has no DOCKER| marker" (genuine code
            # deployment) from "config fetch failed" (unknown). Silently defaulting
            # to "code" on a transient Azure error would misclassify container apps.
            site_config: dict[str, Any] | None = (
                configurations.get(app_id) if isinstance(app_id, str) else None
            )
            if site_config is not None:
                linux_fx_version = site_config.get(
                    "linux_fx_version"
                ) or site_config.get("linuxFxVersion")
                is_container: bool | None = _linux_fx_version_is_container(
                    linux_fx_version
                )
                image_uri, image_digest = (
                    parse_image_uri(linux_fx_version) if is_container else (None, None)
                )
                architecture_normalized: str | None = None
                if is_container:
                    # Function Apps do not expose host architecture; we only know
                    # that Linux container plans default to amd64 today.
                    architecture_normalized = normalize_architecture("amd64")
                deployment_type: str | None = "container" if is_container else "code"
            else:
                is_container = None
                deployment_type = None
                image_uri = None
                image_digest = None
                architecture_normalized = None

            transformed_app = {
                "id": app.get("id"),
                "name": app.get("name"),
                "kind": app.get("kind"),
                "location": app.get("location"),
                "state": app.get("state"),
                "default_host_name": app.get("default_host_name"),
                "https_only": app.get("https_only"),
                "is_container": is_container,
                "deployment_type": deployment_type,
                "image_uri": image_uri,
                "image_digest": image_digest,
                "architecture_normalized": architecture_normalized,
                "tags": app.get("tags"),
            }
            transformed_apps.append(transformed_app)
    return transformed_apps


@timeit
def load_function_apps(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Load the transformed Azure Function App data to Neo4j.
    """
    load(
        neo4j_session,
        AzureFunctionAppSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_function_app_tags(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    apps: list[dict],
    update_tag: int,
) -> None:
    """
    Loads tags for Function Apps.
    """
    tags = transform_tags(apps, subscription_id)
    load(
        neo4j_session,
        AzureFunctionAppTagsSchema(),
        tags,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def cleanup_function_apps(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Run the cleanup job for Azure Function Apps.
    """
    GraphJob.from_node_schema(AzureFunctionAppSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_function_app_tags(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Runs cleanup job for Azure Function App tags.
    """
    GraphJob.from_node_schema(AzureFunctionAppTagsSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    The main sync function for Azure Function Apps.
    """
    logger.info(f"Syncing Azure Function Apps for subscription {subscription_id}.")
    raw_apps = get_function_apps(credentials, subscription_id)
    function_apps = [app for app in raw_apps if "functionapp" in app.get("kind", "")]
    client = WebSiteManagementClient(credentials.credential, subscription_id)
    configurations = fetch_function_app_configurations(client, function_apps)
    transformed_apps = transform_function_apps(raw_apps, configurations)
    load_function_apps(neo4j_session, transformed_apps, subscription_id, update_tag)
    load_function_app_tags(neo4j_session, subscription_id, transformed_apps, update_tag)
    cleanup_function_apps(neo4j_session, common_job_parameters)
    cleanup_function_app_tags(neo4j_session, common_job_parameters)
