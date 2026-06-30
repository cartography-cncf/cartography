import logging

import neo4j

import cartography.intel.databricks.groups
import cartography.intel.databricks.service_principals
import cartography.intel.databricks.tokens
import cartography.intel.databricks.users
import cartography.intel.databricks.workspaces
from cartography.config import Config
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.util import timeit

logger = logging.getLogger(__name__)


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
