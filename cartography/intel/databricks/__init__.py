import logging

import neo4j

import cartography.intel.databricks.artifact_allowlists
import cartography.intel.databricks.catalogs
import cartography.intel.databricks.cluster_policies
import cartography.intel.databricks.clusters
import cartography.intel.databricks.connections
import cartography.intel.databricks.external_locations
import cartography.intel.databricks.functions
import cartography.intel.databricks.grants
import cartography.intel.databricks.groups
import cartography.intel.databricks.instance_pools
import cartography.intel.databricks.ip_access_lists
import cartography.intel.databricks.metastores
import cartography.intel.databricks.online_tables
import cartography.intel.databricks.registered_models
import cartography.intel.databricks.schemas
import cartography.intel.databricks.secret_scopes
import cartography.intel.databricks.service_principals
import cartography.intel.databricks.storage_credentials
import cartography.intel.databricks.tables
import cartography.intel.databricks.tokens
import cartography.intel.databricks.users
import cartography.intel.databricks.vector_search
import cartography.intel.databricks.volumes
import cartography.intel.databricks.workspaces
from cartography.config import Config
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _cleanup_unity_catalog(
    neo4j_session: neo4j.Session,
    workspace_id: str,
    common_job_parameters: dict,
    clean_artifact_allowlists: bool = True,
) -> None:
    """Run every Unity Catalog cleanup, in reverse dependency order.

    Cleanup runs centrally (not inside each resource sync) and only after the
    whole UC sync succeeds. That keeps a mid-sync failure from deleting stale
    nodes on partial data, and deleting children before parents avoids
    detaching hierarchy edges or orphaning child nodes. Also invoked on the
    no-metastore path to purge UC data left over from a previous run.

    ``clean_artifact_allowlists`` is False when the allowlist fetch was
    incomplete (a 403 on a type), so its cleanup is skipped rather than deleting
    an allowlist node we could not re-read this run.
    """
    # Grants (edges) first, then leaf resources, then up the containment
    # hierarchy, and the metastore last.
    cartography.intel.databricks.grants.cleanup(
        neo4j_session, workspace_id, common_job_parameters["UPDATE_TAG"]
    )
    for module in (
        cartography.intel.databricks.online_tables,
        cartography.intel.databricks.vector_search,
        cartography.intel.databricks.registered_models,
        cartography.intel.databricks.functions,
        cartography.intel.databricks.tables,
        cartography.intel.databricks.volumes,
        cartography.intel.databricks.schemas,
        cartography.intel.databricks.catalogs,
        cartography.intel.databricks.external_locations,
        cartography.intel.databricks.storage_credentials,
        cartography.intel.databricks.connections,
    ):
        module.cleanup(neo4j_session, common_job_parameters)
    if clean_artifact_allowlists:
        cartography.intel.databricks.artifact_allowlists.cleanup(
            neo4j_session, common_job_parameters
        )
    cartography.intel.databricks.metastores.cleanup(
        neo4j_session, common_job_parameters
    )


@timeit
def start_databricks_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Databricks data. Otherwise warn and exit.

    Authentication supports either:
      - Personal Access Token (PAT) via ``--databricks-token-env-var``
      - OAuth M2M (workspace-level service principal) via
        ``--databricks-client-id`` + ``--databricks-client-secret-env-var``

    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.databricks_workspace_url:
        logger.info(
            "Databricks import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    has_token = bool(config.databricks_token)
    has_client_id = bool(config.databricks_client_id)
    has_client_secret = bool(config.databricks_client_secret)

    # OAuth requires *both* halves. A partial pair is an operator mistake
    # (typo in --databricks-client-secret-env-var, missing env variable) —
    # fail loudly so it cannot silently fall through to "not configured".
    if has_client_id ^ has_client_secret:
        raise ValueError(
            "Databricks OAuth M2M is partially configured: "
            "--databricks-client-id and --databricks-client-secret-env-var "
            "must be set together (and the env variable must be populated).",
        )

    if not has_token and not (has_client_id and has_client_secret):
        logger.info(
            "Databricks import is not configured - skipping this module. "
            "Set --databricks-token-env-var or "
            "--databricks-client-id + --databricks-client-secret-env-var.",
        )
        return

    api_client = DatabricksWorkspaceClient(
        host=config.databricks_workspace_url,
        token=config.databricks_token,
        client_id=config.databricks_client_id,
        client_secret=config.databricks_client_secret,
    )

    workspace = cartography.intel.databricks.workspaces.sync(
        neo4j_session,
        api_client,
        {"UPDATE_TAG": config.update_tag},
    )
    workspace_id = workspace["id"]
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "WORKSPACE_ID": workspace_id,
    }

    # Groups must be synced before users + service principals so the
    # User/SP -[:MEMBER_OF]-> Group MATCH lands the relationship.
    cartography.intel.databricks.groups.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.users.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.service_principals.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.tokens.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    # Policies + pools first so cluster -> policy / cluster -> pool edges
    # land on the cluster sync, not after-the-fact.
    cartography.intel.databricks.cluster_policies.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.instance_pools.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.clusters.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.secret_scopes.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.ip_access_lists.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    # Unity Catalog (data plane). The metastore anchors every UC object; when
    # the workspace has no metastore assigned, skip the whole UC surface.
    metastore_id = cartography.intel.databricks.metastores.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )
    if metastore_id is None:
        logger.info(
            "Databricks workspace %s has no Unity Catalog metastore assigned - "
            "purging any stale UC data and skipping the UC data-plane sync.",
            workspace_id,
        )
        _cleanup_unity_catalog(neo4j_session, workspace_id, common_job_parameters)
        return

    # Storage credentials + external locations first so catalogs / tables /
    # volumes can attach to them.
    cartography.intel.databricks.storage_credentials.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.external_locations.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    # Catalog -> schema -> table/volume hierarchy.
    catalogs = cartography.intel.databricks.catalogs.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    schemas = cartography.intel.databricks.schemas.sync(
        neo4j_session,
        api_client,
        workspace_id,
        catalogs,
        common_job_parameters,
    )

    cartography.intel.databricks.tables.sync(
        neo4j_session,
        api_client,
        workspace_id,
        schemas,
        common_job_parameters,
    )

    cartography.intel.databricks.volumes.sync(
        neo4j_session,
        api_client,
        workspace_id,
        schemas,
        common_job_parameters,
    )

    cartography.intel.databricks.functions.sync(
        neo4j_session,
        api_client,
        workspace_id,
        schemas,
        common_job_parameters,
    )

    cartography.intel.databricks.connections.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.registered_models.sync(
        neo4j_session,
        api_client,
        workspace_id,
        schemas,
        common_job_parameters,
    )

    # Online tables read managed tables from the graph, so run after tables.
    cartography.intel.databricks.online_tables.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.vector_search.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        common_job_parameters,
    )

    artifact_allowlists_complete = (
        cartography.intel.databricks.artifact_allowlists.sync(
            neo4j_session,
            api_client,
            workspace_id,
            metastore_id,
            common_job_parameters,
        )
    )

    # Grants last: materialises principal -> securable HAS_PRIVILEGE edges by
    # reading every securable already loaded for the workspace.
    cartography.intel.databricks.grants.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    # Cleanup runs once, centrally, only after every UC sync above succeeded, in
    # reverse dependency order (see _cleanup_unity_catalog). Artifact-allowlist
    # cleanup is gated: a 403-skipped type must not be deleted just because we
    # couldn't re-read it this run.
    _cleanup_unity_catalog(
        neo4j_session,
        workspace_id,
        common_job_parameters,
        clean_artifact_allowlists=artifact_allowlists_complete,
    )
