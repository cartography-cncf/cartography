import logging
from typing import Any

import neo4j
import scaleway
from scaleway.mnq.v1beta1 import MnqV1Beta1SqsAPI
from scaleway.mnq.v1beta1 import SqsCredentials
from scaleway.mnq.v1beta1 import SqsInfo
from scaleway.mnq.v1beta1 import SqsInfoStatus
from scaleway_core.api import ScalewayException

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import DEFAULT_REGIONS
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.mnq.sqs import ScalewayMnqSqsCredentialSchema
from cartography.models.scaleway.mnq.sqs import ScalewayMnqSqsNamespaceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_PROJECT_UNREADABLE_STATUS_CODES = {403, 404}


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    projects_id: list[str],
    update_tag: int,
) -> None:
    sqs_info, credentials, readable_projects_id = get(client, projects_id)
    namespaces_by_project = transform_namespaces(sqs_info)
    credentials_by_project = transform_credentials(credentials)
    load_sqs(
        neo4j_session,
        namespaces_by_project,
        credentials_by_project,
        update_tag,
    )
    cleanup(neo4j_session, readable_projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    projects_id: list[str],
) -> tuple[list[SqsInfo], list[SqsCredentials], list[str]]:
    # SQS activation status and credentials are both fetched per project - there is
    # no organization-wide list endpoint. get_sqs_info() returns a single object
    # (not a list), so list_all_regions() doesn't apply here; fan out over regions
    # manually, mirroring its "unknown service" skip behavior for a scalar fetcher.
    api = MnqV1Beta1SqsAPI(client)
    sqs_info: list[SqsInfo] = []
    credentials: list[SqsCredentials] = []
    readable_projects_id: list[str] = []
    for project_id in projects_id:
        project_sqs_info: list[SqsInfo] = []
        project_credentials: list[SqsCredentials] = []
        for region in DEFAULT_REGIONS:
            try:
                info = api.get_sqs_info(project_id=project_id, region=region)
            except ScalewayException as exc:
                if "unknown service" in str(exc).lower():
                    logger.info(
                        "Scaleway SQS not available in region %s, skipping.",
                        region,
                    )
                    continue
                if _is_project_unreadable(exc):
                    logger.warning(
                        "Skipping Scaleway SQS for unreadable project %s: %s",
                        project_id,
                        exc,
                    )
                    break
                raise
            project_sqs_info.append(info)
            # list_sqs_credentials_all() 400s with "precondition_failed: SQS must
            # be enabled" for a region where the service exists but hasn't been
            # activated for this project - confirmed live. Only query credentials
            # where activation actually succeeded, rather than treating that as an
            # unexpected error.
            if info.status != SqsInfoStatus.ENABLED:
                continue
            try:
                project_credentials.extend(
                    api.list_sqs_credentials_all(project_id=project_id, region=region)
                )
            except ScalewayException as exc:
                if _is_project_unreadable(exc):
                    logger.warning(
                        "Skipping Scaleway SQS for unreadable project %s: %s",
                        project_id,
                        exc,
                    )
                    break
                raise
        else:
            sqs_info.extend(project_sqs_info)
            credentials.extend(project_credentials)
            readable_projects_id.append(project_id)
    return sqs_info, credentials, readable_projects_id


def _is_project_unreadable(exc: ScalewayException) -> bool:
    return exc.status_code in _PROJECT_UNREADABLE_STATUS_CODES


def transform_namespaces(
    sqs_info: list[SqsInfo],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for info in sqs_info:
        formatted = scaleway_obj_to_dict(info)
        formatted["id"] = f"{info.project_id}/{info.region}"
        result.setdefault(info.project_id, []).append(formatted)
    return result


def transform_credentials(
    credentials: list[SqsCredentials],
) -> dict[str, list[dict[str, Any]]]:
    # secret_key is the credential's actual bearer secret - Scaleway's list API
    # returns it inline alongside the credential's metadata, but it must never be
    # ingested. It's dropped here, before the row is ever built, rather than
    # filtered out of an already-built dict, so there's no path where it could
    # accidentally survive into load().
    result: dict[str, list[dict[str, Any]]] = {}
    for credential in credentials:
        formatted = scaleway_obj_to_dict(credential)
        formatted.pop("secret_key", None)
        formatted.pop("secret_checksum", None)
        permissions = formatted.pop("permissions", None) or {}
        formatted["can_publish"] = permissions.get("can_publish")
        formatted["can_receive"] = permissions.get("can_receive")
        formatted["can_manage"] = permissions.get("can_manage")
        formatted["namespace_id"] = f"{credential.project_id}/{credential.region}"
        result.setdefault(credential.project_id, []).append(formatted)
    return result


@timeit
def load_sqs(
    neo4j_session: neo4j.Session,
    namespaces_by_project: dict[str, list[dict[str, Any]]],
    credentials_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, namespaces in namespaces_by_project.items():
        load(
            neo4j_session,
            ScalewayMnqSqsNamespaceSchema(),
            namespaces,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
    for project_id, credentials in credentials_by_project.items():
        load(
            neo4j_session,
            ScalewayMnqSqsCredentialSchema(),
            credentials,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    projects_id: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    for project_id in projects_id:
        scoped_job_parameters = common_job_parameters.copy()
        scoped_job_parameters["PROJECT_ID"] = project_id
        # Credentials before the namespace itself.
        GraphJob.from_node_schema(
            ScalewayMnqSqsCredentialSchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            ScalewayMnqSqsNamespaceSchema(), scoped_job_parameters
        ).run(neo4j_session)
