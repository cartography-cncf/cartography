import base64
import json
import logging
import os
import time
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from typing import Dict
from typing import List

import neo4j
from neo4j import GraphDatabase
from requests import exceptions

from . import organization
from .resources import RESOURCE_FUNCTIONS
from cartography.config import Config
from cartography.graph.session import Session
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def concurrent_execution(
    service: str, service_func: Any, config: Config, organization_name: str, url, refresh_token: str, common_job_parameters: Dict,
    shared_neo4j_driver=None,
):
    tic = time.perf_counter()
    logger.info(f"BEGIN processing for service: {service} org={organization_name}")
    try:
        neo4j_auth = (config.neo4j_user, config.neo4j_password)
        if shared_neo4j_driver is not None:
            neo4j_driver = shared_neo4j_driver
        else:
            neo4j_driver = GraphDatabase.driver(
                config.neo4j_uri,
                auth=neo4j_auth,
                max_connection_lifetime=config.neo4j_max_connection_lifetime,
            )
        service_func(
            Session(neo4j_driver), common_job_parameters, refresh_token, url, organization_name,
        )
        toc = time.perf_counter()
        logger.info(f"END processing for service: {service} org={organization_name} — {toc - tic:0.4f}s")
        return toc - tic
    except Exception as e:
        logger.warning(f"error to process service {service} org={organization_name} — {e}")
        return None


@timeit
def sync_organization(neo4j_session: neo4j.Session, config: Config, auth_data: Dict, common_job_parameters: Dict) -> None:
    _org_tic = time.perf_counter()
    try:
        logger.info("Syncing Github Organization: %s", common_job_parameters["ORGANIZATION_ID"])
        organization.sync(neo4j_session, auth_data["token"], auth_data["name"], auth_data["url"], common_job_parameters)

        requested_syncs: List[str] = list(RESOURCE_FUNCTIONS.keys())

        if os.environ.get("LOCAL_RUN", "0") == "1":
            # BEGIN - Sequential Run

            sync_args = {
                'neo4j_session': neo4j_session,
                'common_job_parameters': common_job_parameters,
                'github_api_key': auth_data['token'],
                'github_url': auth_data['url'],
                'organization': auth_data['name'],
            }

            for func_name in requested_syncs:
                if func_name in RESOURCE_FUNCTIONS:
                    try:
                        _svc_tic = time.perf_counter()
                        logger.info(f"Processing {func_name} org={auth_data['name']}")
                        RESOURCE_FUNCTIONS[func_name](**sync_args)
                        logger.info(f"Done {func_name} org={auth_data['name']} — {time.perf_counter() - _svc_tic:0.4f}s")
                    except Exception as e:
                        logger.warning(f"error to process service {func_name} - {e}")
                else:
                    logger.warning(f'GITHUB sync function "{func_name}" was specified but does not exist. Did you misspell it?')

            # END - Sequential Run

        else:
            # BEGIN - Parallel Run

            neo4j_auth = (config.neo4j_user, config.neo4j_password)
            shared_driver = GraphDatabase.driver(
                config.neo4j_uri,
                auth=neo4j_auth,
                max_connection_lifetime=config.neo4j_max_connection_lifetime,
            )
            # Process each service in parallel.
            try:
                with ThreadPoolExecutor(max_workers=min(8, len(RESOURCE_FUNCTIONS))) as executor:
                    futures = []
                    for request in requested_syncs:
                        if request in RESOURCE_FUNCTIONS:
                            try:
                                futures.append(
                                    executor.submit(
                                        concurrent_execution,
                                        request,
                                        RESOURCE_FUNCTIONS[request],
                                        config,
                                        auth_data['name'],
                                        auth_data['url'],
                                        auth_data['token'],
                                        common_job_parameters,
                                        shared_driver,
                                    ),
                                )
                            except Exception as e:
                                logger.warning(f"error to append service {request} in futures - {e}")
                        else:
                            logger.warning(f'Github sync function "{request}" was specified but does not exist. Did you misspell it?')

                    for future in as_completed(futures):
                        logger.info(f'Result from Future - Service Processing: {future.result()}')
            finally:
                shared_driver.close()

            # END - Parallel Run

    except exceptions.RequestException as e:
        logger.error("Could not complete request to the GitHub API: %s", e)
    logger.info(f"github org={auth_data.get('name')}: full sync done in {time.perf_counter() - _org_tic:0.4f}s")


@timeit
def start_github_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Github  data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.github_config:
        logger.info('GitHub import is not configured - skipping this module. See docs to configure.')
        return

    auth_tokens = json.loads(base64.b64decode(config.github_config).decode())
    common_job_parameters = {
        "WORKSPACE_ID": config.params['workspace']['id_string'],
        "UPDATE_TAG": config.update_tag,
        "ORGANIZATION_ID": config.params['workspace']['account_id'],
    }

    # run sync for the provided github tokens
    for auth_data in auth_tokens['organization']:
        sync_organization(neo4j_session, config, auth_data, common_job_parameters)

    return common_job_parameters
