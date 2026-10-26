import logging
from collections.abc import Collection
from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field

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
from cartography.intel.databricks._unity_catalog import (
    cleanup_legacy_workspace_resource_edges,
)
from cartography.intel.databricks._unity_catalog import cleanup_visibility
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.util import timeit

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DatabricksSyncResult:
    """What one ``start_databricks_ingestion`` run loaded, for ``cleanup_databricks``.

    ``partial_reads`` names the syncs that skipped part of their source (403/404)
    this run. Their cleanup is skipped so data that could not be re-read is not
    deleted as stale.
    """

    workspace_id: str
    account_id: str | None = None
    metastore_id: str | None = None
    partial_reads: frozenset[str] = field(default_factory=frozenset)


def _cleanup_metastore(
    neo4j_session: neo4j.Session,
    metastore_id: str,
    partial_reads: frozenset[str],
    update_tag: int,
) -> None:
    """Run every Unity Catalog object cleanup for one metastore.

    Children go before parents so no hierarchy edge is detached from a child
    that is about to be deleted anyway. Artifact allowlists and clean rooms are
    skipped when a workspace read them partially (a 403 on an allowlist type,
    external OpenSharing disabled): what could not be re-read is not proof of
    deletion.
    """
    common_job_parameters = {"UPDATE_TAG": update_tag, "METASTORE_ID": metastore_id}
    for module in (
        # Share nodes carry the SHARED_WITH edge, so purge them before recipients.
        cartography.intel.databricks.shares,
        cartography.intel.databricks.recipients,
        cartography.intel.databricks.providers,
        cartography.intel.databricks.online_tables,
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
    if "clean_rooms" not in partial_reads:
        cartography.intel.databricks.clean_rooms.cleanup(
            neo4j_session, common_job_parameters
        )
    if "artifact_allowlists" not in partial_reads:
        cartography.intel.databricks.artifact_allowlists.cleanup(
            neo4j_session, common_job_parameters
        )


def _cleanup_workspace(
    neo4j_session: neo4j.Session,
    result: DatabricksSyncResult,
    update_tag: int,
) -> None:
    """Run every workspace-scoped cleanup, in reverse load order."""
    workspace_id = result.workspace_id
    common_job_parameters = {"UPDATE_TAG": update_tag, "WORKSPACE_ID": workspace_id}
    if "permissions" not in result.partial_reads:
        cartography.intel.databricks.permissions.cleanup(
            neo4j_session, workspace_id, update_tag
        )
    # A workspace's links into its metastore are its own, so they are pruned
    # here even when the metastore's objects are not. This also purges them on
    # the no-metastore path once the workspace loses its assignment.
    if "grants" not in result.partial_reads:
        cartography.intel.databricks.grants.cleanup(
            neo4j_session, workspace_id, update_tag
        )
    cleanup_visibility(neo4j_session, workspace_id, update_tag)
    cartography.intel.databricks.metastores.cleanup_assignment(
        neo4j_session, workspace_id, update_tag
    )
    cleanup_legacy_workspace_resource_edges(neo4j_session, update_tag)
    for module in (
        cartography.intel.databricks.vector_search,
        cartography.intel.databricks.notebooks,
        cartography.intel.databricks.jobs,
        cartography.intel.databricks.pipelines,
        cartography.intel.databricks.git_credentials,
        cartography.intel.databricks.repos,
        cartography.intel.databricks.apps,
        cartography.intel.databricks.genie_spaces,
        cartography.intel.databricks.serving_endpoints,
        cartography.intel.databricks.dashboards,
        cartography.intel.databricks.alerts,
        cartography.intel.databricks.queries,
        cartography.intel.databricks.data_sources,
        cartography.intel.databricks.sql_warehouses,
        cartography.intel.databricks.ip_access_lists,
        cartography.intel.databricks.secret_scopes,
        cartography.intel.databricks.clusters,
        cartography.intel.databricks.instance_pools,
        cartography.intel.databricks.cluster_policies,
        cartography.intel.databricks.tokens,
        cartography.intel.databricks.service_principals,
        cartography.intel.databricks.users,
        cartography.intel.databricks.groups,
    ):
        module.cleanup(neo4j_session, common_job_parameters)


def _cleanup_account(
    neo4j_session: neo4j.Session,
    account_id: str,
    partial_reads: frozenset[str],
    update_tag: int,
) -> None:
    """Run every account-scoped cleanup, in reverse load order."""
    common_job_parameters = {"UPDATE_TAG": update_tag, "ACCOUNT_ID": account_id}
    for module in (
        cartography.intel.databricks.account_settings,
        cartography.intel.databricks.budgets,
        cartography.intel.databricks.log_delivery,
        cartography.intel.databricks.network_connectivity_configs,
        cartography.intel.databricks.encryption_keys,
        cartography.intel.databricks.vpc_endpoints,
        cartography.intel.databricks.private_access_settings,
        cartography.intel.databricks.network_configs,
        cartography.intel.databricks.storage_configs,
        cartography.intel.databricks.credential_configs,
    ):
        module.cleanup(neo4j_session, common_job_parameters)
    if "federation_policies" not in partial_reads:
        cartography.intel.databricks.federation_policies.cleanup(
            neo4j_session, common_job_parameters
        )
    if "workspace_assignments" not in partial_reads:
        cartography.intel.databricks.workspace_assignments.cleanup(
            neo4j_session, account_id, update_tag
        )
    cartography.intel.databricks.account_workspaces.cleanup(
        neo4j_session, account_id, update_tag
    )
    for module in (
        cartography.intel.databricks.account_service_principals,
        cartography.intel.databricks.account_users,
        cartography.intel.databricks.account_groups,
        cartography.intel.databricks.account,
    ):
        module.cleanup(neo4j_session, common_job_parameters)


@timeit
def cleanup_databricks(
    neo4j_session: neo4j.Session,
    update_tag: int,
    results: Iterable[DatabricksSyncResult],
    skip_metastore_ids: Collection[str] = (),
) -> None:
    """Run every Databricks cleanup for workspaces that loaded under ``update_tag``.

    ``start_databricks_ingestion`` calls this itself unless
    ``config.databricks_skip_cleanup`` is set. Orchestrators that sync several
    workspaces into one graph set that flag, run every workspace with the same
    update tag, then call this once with the results of the runs that succeeded.
    Deferring cleanup until every workspace has loaded keeps nodes that several
    workspaces share from being pruned by whichever workspace runs first, and
    leaves a failed workspace's data in place until a run of it succeeds.

    Unity Catalog objects belong to the metastore, so each metastore in
    ``results`` is cleaned once: an object goes only when no workspace listed it
    under ``update_tag``. Pass the metastore of every workspace whose run failed
    in ``skip_metastore_ids``; otherwise objects only that workspace could list
    are pruned.
    """
    account_partial_reads: dict[str, frozenset[str]] = {}
    metastore_partial_reads: dict[str, frozenset[str]] = {}
    for result in results:
        _cleanup_workspace(neo4j_session, result, update_tag)
        if result.account_id is not None:
            account_partial_reads[result.account_id] = (
                account_partial_reads.get(result.account_id, frozenset())
                | result.partial_reads
            )
        if result.metastore_id is not None:
            metastore_partial_reads[result.metastore_id] = (
                metastore_partial_reads.get(result.metastore_id, frozenset())
                | result.partial_reads
            )
    for metastore_id, partial_reads in metastore_partial_reads.items():
        if metastore_id not in skip_metastore_ids:
            _cleanup_metastore(neo4j_session, metastore_id, partial_reads, update_tag)
    for account_id, partial_reads in account_partial_reads.items():
        _cleanup_account(neo4j_session, account_id, partial_reads, update_tag)


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
) -> frozenset[str]:
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

    Returns the names of the syncs whose read was partial, for cleanup.
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
    partial_reads: set[str] = set()
    if not cartography.intel.databricks.workspace_assignments.sync(
        neo4j_session,
        account_client,
        account_id,
        workspace_node_ids,
        account_job_parameters,
    ):
        partial_reads.add("workspace_assignments")

    # Federation policies read the account service principals from the graph.
    if not cartography.intel.databricks.federation_policies.sync(
        neo4j_session, account_client, account_id, account_job_parameters
    ):
        partial_reads.add("federation_policies")

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
    return frozenset(partial_reads)


@timeit
def start_databricks_ingestion(
    neo4j_session: neo4j.Session, config: Config
) -> DatabricksSyncResult | None:
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

    With ``config.databricks_skip_cleanup`` set, only loads; the caller must run
    ``cleanup_databricks`` with the returned result once every workspace sharing
    the graph has loaded.

    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: What was loaded, or None when the module is not configured
    """
    if not config.databricks_workspace_url:
        logger.info(
            "Databricks import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return None

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
        return None

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
    partial_reads: set[str] = set()
    if account_client is not None and account_id is not None:
        partial_reads |= _sync_account_details(
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
            "skipping the UC data-plane sync; cleanup drops its links to any "
            "metastore it was assigned before.",
            workspace_id,
        )
        # Pipelines + jobs are workspace-level: sync them even without UC. The
        # pipeline -> catalog edge is skipped (no metastore), but nodes, run-as
        # and job-task -> pipeline edges still land.
        _sync_workflows(
            neo4j_session, api_client, workspace_id, None, common_job_parameters
        )
        # Object ACLs (principal -> workspace-object HAS_PERMISSION) are
        # workspace-level, so materialise them even without Unity Catalog. Runs
        # last so every ACL-bearing object (clusters, jobs, pipelines, secret
        # scopes, ...) is already in the graph.
        if not cartography.intel.databricks.permissions.sync(
            neo4j_session,
            api_client,
            workspace_id,
            common_job_parameters,
        ):
            partial_reads.add("permissions")
        return _finish(
            neo4j_session,
            config,
            DatabricksSyncResult(
                workspace_id, account_id, None, frozenset(partial_reads)
            ),
        )

    # Storage credentials + external locations first so catalogs / tables /
    # volumes can attach to them.
    cartography.intel.databricks.storage_credentials.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        common_job_parameters,
    )

    cartography.intel.databricks.external_locations.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        common_job_parameters,
    )

    # Catalog -> schema -> table/volume hierarchy.
    catalogs = cartography.intel.databricks.catalogs.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
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
        metastore_id,
        catalogs,
        common_job_parameters,
    )

    cartography.intel.databricks.tables.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        schemas,
        common_job_parameters,
    )

    cartography.intel.databricks.volumes.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        schemas,
        common_job_parameters,
    )

    cartography.intel.databricks.functions.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        schemas,
        common_job_parameters,
    )

    cartography.intel.databricks.connections.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        common_job_parameters,
    )

    cartography.intel.databricks.registered_models.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        schemas,
        common_job_parameters,
    )

    # Online tables read managed tables from the graph, so run after tables.
    cartography.intel.databricks.online_tables.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        common_job_parameters,
    )

    cartography.intel.databricks.vector_search.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        common_job_parameters,
    )

    if not cartography.intel.databricks.artifact_allowlists.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        common_job_parameters,
    ):
        partial_reads.add("artifact_allowlists")

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

    if not cartography.intel.databricks.clean_rooms.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        common_job_parameters,
    ):
        partial_reads.add("clean_rooms")

    cartography.intel.databricks.shares.sync(
        neo4j_session,
        api_client,
        workspace_id,
        metastore_id,
        common_job_parameters,
    )

    # Grants last: materialises principal -> securable HAS_PRIVILEGE edges by
    # reading every securable already loaded for the workspace.
    if not cartography.intel.databricks.grants.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    ):
        partial_reads.add("grants")

    # Object ACLs (principal -> workspace-object HAS_PERMISSION). Workspace-level
    # like grants, so it runs on both the UC and no-UC paths; here it runs after
    # every ACL-bearing object is loaded.
    if not cartography.intel.databricks.permissions.sync(
        neo4j_session,
        api_client,
        workspace_id,
        common_job_parameters,
    ):
        partial_reads.add("permissions")

    return _finish(
        neo4j_session,
        config,
        DatabricksSyncResult(
            workspace_id, account_id, metastore_id, frozenset(partial_reads)
        ),
    )


def _finish(
    neo4j_session: neo4j.Session, config: Config, result: DatabricksSyncResult
) -> DatabricksSyncResult:
    # Cleanup runs only after every load succeeded, so a mid-sync failure never
    # prunes on partial data.
    if not config.databricks_skip_cleanup:
        cleanup_databricks(neo4j_session, config.update_tag, [result])
    return result
