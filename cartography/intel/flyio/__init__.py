import logging

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import cartography.intel.flyio.apps
import cartography.intel.flyio.certificates
import cartography.intel.flyio.machines
import cartography.intel.flyio.secrets
import cartography.intel.flyio.volumes
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_flyio_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Fly.io data. Otherwise skip.
    """
    if not config.flyio_token or not config.flyio_org_slug:
        logger.info(
            "Fly.io import is not configured - skipping this module. "
            "Set flyio_token and flyio_org_slug to enable the Fly.io sync stage.",
        )
        return

    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    api_session.headers.update({"Authorization": _make_auth_header(config.flyio_token)})

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": config.flyio_base_url,
        "ORGANIZATION_ID": config.flyio_org_slug,
    }

    apps = cartography.intel.flyio.apps.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    for app in apps:
        app_job_parameters = {
            **common_job_parameters,
            "APP_ID": app["id"],
            "APP_NAME": app["name"],
        }
        cartography.intel.flyio.machines.sync(
            neo4j_session,
            api_session,
            app_job_parameters,
        )
        cartography.intel.flyio.volumes.sync(
            neo4j_session,
            api_session,
            app_job_parameters,
        )
        cartography.intel.flyio.secrets.sync(
            neo4j_session,
            api_session,
            app_job_parameters,
        )
        cartography.intel.flyio.certificates.sync(
            neo4j_session,
            api_session,
            app_job_parameters,
        )

    cartography.intel.flyio.apps.cleanup_apps(
        neo4j_session,
        common_job_parameters,
        cascade_delete=True,
    )


def _make_auth_header(token: str) -> str:
    if token.startswith("Bearer ") or token.startswith("FlyV1 "):
        return token
    return f"Bearer {token}"
