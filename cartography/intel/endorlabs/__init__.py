import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.config import Config
from cartography.intel.endorlabs.dependency_metadata import sync_dependency_metadata
from cartography.intel.endorlabs.findings import sync_findings
from cartography.intel.endorlabs.package_versions import sync_package_versions
from cartography.intel.endorlabs.projects import sync_projects
from cartography.models.endorlabs.namespace import EndorLabsNamespaceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)


def _get_bearer_token(api_key: str, api_secret: str) -> str:
    response = requests.post(
        "https://api.endorlabs.com/v1/auth/api-key",
        json={"key": api_key, "secret": api_secret},
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["token"]


def _sync_namespace(
    neo4j_session: neo4j.Session,
    namespace: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EndorLabsNamespaceSchema(),
        [{"id": namespace, "name": namespace}],
        lastupdated=update_tag,
    )


@timeit
def start_endorlabs_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    if not config.endorlabs_api_key or not config.endorlabs_api_secret:
        logger.info(
            "Endor Labs import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    namespace = config.endorlabs_namespace
    if not namespace:
        logger.warning(
            "Endor Labs namespace is not configured. "
            "Set --endorlabs-namespace to specify the tenant namespace.",
        )
        return

    bearer_token = _get_bearer_token(
        config.endorlabs_api_key,
        config.endorlabs_api_secret,
    )

    _sync_namespace(neo4j_session, namespace, config.update_tag)

    common_job_parameters: dict[str, Any] = {
        "UPDATE_TAG": config.update_tag,
        "NAMESPACE_ID": namespace,
    }

    projects = sync_projects(
        neo4j_session,
        bearer_token,
        namespace,
        config.update_tag,
        common_job_parameters,
    )

    if not projects:
        logger.warning(
            "No Endor Labs projects found. Skipping remaining sync jobs.",
        )
        return

    sync_package_versions(
        neo4j_session,
        bearer_token,
        namespace,
        config.update_tag,
        common_job_parameters,
    )

    sync_dependency_metadata(
        neo4j_session,
        bearer_token,
        namespace,
        config.update_tag,
        common_job_parameters,
    )

    sync_findings(
        neo4j_session,
        bearer_token,
        namespace,
        config.update_tag,
        common_job_parameters,
    )
