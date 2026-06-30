import logging
from typing import Any

import neo4j
import scaleway
from scaleway.secret.v1beta1 import Secret
from scaleway.secret.v1beta1 import SecretV1Beta1API
from scaleway.secret.v1beta1 import SecretVersion

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.secret.secret import ScalewaySecretSchema
from cartography.models.scaleway.secret.secret import ScalewaySecretVersionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    projects_id: list[str],
    update_tag: int,
) -> None:
    secrets, versions_by_secret = get(client, org_id)
    secrets_by_project, versions_by_project = transform_secrets(
        secrets, versions_by_secret
    )
    load_secrets(neo4j_session, secrets_by_project, versions_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> tuple[list[Secret], dict[str, list[SecretVersion]]]:
    api = SecretV1Beta1API(client)
    secrets = list_all_regions(
        api.list_secrets_all,
        organization_id=org_id,
        scheduled_for_deletion=False,
    )
    versions_by_secret: dict[str, list[SecretVersion]] = {}
    for secret in secrets:
        versions_by_secret[secret.id] = api.list_secret_versions_all(
            secret_id=secret.id, region=secret.region
        )
    return secrets, versions_by_secret


def transform_secrets(
    secrets: list[Secret],
    versions_by_secret: dict[str, list[SecretVersion]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    secrets_by_project: dict[str, list[dict[str, Any]]] = {}
    versions_by_project: dict[str, list[dict[str, Any]]] = {}
    project_by_secret = {secret.id: secret.project_id for secret in secrets}
    for secret in secrets:
        formatted_secret = scaleway_obj_to_dict(secret)
        secrets_by_project.setdefault(secret.project_id, []).append(formatted_secret)
        for version in versions_by_secret.get(secret.id, []):
            project_id = project_by_secret.get(version.secret_id)
            if project_id is None:
                logger.warning(
                    "Skipping Scaleway secret version revision=%s: unknown parent secret %s.",
                    version.revision,
                    version.secret_id,
                )
                continue
            formatted_version = scaleway_obj_to_dict(version)
            formatted_version["id"] = f"{version.secret_id}/{version.revision}"
            versions_by_project.setdefault(project_id, []).append(formatted_version)
    return secrets_by_project, versions_by_project


@timeit
def load_secrets(
    neo4j_session: neo4j.Session,
    secrets_by_project: dict[str, list[dict[str, Any]]],
    versions_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, secrets in secrets_by_project.items():
        logger.info(
            "Loading %d Scaleway Secrets in project '%s' into Neo4j.",
            len(secrets),
            project_id,
        )
        load(
            neo4j_session,
            ScalewaySecretSchema(),
            secrets,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
    for project_id, versions in versions_by_project.items():
        load(
            neo4j_session,
            ScalewaySecretVersionSchema(),
            versions,
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
        # Versions before secrets.
        GraphJob.from_node_schema(
            ScalewaySecretVersionSchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_node_schema(ScalewaySecretSchema(), scoped_job_parameters).run(
            neo4j_session
        )
