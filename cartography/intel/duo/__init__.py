import logging
import os
from base64 import b64encode
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import neo4j

from cartography.config import Config
from cartography.util import timeit
from cartography.util.lazy import lazy_callable
from cartography.util.lazy import lazy_import

# Bound lazily so that the provider SDK only loads once the config gate below
# has decided that this module has something to sync.
if TYPE_CHECKING:
    import duo_client
else:
    duo_client = lazy_import("duo_client")

sync_duo_api_host = lazy_callable("cartography.intel.duo.api_host", "sync_duo_api_host")
sync_duo_endpoints = lazy_callable(
    "cartography.intel.duo.endpoints", "sync_duo_endpoints"
)
sync_duo_groups = lazy_callable("cartography.intel.duo.groups", "sync_duo_groups")
sync_duo_phones = lazy_callable("cartography.intel.duo.phones", "sync")
sync_duo_tokens = lazy_callable("cartography.intel.duo.tokens", "sync")
sync_duo_users = lazy_callable("cartography.intel.duo.users", "sync_duo_users")
sync_duo_web_authn_credentials = lazy_callable(
    "cartography.intel.duo.web_authn_credentials", "sync"
)

logger = logging.getLogger(__name__)


@timeit
def get_client(config: Config) -> "duo_client.Admin":
    """
    Return a duo Admin client with the creds in the config object
    """
    client = duo_client.Admin(
        ikey=config.duo_api_key,
        skey=config.duo_api_secret,
        host=config.duo_api_hostname,
    )
    # Duo's library does not automatically respect the HTTP_PROXY env variable
    proxy_url = os.environ.get("HTTP_PROXY")
    if proxy_url:
        proxy_config = urlparse(proxy_url)
        headers = {}
        if proxy_config.username:
            proxy_auth_token = b64encode(
                f"{proxy_config.username}:{proxy_config.password}".encode(),
            ).decode("ascii")
            headers["Proxy-Authorization"] = f"Basic {proxy_auth_token}"
        client.set_proxy(
            host=proxy_config.hostname,
            port=proxy_config.port,
            headers=headers,
        )
    return client


@timeit
def start_duo_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of duo data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not all(
        [
            config.duo_api_key,
            config.duo_api_secret,
            config.duo_api_hostname,
        ],
    ):
        logger.info(
            "Duo import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    client = get_client(config)
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "DUO_API_HOSTNAME": config.duo_api_hostname,
    }

    sync_duo_api_host(
        neo4j_session,
        common_job_parameters,
    )
    sync_duo_tokens(
        client,
        neo4j_session,
        common_job_parameters,
    )
    sync_duo_web_authn_credentials(
        client,
        neo4j_session,
        common_job_parameters,
    )
    sync_duo_endpoints(
        client,
        neo4j_session,
        common_job_parameters,
    )
    sync_duo_phones(
        client,
        neo4j_session,
        common_job_parameters,
    )
    sync_duo_groups(
        client,
        neo4j_session,
        common_job_parameters,
    )
    sync_duo_users(
        client,
        neo4j_session,
        common_job_parameters,
    )
