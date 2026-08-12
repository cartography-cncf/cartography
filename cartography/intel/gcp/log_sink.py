# GCP Cloud Logging sinks
# https://cloud.google.com/logging/docs/reference/v2/rest/v2/sinks
from __future__ import annotations

import logging
from typing import Any

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import classify_gcp_http_error
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import summarize_gcp_http_error
from cartography.models.gcp.logging.log_sink import GCPFolderLogSinkSchema
from cartography.models.gcp.logging.log_sink import GCPOrgLogSinkSchema
from cartography.models.gcp.logging.log_sink import GCPProjectLogSinkSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_EXPECTED_SKIP_CATEGORIES = (
    "api_disabled",
    "billing_disabled",
    "forbidden",
    "not_found",
)


def _list_sinks(
    list_request: Any,
    list_next: Any,
    parent: str,
) -> list[dict] | None:
    sinks: list[dict] = []
    req = list_request(parent=parent)
    while req is not None:
        try:
            res = gcp_api_execute_with_retry(req)
        except HttpError as e:
            if classify_gcp_http_error(e) in _EXPECTED_SKIP_CATEGORIES:
                logger.warning(
                    "GCP: Unable to list Cloud Logging sinks for %s; skipping this scope. %s",
                    parent,
                    summarize_gcp_http_error(e),
                )
                return None
            raise
        sinks.extend(res.get("sinks", []))
        req = list_next(previous_request=req, previous_response=res)
    return sinks


@timeit
def get_org_log_sinks(client: Resource, org_resource_name: str) -> list[dict] | None:
    return _list_sinks(
        client.organizations().sinks().list,
        client.organizations().sinks().list_next,
        org_resource_name,
    )


@timeit
def get_folder_log_sinks(client: Resource, folder_name: str) -> list[dict] | None:
    return _list_sinks(
        client.folders().sinks().list,
        client.folders().sinks().list_next,
        folder_name,
    )


@timeit
def get_project_log_sinks(client: Resource, project_id: str) -> list[dict] | None:
    return _list_sinks(
        client.projects().sinks().list,
        client.projects().sinks().list_next,
        f"projects/{project_id}",
    )


def _sink_short_name(sink_name: str | None) -> str | None:
    if not sink_name:
        return None
    return sink_name.split("/sinks/")[-1]


@timeit
def transform_gcp_log_sinks(
    sinks: list[dict],
    parent_type: str,
    parent_id: str,
) -> list[dict]:
    transformed: list[dict] = []
    for sink in sinks:
        name = sink.get("name")
        if not name:
            continue
        transformed.append(
            {
                "id": name,
                "name": name,
                "sink_name": _sink_short_name(name),
                "destination": sink.get("destination"),
                "filter": sink.get("filter"),
                "description": sink.get("description"),
                "disabled": sink.get("disabled", False),
                "include_children": sink.get("includeChildren", False),
                "writer_identity": sink.get("writerIdentity"),
                "output_version_format": sink.get("outputVersionFormat"),
                "parent_type": parent_type,
                "parent_id": parent_id,
            },
        )
    return transformed


@timeit
def load_org_log_sinks(
    neo4j_session: neo4j.Session,
    sinks: list[dict],
    update_tag: int,
    org_resource_name: str,
) -> None:
    load(
        neo4j_session,
        GCPOrgLogSinkSchema(),
        sinks,
        lastupdated=update_tag,
        ORG_RESOURCE_NAME=org_resource_name,
    )


@timeit
def load_folder_log_sinks(
    neo4j_session: neo4j.Session,
    sinks: list[dict],
    update_tag: int,
    folder_id: str,
) -> None:
    load(
        neo4j_session,
        GCPFolderLogSinkSchema(),
        sinks,
        lastupdated=update_tag,
        FOLDER_ID=folder_id,
    )


@timeit
def load_project_log_sinks(
    neo4j_session: neo4j.Session,
    sinks: list[dict],
    update_tag: int,
    project_id: str,
) -> None:
    load(
        neo4j_session,
        GCPProjectLogSinkSchema(),
        sinks,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_org_log_sinks(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
    org_resource_name: str,
) -> None:
    params = common_job_parameters.copy()
    params["ORG_RESOURCE_NAME"] = org_resource_name
    GraphJob.from_node_schema(GCPOrgLogSinkSchema(), params).run(neo4j_session)


@timeit
def cleanup_folder_log_sinks(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
    folder_id: str,
) -> None:
    params = common_job_parameters.copy()
    params["FOLDER_ID"] = folder_id
    GraphJob.from_node_schema(GCPFolderLogSinkSchema(), params).run(neo4j_session)


@timeit
def cleanup_project_log_sinks(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
    project_id: str,
) -> None:
    params = common_job_parameters.copy()
    params["PROJECT_ID"] = project_id
    GraphJob.from_node_schema(GCPProjectLogSinkSchema(), params).run(neo4j_session)


@timeit
def sync_gcp_log_sinks(
    neo4j_session: neo4j.Session,
    client: Resource,
    org_resource_name: str,
    folders: list[dict],
    projects: list[dict],
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info("Syncing GCP Cloud Logging sinks for %s", org_resource_name)

    org_sinks_raw = get_org_log_sinks(client, org_resource_name)
    if org_sinks_raw is not None:
        org_sinks = transform_gcp_log_sinks(
            org_sinks_raw,
            "organization",
            org_resource_name,
        )
        load_org_log_sinks(neo4j_session, org_sinks, update_tag, org_resource_name)
        cleanup_org_log_sinks(neo4j_session, common_job_parameters, org_resource_name)

    for folder in folders:
        folder_name = folder.get("name")
        if not folder_name:
            continue
        folder_sinks_raw = get_folder_log_sinks(client, folder_name)
        if folder_sinks_raw is None:
            continue
        folder_sinks = transform_gcp_log_sinks(
            folder_sinks_raw,
            "folder",
            folder_name,
        )
        load_folder_log_sinks(neo4j_session, folder_sinks, update_tag, folder_name)
        cleanup_folder_log_sinks(neo4j_session, common_job_parameters, folder_name)

    for project in projects:
        project_id = project.get("projectId")
        if not project_id:
            continue
        project_parent = f"projects/{project_id}"
        project_sinks_raw = get_project_log_sinks(client, project_id)
        if project_sinks_raw is None:
            continue
        project_sinks = transform_gcp_log_sinks(
            project_sinks_raw,
            "project",
            project_parent,
        )
        load_project_log_sinks(neo4j_session, project_sinks, update_tag, project_id)
        cleanup_project_log_sinks(neo4j_session, common_job_parameters, project_id)
