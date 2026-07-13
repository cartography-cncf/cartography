import logging

import neo4j

import cartography.intel.databricks.account
import cartography.intel.databricks.account_groups
import cartography.intel.databricks.account_service_principals
import cartography.intel.databricks.account_settings
import cartography.intel.databricks.account_users
import cartography.intel.databricks.account_workspaces
import cartography.intel.databricks.alerts
import cartography.intel.databricks.apps
import cartography.intel.databricks.artifact_allowlists
import cartography.intel.databricks.budgets
import cartography.intel.databricks.catalogs
import cartography.intel.databricks.clean_rooms
import cartography.intel.databricks.cluster_policies
import cartography.intel.databricks.clusters
import cartography.intel.databricks.connections
import cartography.intel.databricks.credential_configs
import cartography.intel.databricks.dashboards
import cartography.intel.databricks.data_sources
import cartography.intel.databricks.encryption_keys
import cartography.intel.databricks.external_locations
import cartography.intel.databricks.federation_policies
import cartography.intel.databricks.functions
import cartography.intel.databricks.genie_spaces
import cartography.intel.databricks.git_credentials
import cartography.intel.databricks.grants
import cartography.intel.databricks.groups
import cartography.intel.databricks.instance_pools
import cartography.intel.databricks.ip_access_lists
import cartography.intel.databricks.jobs
import cartography.intel.databricks.log_delivery
import cartography.intel.databricks.metastores
import cartography.intel.databricks.network_configs
import cartography.intel.databricks.network_connectivity_configs
import cartography.intel.databricks.notebooks
import cartography.intel.databricks.online_tables
import cartography.intel.databricks.permissions
import cartography.intel.databricks.pipelines
import cartography.intel.databricks.private_access_settings
import cartography.intel.databricks.providers
import cartography.intel.databricks.queries
import cartography.intel.databricks.recipients
import cartography.intel.databricks.registered_models
import cartography.intel.databricks.repos
import cartography.intel.databricks.schemas
import cartography.intel.databricks.secret_scopes
import cartography.intel.databricks.service_principals
import cartography.intel.databricks.serving_endpoints
import cartography.intel.databricks.shares
import cartography.intel.databricks.sql_warehouses
import cartography.intel.databricks.storage_configs
import cartography.intel.databricks.storage_credentials
import cartography.intel.databricks.tables
import cartography.intel.databricks.tokens
import cartography.intel.databricks.users
import cartography.intel.databricks.vector_search
import cartography.intel.databricks.volumes
import cartography.intel.databricks.vpc_endpoints
import cartography.intel.databricks.workspace_assignments
import cartography.intel.databricks.workspaces
from cartography.config import Config
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _cleanup_unity_catalog(
    neo4j_session: neo4j.Session,
    workspace_id: str,
    common_job_parameters: dict,
    clean_artifact_allowlists: bool = True,
    clean_clean_rooms: bool = True,
) -> None:
    """Run every Unity Catalog cleanup, in reverse dependency order.

    Cleanup runs centrally (not inside each resource sync) and only after the
    whole UC sync succeeds. That keeps a mid-sync failure from deleting stale
    nodes on partial data, and deleting children before parents avoids
    detaching hierarchy edges or orphaning child nodes. Also invoked on the
    no-metastore path to purge UC data left over from a previous run.

    ``clean_artifact_allowlists`` is False when the allowlist fetch was
    incomplete (a 403 on a type), so its cleanup is skipped rather than deleting
    an allowlist node we could not re-read this run. ``clean_clean_rooms`` is
    False when the clean-rooms listing was skipped (external OpenSharing
    disabled), for the same reason.
    """
    # Grants (edges) first, then leaf resources, then up the containment
    # hierarchy, and the metastore last.
    cartography.intel.databricks.grants.cleanup(
        neo4j_session, workspace_id, common_job_parameters["UPDATE_TAG"]
    )
    for module in (
        # Delta Sharing: share nodes carry the SHARED_WITH edge, so purge them
        # before recipients. All are metastore-scoped leaves cleaned centrally
        # (like the rest of UC) so the no-metastore path purges them too.
        cartography.intel.databricks.shares,
        cartography.intel.databricks.recipients,
        cartography.intel.databricks.providers,
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
    if clean_clean_rooms:
        cartography.intel.databricks.clean_rooms.cleanup(
            neo4j_session, common_job_parameters
        )
    if clean_artifact_allowlists:
        cartography.intel.databricks.artifact_allowlists.cleanup(
            neo4j_session, common_job_parameters
        )
    cartography.intel.databricks.metastores.cleanup(
        neo4j_session, common_job_parameters
    )


def _sync_workflows(
    neo4j_session: neo4j.Session,
    api_client: DatabricksWorkspaceClient,
    workspace_id: str,
    metastore_id: str | None,
    common_job_parameters: dict,
) -> None:
    """Sync pipelines then jobs.

    Ordered so that a job task's RUNS_PIPELINE edge lands (pipelines first) and
    a pipeline's PUBLISHES_TO edge lands (catalogs already synced by the caller
    when a metastore is present). Both are workspace-level, so this runs whether
    or not the workspace has Unity Catalog.
    """
    cartography.intel.databricks.pipelines.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        common_job_parameters,
    )
    cartography.intel.databricks.jobs.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )
    # Notebooks are derived from the task notebook_paths just loaded, so this
    # runs last and needs no api_client.
    cartography.intel.databricks.notebooks.sync(
        neo4j_session,
        workspace_id,
        common_job_parameters,
    )


def _sync_account_details(
    neo4j_session: neo4j.Session,
    account_client: DatabricksAccountClient,
    account_id: str,
    update_tag: int,
) -> None:
    """Sync the account-level surface (AWS / GCP) below the account node.

    Covers the Databricks Account API, which does not exist on Azure: account
    SCIM (groups first so member edges land, then users + service principals),
    the account's workspaces (so workspace permission assignments can key off
    the numeric workspace id), account-to-workspace permission assignments,
    federation policies, and the workspace cloud configurations (credentials /
    storage / network / encryption / ...).

    Runs AFTER the workspace-API workspace sync so that account_workspaces
    enriches (rather than gets clobbered by) the DatabricksWorkspace node. The
    ``DatabricksAccount`` node itself is synced earlier, before the workspace, so
    the workspace's account RESOURCE edge can form. Each account resource is
    scoped to ``DatabricksAccount`` for cleanup, so ``ACCOUNT_ID`` rides in the
    common job parameters.
    """
    account_job_parameters = {"UPDATE_TAG": update_tag, "ACCOUNT_ID": account_id}

    cartography.intel.databricks.account_groups.sync(
        neo4j_session, account_client, account_id, account_job_parameters
    )
    cartography.intel.databricks.account_users.sync(
        neo4j_session, account_client, account_id, account_job_parameters
    )
    cartography.intel.databricks.account_service_principals.sync(
        neo4j_session, account_client, account_id, account_job_parameters
    )

    # Account workspaces create/enrich the DatabricksWorkspace nodes (numeric
    # workspace id + account RESOURCE edge) and return the numeric-id -> node-id
    # map the permission-assignment sweep needs.
    workspace_node_ids = cartography.intel.databricks.account_workspaces.sync(
        neo4j_session, account_client, account_id, account_job_parameters
    )
    cartography.intel.databricks.workspace_assignments.sync(
        neo4j_session,
        account_client,
        account_id,
        workspace_node_ids,
        account_job_parameters,
    )

    # Federation policies read the account service principals from the graph.
    cartography.intel.databricks.federation_policies.sync(
        neo4j_session, account_client, account_id, account_job_parameters
    )

    # Workspace cloud configurations. Each links back to the AWS / GCP nodes
    # already in the graph where they exist.
    for module in (
        cartography.intel.databricks.credential_configs,
        cartography.intel.databricks.storage_configs,
        cartography.intel.databricks.network_configs,
        cartography.intel.databricks.private_access_settings,
        cartography.intel.databricks.vpc_endpoints,
        cartography.intel.databricks.encryption_keys,
        cartography.intel.databricks.network_connectivity_configs,
        cartography.intel.databricks.log_delivery,
        cartography.intel.databricks.budgets,
        cartography.intel.databricks.account_settings,
    ):
        module.sync(neo4j_session, account_client, account_id, account_job_parameters)


@timeit
def start_databricks_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Databricks data. Otherwise warn and exit.

    Workspace authentication supports either:
      - Personal Access Token (PAT) via ``--databricks-token-env-var``
      - OAuth M2M (workspace-level service principal) via
        ``--databricks-client-id`` + ``--databricks-client-secret-env-var``

    The account-level surface (AWS / GCP only) is additionally enabled by
    ``--databricks-account-id`` + ``--databricks-account-client-id`` +
    ``--databricks-account-client-secret-env-var``; when unset the module runs
    workspace-only.

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

    # Account API (AWS / GCP only; Azure has no Databricks account API). All
    # three flags are required together: OAuth M2M against the account host
    # needs the account id + a client id/secret pair. A partial set is an
    # operator mistake, so fail loudly rather than silently skipping the
    # account-level surface. When none are set, the workspace-only path runs
    # unchanged.
    has_account_id = bool(config.databricks_account_id)
    has_account_client_id = bool(config.databricks_account_client_id)
    has_account_client_secret = bool(config.databricks_account_client_secret)
    account_configured = (
        has_account_id or has_account_client_id or has_account_client_secret
    )
    if account_configured and not (
        has_account_id and has_account_client_id and has_account_client_secret
    ):
        raise ValueError(
            "Databricks account API is partially configured: "
            "--databricks-account-id, --databricks-account-client-id and "
            "--databricks-account-client-secret-env-var must be set together.",
        )

    # Sync the DatabricksAccount node first (before the workspace) so the
    # workspace's account RESOURCE edge can match it. The rest of the account
    # surface runs after the workspace sync below, so account_workspaces enriches
    # the DatabricksWorkspace node instead of being clobbered by the workspace
    # sync (which does not carry the numeric id / deployment fields).
    account_id: str | None = None
    account_client: DatabricksAccountClient | None = None
    if account_configured:
        account_client = DatabricksAccountClient(
            host=config.databricks_account_host,
            account_id=config.databricks_account_id,
            client_id=config.databricks_account_client_id,
            client_secret=config.databricks_account_client_secret,
        )
        account_id = cartography.intel.databricks.account.sync(
            neo4j_session, account_client, {"UPDATE_TAG": config.update_tag}
        )

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
        account_id,
    )
    workspace_id = workspace["id"]
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "WORKSPACE_ID": workspace_id,
    }

    # Account-level surface (SCIM, workspaces, assignments, federation, cloud
    # configs). Runs after the workspace sync so account_workspaces enriches the
    # existing workspace node rather than being overwritten by it.
    if account_client is not None and account_id is not None:
        _sync_account_details(
            neo4j_session, account_client, account_id, config.update_tag
        )

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

    # SQL workloads. Warehouses first so data sources / queries / dashboards /
    # job tasks can attach to them; queries before alerts (alerts monitor a
    # query). None of these need Unity Catalog.
    cartography.intel.databricks.sql_warehouses.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.data_sources.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.queries.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.alerts.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.dashboards.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    # ML serving + apps + content. Genie spaces bind to a warehouse synced
    # above; the rest are independent workspace-level surfaces.
    cartography.intel.databricks.serving_endpoints.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.genie_spaces.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.apps.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.repos.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    cartography.intel.databricks.git_credentials.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    # Unity Catalog (data plane). The metastore anchors every UC object; when
    # the workspace has no metastore assigned, skip the whole UC surface but
    # still sync workspace-level pipelines + jobs below.
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
        # Pipelines + jobs are workspace-level: sync them even without UC. The
        # pipeline -> catalog edge is skipped (no metastore), but nodes, run-as
        # and job-task -> pipeline edges still land.
        _sync_workflows(
            neo4j_session, api_client, workspace_id, None, common_job_parameters
        )
        # Object ACLs (principal -> workspace-object HAS_PERMISSION) are
        # workspace-level, so materialise them even without Unity Catalog. Runs
        # last so every ACL-bearing object (clusters, jobs, pipelines, secret
        # scopes, ...) is already in the graph. Self-contained: it runs its own
        # scoped MatchLink cleanup.
        cartography.intel.databricks.permissions.sync(
            neo4j_session,
            api_client,
            workspace_id,
            common_job_parameters,
        )
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

    # Pipelines + jobs after catalogs so pipeline -> catalog and job-task ->
    # pipeline edges resolve against nodes already in the graph.
    _sync_workflows(
        neo4j_session, api_client, workspace_id, metastore_id, common_job_parameters
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

    # Delta Sharing. Recipients + providers before shares so the share ->
    # recipient SHARED_WITH edge resolves against recipient nodes already loaded.
    cartography.intel.databricks.recipients.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        common_job_parameters,
    )

    cartography.intel.databricks.providers.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        common_job_parameters,
    )

    clean_rooms_complete = cartography.intel.databricks.clean_rooms.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        common_job_parameters,
    )

    cartography.intel.databricks.shares.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        common_job_parameters,
    )

    # Grants last: materialises principal -> securable HAS_PRIVILEGE edges by
    # reading every securable already loaded for the workspace.
    cartography.intel.databricks.grants.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    )

    # Object ACLs (principal -> workspace-object HAS_PERMISSION). Workspace-level
    # like grants, so it runs on both the UC and no-UC paths; here it runs after
    # every ACL-bearing object is loaded. Self-contained: runs its own scoped
    # MatchLink cleanup, so it is not part of _cleanup_unity_catalog.
    cartography.intel.databricks.permissions.sync(
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
        clean_clean_rooms=clean_rooms_complete,
    )
