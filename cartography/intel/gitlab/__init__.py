import json
import logging
import time
from typing import Any
from typing import Dict
from typing import List

import neo4j
from requests import exceptions

import cartography.intel.gitlab.group
from .resources import RESOURCE_FUNCTIONS
from cartography.config import Config
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def concurrent_execution(
    service: str,
    service_func: Any,
    neo4j_session: neo4j.Session,
    group_name: str,
    access_token: str,
    common_job_parameters: Dict,
):
    tic = time.perf_counter()
    _status = "success"
    _err: Dict = {}
    try:
        service_func(
            neo4j_session,
            common_job_parameters["GITLAB_GROUP_ID"],
            access_token,
            common_job_parameters,
            group_name,
        )
    except Exception as e:
        _status = "error"
        _err = {"error_type": type(e).__name__, "error_message": str(e)}
        logger.warning(f"error processing service {service} group={group_name} — {e}")
    finally:
        _ev: Dict = {
            "event": "gitlab_service_timing",
            "group": group_name,
            "service": service,
            "run_mode": "parallel",
            "duration_seconds": round(time.perf_counter() - tic, 4),
            "status": _status,
        }
        if _err:
            _ev.update(_err)
        logger.info(json.dumps(_ev))


def _sync_one_gitlab_group(
    neo4j_session: neo4j.Session,
    group_name: str,
    hosted_domain: str,
    access_token: str,
    common_job_parameters: Dict[str, Any],
    config: Config,
):
    _group_tic = time.perf_counter()
    _service_timings: Dict = {}
    _failed_services: Dict = {}
    logger.info(f"Syncing Gitlab Group: {common_job_parameters['GITLAB_GROUP_ID']}")

    sync_order = ["projects", "members"]

    sync_args = {
        "neo4j_session": neo4j_session,
        "common_job_parameters": common_job_parameters,
        "group_id": common_job_parameters["GITLAB_GROUP_ID"],
        "group_name": group_name,
        "access_token": access_token,
        "hosted_domain": hosted_domain,
    }

    for func_name in sync_order:
        if func_name in RESOURCE_FUNCTIONS:
            _svc_tic = time.perf_counter()
            _svc_status = "success"
            _svc_err: Dict = {}
            try:
                logger.info(f"Processing {func_name} group={group_name}")
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
                    "event": "gitlab_service_timing",
                    "group": group_name,
                    "service": func_name,
                    "run_mode": "sequential",
                    "duration_seconds": _svc_elapsed,
                    "status": _svc_status,
                }
                if _svc_err:
                    _ev.update(_svc_err)
                logger.info(json.dumps(_ev))
        else:
            logger.warning(
                f'Gitlab sync function "{func_name}" was specified but is not available.',
            )

    logger.info(
        json.dumps({
            "event": "gitlab_group_timing_summary",
            "group": group_name,
            "total_duration_seconds": round(time.perf_counter() - _group_tic, 4),
            "service_timings": _service_timings,
            "slowest_service": max(_service_timings, key=_service_timings.get) if _service_timings else None,
            "failed_services": _failed_services,
        }),
    )
    return True


def _sync_multiple_groups(
    neo4j_session: neo4j.Session,
    hosted_domain: str,
    access_token: str,
    groups: List[Dict],
    common_job_parameters: Dict[str, Any],
    config: Config,
) -> bool:
    for group in groups:
        if common_job_parameters["GITLAB_GROUP_ID"] != group.get("full_path"):
            continue

        _sync_one_gitlab_group(
            neo4j_session,
            group.get("full_path"),
            hosted_domain,
            access_token,
            common_job_parameters,
            config,
        )
        run_cleanup_job(
            "gitlab_group_cleanup.json",
            neo4j_session,
            common_job_parameters,
        )

    return True


@timeit
def start_gitlab_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of gitlab  data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.gitlab_access_token:
        logger.info(
            "gitlab import is not configured - skipping this module. See docs to configure.",
        )
        return

    access_token = config.gitlab_access_token
    hosted_domain = config.gitlab_hosted_domain
    workspace_id = config.params.get("workspace", {}).get("id_string", "")
    group_id = config.params.get("workspace", {}).get("account_id", "")

    if not isinstance(group_id, str) or not group_id:
        logger.error("GitLab 'group_id' must be configured and be a non-empty string.")
        return

    common_job_parameters = {
        "WORKSPACE_ID": workspace_id,
        "GITLAB_GROUP_ID": group_id,
        "UPDATE_TAG": config.update_tag,
    }

    try:
        group_info = cartography.intel.gitlab.group.get_group(
            hosted_domain,
            access_token,
            common_job_parameters["GITLAB_GROUP_ID"],
        )

        if not group_info:
            logger.debug("No group info found, will list out groups to find the correct one.")

            all_groups = cartography.intel.gitlab.group.get_groups(hosted_domain, access_token)

            matching_groups = [
                grp for grp in all_groups if grp.get("full_path") == common_job_parameters["GITLAB_GROUP_ID"]
            ]
            if matching_groups:
                group_info = matching_groups[0]

                group_info_new = cartography.intel.gitlab.group.get_group(
                    hosted_domain,
                    access_token,
                    group_info.get("id"),
                )

            else:
                logger.warning(f"No matching group found for ID: {common_job_parameters['GITLAB_GROUP_ID']}")

        # TODO: namespace should always be for the root group only
        namespace_info = cartography.intel.gitlab.group.get_namespace(
            hosted_domain,
            access_token,
            common_job_parameters["GITLAB_GROUP_ID"],
        )

        # namespace_info = cartography.intel.gitlab.group.get_namespace(
        #     hosted_domain,
        #     access_token,
        #     group_info.get("id"),
        # )
        # logger.debug(f"Fetched namespace info with group id: {namespace_info}")

        if namespace_info:
            group_info["plan"] = namespace_info.get("plan")
            group_info["trial"] = namespace_info.get("trial")  # bool
            group_info["projects_count"] = namespace_info.get("projects_count")

        groups_list = [group_info]

        if not groups_list or not isinstance(groups_list, list) or not groups_list[0]:
            logger.error(
                f"No valid groups found for the id '{common_job_parameters['GITLAB_GROUP_ID']}'.",
            )
            return

        cartography.intel.gitlab.group.sync(
            neo4j_session,
            groups_list,
            hosted_domain,
            access_token,
            common_job_parameters,
        )

        _sync_multiple_groups(
            neo4j_session,
            hosted_domain,
            access_token,
            groups_list,
            common_job_parameters,
            config,
        )

    except exceptions.RequestException as e:
        logger.error("Could not complete request to the Gitlab API: %s", e)

    return common_job_parameters
