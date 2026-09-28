from __future__ import annotations

# Okta intel module - Organization
import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.models.okta.organization import OktaOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_okta_organization(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Add the OktaOrganization subresource
    """
    _load_organization(neo4j_session, common_job_parameters)


@timeit
def _load_organization(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
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
        },
    ]
    load(
        neo4j_session,
        OktaOrganizationSchema(),
        data,
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )
