import logging
import os
from base64 import b64encode
from urllib.parse import urlparse

import duo_client
import neo4j

from cartography.intel.duo.api_host import sync_duo_api_host
from cartography.intel.duo.endpoints import sync_duo_endpoints
from cartography.intel.duo.groups import sync_duo_groups
from cartography.intel.duo.phones import sync as sync_duo_phones
from cartography.intel.duo.tokens import sync as sync_duo_tokens
from cartography.intel.duo.users import sync_duo_users
from cartography.intel.duo.web_authn_credentials import sync as sync_duo_web_authn_credentials
from cartography.settings import check_module_settings
from cartography.settings import settings
from cartography.util import timeit


logger = logging.getLogger(__name__)


@timeit
def get_client() -> duo_client.Admin:
    '''
    Return a duo Admin client with the creds in settings
    '''
    client = duo_client.Admin(
        ikey=settings.duo.api_key,
        skey=settings.duo.api_secret,
        host=settings.duo.api_hostname,
    )
    # Duo's library does not automatically respect the HTTP_PROXY env variable
    proxy_url = os.environ.get('HTTP_PROXY')
    if proxy_url:
        proxy_config = urlparse(proxy_url)
        headers = {}
        if proxy_config.username:
            proxy_auth_token = b64encode(f"{proxy_config.username}:{proxy_config.password}".encode()).decode('ascii')
            headers['Proxy-Authorization'] = f'Basic {proxy_auth_token}'
        client.set_proxy(
            host=proxy_config.hostname,
            port=proxy_config.port,
            headers=headers,
        )
    return client


@timeit
def start_duo_ingestion(neo4j_session: neo4j.Session) -> None:
    '''
    If this module is configured, perform ingestion of duo data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :return: None
    '''
    if not check_module_settings('Duo', ['api_key', 'api_secret', 'api_hostname']):
        return

    client = get_client()
    common_job_parameters = {
        "UPDATE_TAG": settings.common.update_tag,
        "DUO_API_HOSTNAME": settings.duo.api_hostname,
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
