from __future__ import annotations

# Okta intel module - Organization
import asyncio
import logging
from typing import Any

import neo4j
from okta.client import Client as OktaClient

from cartography.client.core.tx import load
from cartography.intel.okta.common import is_missing_scope_error
from cartography.intel.okta.common import is_resource_not_found_error
from cartography.intel.okta.common import OktaApiError
from cartography.intel.okta.common import raise_for_okta_error
from cartography.models.okta.organization import OktaOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_okta_organization(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    okta_client: OktaClient | None = None,
) -> dict[str, Any]:
    """
    Add the OktaOrganization subresource and return the properties loaded on it
    """
    admin_console_settings: dict[str, Any] = {}
    if okta_client is not None:
        admin_console_settings = _get_admin_console_settings(okta_client)
    _load_organization(neo4j_session, common_job_parameters, admin_console_settings)
    return admin_console_settings


def record_okta_sync_coverage(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    org_properties: dict[str, Any],
    coverage: dict[str, bool],
) -> None:
    """
    Reload the organization with flags saying whether the API token could read
    resources that need extra permissions, so an org without them can be told
    apart from one whose token could not read them.
    """
    _load_organization(
        neo4j_session,
        common_job_parameters,
        {**org_properties, **coverage},
    )


@timeit
def _get_admin_console_settings(okta_client: OktaClient) -> dict[str, Any]:
    """
    Return the Okta Admin Console session settings, or an empty dict when the
    token cannot read them or the org does not expose them (Classic Engine).
    """
    try:
        settings = asyncio.run(_fetch_admin_console_settings(okta_client))
    except OktaApiError as exc:
        if is_missing_scope_error(exc) or is_resource_not_found_error(exc):
            logger.warning(
                "Unable to read Okta Admin Console session settings - api token "
                "needs okta.apps.read and an Identity Engine org",
            )
            return {}
        raise
    if settings is None:
        return {}
    return {
        "admin_console_session_idle_timeout_minutes": settings.session_idle_timeout_minutes,
        "admin_console_session_max_lifetime_minutes": settings.session_max_lifetime_minutes,
    }


async def _fetch_admin_console_settings(okta_client: OktaClient) -> Any:
    settings, _, error = await okta_client.get_first_party_app_settings(
        "admin-console",
    )
    raise_for_okta_error(error, "get_first_party_app_settings")
    return settings


@timeit
def _load_organization(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    properties: dict[str, Any] | None = None,
) -> None:
    """
    Load the host node into the graph
    """
    # The Okta API has no separate tenant "name" field: the org slug
    # (e.g. "lyft") is what identifies the tenant, so we mirror it into
    # the name property to satisfy the ontology Tenant mapping.
    org_id = common_job_parameters["OKTA_ORG_ID"]
    data = [
        {
            "id": org_id,
            "name": org_id,
            **(properties or {}),
        },
    ]
    load(
        neo4j_session,
        OktaOrganizationSchema(),
        data,
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )
