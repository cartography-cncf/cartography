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
    _status = "success"
    _err: Dict = {}
    _result = None
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
        _result = round(time.perf_counter() - tic, 4)
    except Exception as e:
        _status = "error"
        _err = {"error_type": type(e).__name__, "error_message": str(e)}
        logger.warning(f"error to process service {service} org={organization_name} — {e}")
    finally:
        _elapsed = _result if _result is not None else round(time.perf_counter() - tic, 4)
        _ev: Dict = {
            "event": "github_service_timing",
            "org": organization_name,
            "service": service,
            "run_mode": "parallel",
            "duration_seconds": _elapsed,
            "status": _status,
        }
        if _err:
            _ev.update(_err)
        logger.info(json.dumps(_ev))
    return _result


@timeit
def sync_organization(neo4j_session: neo4j.Session, config: Config, auth_data: Dict, common_job_parameters: Dict) -> None:
    _org_tic = time.perf_counter()
    _service_timings: Dict = {}
    _failed_services: Dict = {}
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
                    _svc_tic = time.perf_counter()
                    _svc_status = "success"
                    _svc_err: Dict = {}
                    try:
                        logger.info(f"Processing {func_name} org={auth_data['name']}")
                        RESOURCE_FUNCTIONS[func_name](**sync_args)
                        _svc_elapsed = round(time.perf_counter() - _svc_tic, 4)
                        _service_timings[func_name] = _svc_elapsed
                    except Exception as e:
                        _svc_status = "error"
                        _svc_elapsed = round(time.perf_counter() - _svc_tic, 4)
                        _svc_err = {"error_type": type(e).__name__, "error_message": str(e)}
                        _failed_services[func_name] = str(e)
                        logger.warning(f"error to process service {func_name} - {e}")
                    finally:
                        _ev: Dict = {
                            "event": "github_service_timing",
                            "org": auth_data['name'],
                            "service": func_name,
                            "run_mode": "sequential",
                            "duration_seconds": _svc_elapsed,
                            "status": _svc_status,
                        }
                        if _svc_err:
                            _ev.update(_svc_err)
                        logger.info(json.dumps(_ev))
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
            try:
                with ThreadPoolExecutor(max_workers=min(8, len(RESOURCE_FUNCTIONS))) as executor:
                    futures: Dict = {}
                    for request in requested_syncs:
                        if request in RESOURCE_FUNCTIONS:
                            try:
                                futures[
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
                                    )
                                ] = request
                            except Exception as e:
                                logger.warning(f"error to append service {request} in futures - {e}")
                        else:
                            logger.warning(f'Github sync function "{request}" was specified but does not exist. Did you misspell it?')

                    for future in as_completed(futures):
                        svc_name = futures[future]
                        result = future.result()
                        if result is not None:
                            _service_timings[svc_name] = result
                        else:
                            _failed_services[svc_name] = "error"
            finally:
                shared_driver.close()

            # END - Parallel Run

    except exceptions.RequestException as e:
        logger.error("Could not complete request to the GitHub API: %s", e)
    logger.info(
        json.dumps({
            "event": "github_org_timing_summary",
            "org": auth_data.get('name'),
            "total_duration_seconds": round(time.perf_counter() - _org_tic, 4),
            "service_timings": _service_timings,
            "slowest_service": max(_service_timings, key=_service_timings.get) if _service_timings else None,
            "failed_services": _failed_services,
        }),
    )


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
