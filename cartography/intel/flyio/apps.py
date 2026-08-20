import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.flyio.util import get_json
from cartography.intel.flyio.util import require_list
from cartography.intel.flyio.util import require_non_empty
from cartography.models.flyio.app import FlyAppSchema
from cartography.models.flyio.organization import FlyOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    org_slug = common_job_parameters["ORGANIZATION_ID"]
    response = get(
        api_session,
        common_job_parameters["BASE_URL"],
        org_slug,
    )
    apps = transform_apps(response)
    organizations = transform_organizations(response, org_slug)
    load_organizations(
        neo4j_session, organizations, common_job_parameters["UPDATE_TAG"]
    )
    load_apps(
        neo4j_session,
        apps,
        org_slug,
        common_job_parameters["UPDATE_TAG"],
    )
    return apps


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    org_slug: str,
) -> dict[str, Any]:
    return get_json(api_session, f"{base_url}/v1/apps", org_slug=org_slug)


def transform_organizations(
    response: dict[str, Any],
    org_slug: str,
) -> list[dict[str, Any]]:
    orgs_by_id: dict[str, dict[str, Any]] = {}
    for app in require_list(response.get("apps"), "apps"):
        org = app.get("organization") or {}
        slug = org.get("slug") or org_slug
        orgs_by_id[org_slug] = {
            "id": org_slug,
            "name": org.get("name") or org_slug,
            "slug": slug,
            "internal_numeric_id": org.get("internal_numeric_id"),
        }

    if not orgs_by_id:
        orgs_by_id[org_slug] = {
            "id": org_slug,
            "name": org_slug,
            "slug": org_slug,
            "internal_numeric_id": None,
        }

    return list(orgs_by_id.values())


def transform_apps(response: dict[str, Any]) -> list[dict[str, Any]]:
    apps = []
    for app in require_list(response.get("apps"), "apps"):
        app_id = require_non_empty(app.get("id"), "app id")
        app_name = require_non_empty(app.get("name"), "app name")
        organization = app.get("organization") or {}
        apps.append(
            {
                "id": app_id,
                "name": app_name,
                "internal_numeric_id": app.get("internal_numeric_id"),
                "network": app.get("network"),
                "network_cidr": app.get("network_cidr"),
                "status": app.get("status"),
                "machine_count": app.get("machine_count"),
                "volume_count": app.get("volume_count"),
                "organization_slug": organization.get("slug"),
            }
        )
    return apps


@timeit
def load_organizations(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FlyOrganizationSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def load_apps(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_slug: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FlyAppSchema(),
        data,
        lastupdated=update_tag,
        ORGANIZATION_ID=org_slug,
    )


@timeit
def cleanup_apps(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    cascade_delete: bool = False,
) -> None:
    GraphJob.from_node_schema(
        FlyAppSchema(),
        common_job_parameters,
        cascade_delete=cascade_delete,
    ).run(neo4j_session)
