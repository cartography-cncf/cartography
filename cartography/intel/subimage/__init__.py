import logging
from typing import Any

import neo4j

import cartography.intel.subimage.apikeys
import cartography.intel.subimage.frameworks
import cartography.intel.subimage.modules
import cartography.intel.subimage.neo4jusers
import cartography.intel.subimage.team
import cartography.intel.subimage.tenant
from cartography.config import Config
from cartography.intel.subimage.util import create_api_session
from cartography.intel.subimage.util import get_access_token
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_subimage_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not (
        config.subimage_client_id
        and config.subimage_client_secret
        and config.subimage_tenant_url
        and config.subimage_authkit_url
    ):
        logger.info(
            "SubImage import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    access_token = get_access_token(
        config.subimage_client_id,
        config.subimage_client_secret,
        config.subimage_authkit_url,
    )
    api_session = create_api_session(access_token)
    base_url = config.subimage_tenant_url.rstrip("/")

    tenants = cartography.intel.subimage.tenant.sync(
        neo4j_session,
        api_session,
        config.update_tag,
        base_url,
    )

    for tenant_data in tenants:
        tenant_id = tenant_data["id"]

        common_job_parameters: dict[str, Any] = {
            "UPDATE_TAG": config.update_tag,
            "TENANT_ID": tenant_id,
            "BASE_URL": base_url,
        }

        cartography.intel.subimage.team.sync(
            neo4j_session,
            api_session,
            tenant_id,
            config.update_tag,
            common_job_parameters,
        )

        cartography.intel.subimage.apikeys.sync(
            neo4j_session,
            api_session,
            tenant_id,
            config.update_tag,
            common_job_parameters,
        )

        cartography.intel.subimage.neo4jusers.sync(
            neo4j_session,
            api_session,
            tenant_id,
            config.update_tag,
            common_job_parameters,
        )

        cartography.intel.subimage.modules.sync(
            neo4j_session,
            api_session,
            tenant_id,
            config.update_tag,
            common_job_parameters,
        )

        cartography.intel.subimage.frameworks.sync(
            neo4j_session,
            api_session,
            tenant_id,
            config.update_tag,
            common_job_parameters,
        )
