import logging
from typing import Any

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import cartography.intel.tailscale.acls
import cartography.intel.tailscale.devices
import cartography.intel.tailscale.grants
import cartography.intel.tailscale.postureintegrations
import cartography.intel.tailscale.postureresolution
import cartography.intel.tailscale.services
import cartography.intel.tailscale.tailnets
import cartography.intel.tailscale.users
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)

_OAUTH_TIMEOUT = (10, 30)
_REAUTH_HEADER = "X-Cartography-Tailscale-Reauth"


def _mint_oauth_bearer(
    api_session: requests.Session,
    base_url: str,
    client_id: str,
    client_secret: str,
) -> str:
    response = api_session.post(
        f"{base_url.rstrip('/')}/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={_REAUTH_HEADER: "1", "Authorization": None},
        timeout=_OAUTH_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def _attach_oauth_refresh(
    api_session: requests.Session,
    base_url: str,
    client_id: str,
    client_secret: str,
) -> None:
    """
    Tailscale OAuth access tokens expire after one hour, which a large tailnet
    sync can outrun. Install a response hook that re-mints the bearer once on
    401 and retries the original request.
    """
    token_url = f"{base_url.rstrip('/')}/oauth/token"

    def _refresh_on_unauthorized(
        response: requests.Response,
        *args: Any,
        **kwargs: Any,
    ) -> requests.Response:
        if response.status_code != 401:
            return response
        if response.request.url == token_url:
            return response
        if response.request.headers.get(_REAUTH_HEADER):
            return response
        logger.info("Tailscale returned 401; re-minting OAuth bearer and retrying.")
        new_token = _mint_oauth_bearer(
            api_session, base_url, client_id, client_secret,
        )
        api_session.headers["Authorization"] = f"Bearer {new_token}"
        retried = response.request.copy()
        retried.headers["Authorization"] = f"Bearer {new_token}"
        retried.headers[_REAUTH_HEADER] = "1"
        return api_session.send(retried, **kwargs)

    api_session.hooks["response"].append(_refresh_on_unauthorized)


@timeit
def start_tailscale_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Tailscale data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """

    has_oauth_client = bool(
        config.tailscale_oauth_client_id and config.tailscale_oauth_client_secret,
    )
    if not config.tailscale_org or not (config.tailscale_token or has_oauth_client):
        logger.info(
            "Tailscale import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    if config.tailscale_token and has_oauth_client:
        logger.warning(
            "Both --tailscale-token-env-var and --tailscale-oauth-client-* are "
            "set; using the OAuth client.",
        )

    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))

    if has_oauth_client:
        bearer_token = _mint_oauth_bearer(
            api_session,
            config.tailscale_base_url,
            config.tailscale_oauth_client_id,
            config.tailscale_oauth_client_secret,
        )
        api_session.headers.update({"Authorization": f"Bearer {bearer_token}"})
        _attach_oauth_refresh(
            api_session,
            config.tailscale_base_url,
            config.tailscale_oauth_client_id,
            config.tailscale_oauth_client_secret,
        )
    else:
        api_session.headers.update(
            {"Authorization": f"Bearer {config.tailscale_token}"},
        )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": config.tailscale_base_url,
        "org": config.tailscale_org,
    }

    cartography.intel.tailscale.tailnets.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        org=config.tailscale_org,
    )

    users = cartography.intel.tailscale.users.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        org=config.tailscale_org,
    )

    devices, device_posture_attributes = cartography.intel.tailscale.devices.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        org=config.tailscale_org,
    )

    cartography.intel.tailscale.postureintegrations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        org=config.tailscale_org,
    )

    services = cartography.intel.tailscale.services.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        org=config.tailscale_org,
    )

    postures, posture_conditions, grants, groups = (
        cartography.intel.tailscale.acls.sync(
            neo4j_session,
            api_session,
            common_job_parameters,
            org=config.tailscale_org,
            users=users,
        )
    )

    posture_matches = cartography.intel.tailscale.postureresolution.sync(
        neo4j_session,
        org=config.tailscale_org,
        update_tag=config.update_tag,
        postures=postures,
        posture_conditions=posture_conditions,
        device_posture_attributes=device_posture_attributes,
    )

    cartography.intel.tailscale.grants.sync(
        neo4j_session,
        org=config.tailscale_org,
        update_tag=config.update_tag,
        grants=grants,
        devices=devices,
        groups=groups,
        tags=[],  # Tags are resolved from device data directly
        users=users,
        services=services,
        posture_matches=posture_matches,
    )
