import json
import logging
from typing import Any
from urllib.parse import quote

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.github.util import fetch_all_rest_api_pages
from cartography.intel.github.util import github_org_url
from cartography.intel.github.util import rest_api_base_url
from cartography.models.github.app_installations import GitHubAppInstallationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(
    token: Any,
    api_url: str,
    organization: str,
) -> list[dict[str, Any]] | None:
    """
    Fetch the GitHub Apps installed on the organization.

    Requires an organization owner with the organization **Administration: Read**
    permission (fine-grained PAT or GitHub App) or the `read:org` scope (classic
    PAT). Returns None when the list is unavailable so stale data is preserved.
    """
    try:
        return fetch_all_rest_api_pages(
            token,
            rest_api_base_url(api_url),
            f"/orgs/{quote(organization, safe='')}/installations",
            "installations",
            params={"per_page": 100},
            raise_on_status=(403, 404),
        )
    except requests.exceptions.RequestException as err:
        logger.warning(
            "Skipping GitHub App installations for org %s due to HTTP %s. This "
            "endpoint requires organization owner access with the organization "
            "Administration: Read permission.",
            organization,
            err.response.status_code if err.response is not None else None,
        )
        return None


def transform(
    installations: list[dict[str, Any]],
    org_url: str,
) -> list[dict[str, Any]]:
    result = []
    for installation in installations:
        installation_id = installation.get("id")
        if installation_id is None:
            continue
        permissions = installation.get("permissions") or {}
        suspended_by = installation.get("suspended_by") or {}
        result.append(
            {
                "id": f"{org_url}/installations/{installation_id}",
                "installation_id": installation_id,
                "app_id": installation.get("app_id"),
                "app_slug": installation.get("app_slug"),
                "client_id": installation.get("client_id"),
                "target_type": installation.get("target_type"),
                "repository_selection": installation.get("repository_selection"),
                "permissions": json.dumps(permissions, sort_keys=True),
                "read_permissions": sorted(
                    name for name, level in permissions.items() if level == "read"
                ),
                "write_permissions": sorted(
                    name
                    for name, level in permissions.items()
                    if level in ("write", "admin")
                ),
                "admin_permissions": sorted(
                    name for name, level in permissions.items() if level == "admin"
                ),
                "events": installation.get("events") or [],
                "enabled": installation.get("suspended_at") is None,
                "suspended_at": installation.get("suspended_at"),
                "suspended_by": suspended_by.get("login"),
                "html_url": installation.get("html_url"),
                "created_at": installation.get("created_at"),
                "updated_at": installation.get("updated_at"),
            },
        )
    return result


@timeit
def load_installations(
    neo4j_session: neo4j.Session,
    installations: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitHubAppInstallationSchema(),
        installations,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    org_url: str,
    update_tag: int,
) -> None:
    GraphJob.from_node_schema(
        GitHubAppInstallationSchema(),
        {"UPDATE_TAG": update_tag, "org_url": org_url},
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    token: Any,
    api_url: str,
    organization: str,
) -> None:
    raw_installations = get(token, api_url, organization)
    if raw_installations is None:
        return
    org_url = github_org_url(api_url, organization)
    update_tag = common_job_parameters["UPDATE_TAG"]
    load_installations(
        neo4j_session,
        transform(raw_installations, org_url),
        org_url,
        update_tag,
    )
    cleanup(neo4j_session, org_url, update_tag)
