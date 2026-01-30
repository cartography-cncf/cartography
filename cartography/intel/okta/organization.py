# Okta intel module - Organization
import logging
from typing import Any
from typing import Dict

import neo4j

from cartography.client.core.tx import load
from cartography.models.okta.organization import OktaOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_okta_organization(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Add the OktaOrganization subresource
    """
    _load_organization(neo4j_session, common_job_parameters)


@timeit
def _load_organization(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Load the host node into the graph
    """
    data = [
        {
            "id": common_job_parameters["OKTA_ORG_ID"],
        },
    ]
    load(
        neo4j_session,
        OktaOrganizationSchema(),
        data,
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )
