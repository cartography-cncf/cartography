# GCP IAM audit configs
# https://cloud.google.com/resource-manager/reference/rest/v3/Policy#auditconfig
from __future__ import annotations

import json
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
from cartography.models.gcp.audit_config import GCPFolderAuditConfigSchema
from cartography.models.gcp.audit_config import GCPOrgAuditConfigSchema
from cartography.models.gcp.audit_config import GCPProjectAuditConfigSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_EXPECTED_SKIP_CATEGORIES = (
    "api_disabled",
    "billing_disabled",
    "forbidden",
    "not_found",
)
_POLICY_VERSION_BODY = {"options": {"requestedPolicyVersion": 3}}


def _get_audit_configs(client_get_iam_policy: Any, resource: str) -> list[dict] | None:
    try:
        req = client_get_iam_policy(resource=resource, body=_POLICY_VERSION_BODY)
        res = gcp_api_execute_with_retry(req)
        return res.get("auditConfigs", [])
    except HttpError as e:
        if classify_gcp_http_error(e) in _EXPECTED_SKIP_CATEGORIES:
            logger.warning(
                "GCP: Unable to get IAM audit configs for %s; skipping this scope. %s",
                resource,
                summarize_gcp_http_error(e),
            )
            return None
        raise


@timeit
def get_org_audit_config(client: Resource, org_resource_name: str) -> list[dict] | None:
    return _get_audit_configs(client.organizations().getIamPolicy, org_resource_name)


@timeit
def get_folder_audit_config(client: Resource, folder_name: str) -> list[dict] | None:
    return _get_audit_configs(client.folders().getIamPolicy, folder_name)


@timeit
def get_project_audit_config(
    client: Resource,
    project_id: str,
    project_number: str | None = None,
) -> list[dict] | None:
    try:
        return _get_audit_configs(
            client.projects().getIamPolicy, f"projects/{project_id}"
        )
    except HttpError as e:
        if classify_gcp_http_error(e) == "invalid" and project_number:
            return _get_audit_configs(
                client.projects().getIamPolicy,
                f"projects/{project_number}",
            )
        raise


@timeit
def transform_gcp_audit_configs(
    audit_configs: list[dict],
    parent_type: str,
    parent_id: str,
) -> list[dict]:
    transformed: list[dict] = []
    for audit_config in audit_configs:
        service = audit_config["service"]
        audit_log_configs = audit_config.get("auditLogConfigs", []) or []
        log_types = {config["logType"] for config in audit_log_configs}
        transformed.append(
            {
                "id": f"{parent_id}/auditConfigs/{service}",
                "parent_type": parent_type,
                "parent_id": parent_id,
                "service": service,
                "has_admin_read": "ADMIN_READ" in log_types,
                "has_data_read": "DATA_READ" in log_types,
                "has_data_write": "DATA_WRITE" in log_types,
                "audit_log_configs_json": json.dumps(audit_log_configs),
            },
        )
    return transformed


@timeit
def load_org_audit_configs(
    neo4j_session: neo4j.Session,
    audit_configs: list[dict],
    update_tag: int,
    org_resource_name: str,
) -> None:
    load(
        neo4j_session,
        GCPOrgAuditConfigSchema(),
        audit_configs,
        lastupdated=update_tag,
        ORG_RESOURCE_NAME=org_resource_name,
    )


@timeit
def load_folder_audit_configs(
    neo4j_session: neo4j.Session,
    audit_configs: list[dict],
    update_tag: int,
    folder_id: str,
) -> None:
    load(
        neo4j_session,
        GCPFolderAuditConfigSchema(),
        audit_configs,
        lastupdated=update_tag,
        FOLDER_ID=folder_id,
    )


@timeit
def load_project_audit_configs(
    neo4j_session: neo4j.Session,
    audit_configs: list[dict],
    update_tag: int,
    project_id: str,
) -> None:
    load(
        neo4j_session,
        GCPProjectAuditConfigSchema(),
        audit_configs,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_org_audit_configs(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
    org_resource_name: str,
) -> None:
    params = common_job_parameters.copy()
    params["ORG_RESOURCE_NAME"] = org_resource_name
    GraphJob.from_node_schema(GCPOrgAuditConfigSchema(), params).run(neo4j_session)


@timeit
def cleanup_folder_audit_configs(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
    folder_id: str,
) -> None:
    params = common_job_parameters.copy()
    params["FOLDER_ID"] = folder_id
    GraphJob.from_node_schema(GCPFolderAuditConfigSchema(), params).run(neo4j_session)


@timeit
def cleanup_project_audit_configs(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
    project_id: str,
) -> None:
    params = common_job_parameters.copy()
    params["PROJECT_ID"] = project_id
    GraphJob.from_node_schema(GCPProjectAuditConfigSchema(), params).run(neo4j_session)


@timeit
def sync_gcp_audit_configs(
    neo4j_session: neo4j.Session,
    client: Resource,
    org_resource_name: str,
    folders: list[dict],
    projects: list[dict],
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info("Syncing GCP IAM audit configs for %s", org_resource_name)

    org_configs_raw = get_org_audit_config(client, org_resource_name)
    if org_configs_raw is not None:
        org_configs = transform_gcp_audit_configs(
            org_configs_raw,
            "organization",
            org_resource_name,
        )
        load_org_audit_configs(
            neo4j_session, org_configs, update_tag, org_resource_name
        )
        cleanup_org_audit_configs(
            neo4j_session, common_job_parameters, org_resource_name
        )

    for folder in folders:
        folder_name = folder.get("name")
        if not folder_name:
            continue
        folder_configs_raw = get_folder_audit_config(client, folder_name)
        if folder_configs_raw is None:
            continue
        folder_configs = transform_gcp_audit_configs(
            folder_configs_raw,
            "folder",
            folder_name,
        )
        load_folder_audit_configs(
            neo4j_session, folder_configs, update_tag, folder_name
        )
        cleanup_folder_audit_configs(neo4j_session, common_job_parameters, folder_name)

    for project in projects:
        project_id = project.get("projectId")
        if not project_id:
            continue
        project_parent = f"projects/{project_id}"
        project_configs_raw = get_project_audit_config(
            client,
            project_id,
            project.get("projectNumber"),
        )
        if project_configs_raw is None:
            continue
        project_configs = transform_gcp_audit_configs(
            project_configs_raw,
            "project",
            project_parent,
        )
        load_project_audit_configs(
            neo4j_session, project_configs, update_tag, project_id
        )
        cleanup_project_audit_configs(neo4j_session, common_job_parameters, project_id)
