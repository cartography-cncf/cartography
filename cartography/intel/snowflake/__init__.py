import logging
from typing import Any

import neo4j

from cartography.config import Config
from cartography.intel.snowflake import access_tokens
from cartography.intel.snowflake import account
from cartography.intel.snowflake import account_grants
from cartography.intel.snowflake import account_parameters
from cartography.intel.snowflake import account_usage
from cartography.intel.snowflake import alerts
from cartography.intel.snowflake import api_integrations
from cartography.intel.snowflake import artifact_repositories
from cartography.intel.snowflake import authentication_policies
from cartography.intel.snowflake import catalog_integrations
from cartography.intel.snowflake import compute_pools
from cartography.intel.snowflake import cortex_search_services
from cartography.intel.snowflake import credentials
from cartography.intel.snowflake import data_policies
from cartography.intel.snowflake import database_roles
from cartography.intel.snowflake import databases
from cartography.intel.snowflake import dynamic_tables
from cartography.intel.snowflake import event_tables
from cartography.intel.snowflake import external_access_integrations
from cartography.intel.snowflake import external_tables
from cartography.intel.snowflake import external_volumes
from cartography.intel.snowflake import file_formats
from cartography.intel.snowflake import functions
from cartography.intel.snowflake import grants
from cartography.intel.snowflake import iceberg_tables
from cartography.intel.snowflake import image_repositories
from cartography.intel.snowflake import listings
from cartography.intel.snowflake import materialized_views
from cartography.intel.snowflake import network_policies
from cartography.intel.snowflake import network_rules
from cartography.intel.snowflake import notebooks
from cartography.intel.snowflake import notification_integrations
from cartography.intel.snowflake import password_policies
from cartography.intel.snowflake import pipes
from cartography.intel.snowflake import policy_references
from cartography.intel.snowflake import procedures
from cartography.intel.snowflake import replication_groups
from cartography.intel.snowflake import resource_monitors
from cartography.intel.snowflake import roles
from cartography.intel.snowflake import schemas
from cartography.intel.snowflake import secrets
from cartography.intel.snowflake import security_integrations
from cartography.intel.snowflake import sequences
from cartography.intel.snowflake import services
from cartography.intel.snowflake import session_policies
from cartography.intel.snowflake import shares
from cartography.intel.snowflake import stages
from cartography.intel.snowflake import storage_integrations
from cartography.intel.snowflake import streamlits
from cartography.intel.snowflake import streams
from cartography.intel.snowflake import tables
from cartography.intel.snowflake import tags
from cartography.intel.snowflake import tasks
from cartography.intel.snowflake import users
from cartography.intel.snowflake import views
from cartography.intel.snowflake import warehouses
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Schema-scoped surfaces, in the order their edges resolve. Secrets precede the
# external access integrations that reference them, tables precede the streams and
# search services that read from them, and stages and file formats precede the
# external tables built on top of them.
_SCHEMA_LEVEL_MODULES = (
    tags,
    file_formats,
    stages,
    secrets,
    sequences,
    tables,
    views,
    materialized_views,
    external_tables,
    event_tables,
    iceberg_tables,
    dynamic_tables,
    streams,
    password_policies,
    session_policies,
    authentication_policies,
    data_policies,
)

# Schema-scoped workloads. These run after the account-level integrations so their
# USES_INTEGRATION and USES_WAREHOUSE edges resolve, and after image repositories
# so a service container can attach to its image.
_WORKLOAD_MODULES = (
    functions,
    procedures,
    pipes,
    tasks,
    alerts,
    cortex_search_services,
    notebooks,
    streamlits,
    artifact_repositories,
    image_repositories,
    services,
)

# Account-level integrations. Storage integrations precede stages (which reference
# them), and security integrations need the roles they run as.
_INTEGRATION_MODULES = (
    storage_integrations,
    api_integrations,
    catalog_integrations,
    notification_integrations,
    security_integrations,
)


def _module_name(module: Any) -> str:
    """Return a module's short name, which is the key used to track completeness."""
    return module.__name__.rsplit(".", 1)[-1]


# Every surface whose contents are enumerated by walking the database or schema list.
# If either list is truncated, none of these can be trusted to be complete, so all of
# them must have their cleanup skipped together. Derived from the module tuples rather
# than written out, so adding a surface cannot silently omit it from this guarantee.
_SCHEMA_SCOPED_SURFACES = frozenset(
    _module_name(module)
    for module in (
        *_SCHEMA_LEVEL_MODULES,
        *_WORKLOAD_MODULES,
        network_rules,
        database_roles,
        schemas,
    )
)


def databases_and_schemas_complete(incomplete: set[str]) -> bool:
    """Whether the database and schema walks both covered everything."""
    return not ({"databases", "schemas"} & incomplete)


# Cleanup order is the reverse of ingestion: leaves first, then up the containment
# hierarchy, so nothing is deleted while a child still hangs off it.
_CLEANUP_ORDER = (
    policy_references,
    listings,
    shares,
    replication_groups,
    *reversed(_WORKLOAD_MODULES),
    external_access_integrations,
    *reversed(_SCHEMA_LEVEL_MODULES),
    schemas,
    database_roles,
    databases,
    external_volumes,
    *reversed(_INTEGRATION_MODULES),
    compute_pools,
    warehouses,
    resource_monitors,
    access_tokens,
    credentials,
    users,
    roles,
    network_policies,
    network_rules,
    account_parameters,
    account,
)


def _build_client(config: Config) -> SnowflakeClient:
    """Validate the credential configuration and build the API client.

    A partially-configured credential is an operator mistake (a typo in an env var
    name, an unpopulated variable), so it fails loudly rather than silently
    falling through to "not configured".
    """
    has_pat = bool(config.snowflake_pat)
    has_private_key = bool(config.snowflake_private_key)

    if has_pat and has_private_key:
        raise ValueError(
            "Snowflake authentication is ambiguously configured: set exactly one "
            "of --snowflake-pat-env-var or --snowflake-private-key-env-var.",
        )
    if config.snowflake_private_key_passphrase and not has_private_key:
        raise ValueError(
            "Snowflake key-pair authentication is partially configured: a private "
            "key passphrase was supplied without a private key. Set "
            "--snowflake-private-key-env-var (and populate the variable).",
        )
    if not config.snowflake_user:
        raise ValueError(
            "Snowflake is partially configured: --snowflake-account was supplied "
            "without --snowflake-user.",
        )

    return SnowflakeClient(
        account_id=config.snowflake_account,
        user=config.snowflake_user,
        pat=config.snowflake_pat,
        private_key=config.snowflake_private_key,
        private_key_passphrase=config.snowflake_private_key_passphrase,
        role=config.snowflake_role,
        warehouse=config.snowflake_warehouse,
    )


def _parse_databases(raw: str | None) -> set[str] | None:
    """Parse the comma-separated database allowlist, or None for every database.

    Names are kept as the operator wrote them. Snowflake folds an unquoted
    identifier to uppercase but preserves the case of a quoted one, so
    upper-casing here would silently drop a database that was created quoted and
    lower-case. The membership test in ``databases._skip_walk_reason`` is
    case-insensitive instead, which matches either form.
    """
    if not raw:
        return None
    names = {name.strip() for name in raw.split(",") if name.strip()}
    return names or None


def _cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
    incomplete: set[str],
) -> None:
    """Run every node cleanup in reverse dependency order.

    A module whose read was incomplete is skipped: a 403 on one database, or an
    ``ACCOUNT_USAGE`` view the role cannot read, means Cartography could not
    re-observe that surface this run. Deleting on that basis would destroy
    still-valid inventory, so the stale data is deliberately left in place.
    """
    for module in _CLEANUP_ORDER:
        name = _module_name(module)
        if name in incomplete:
            logger.warning(
                "Skipping Snowflake %s cleanup: this run could not read the whole "
                "surface, so stale nodes are kept rather than deleted.",
                name,
            )
            continue
        module.cleanup(neo4j_session, common_job_parameters)


@timeit
def start_snowflake_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Snowflake data. Otherwise warn and exit.

    One account is synced per run. Authentication is either a programmatic access
    token or an RSA key pair; see ``docs/root/modules/snowflake/config.md``.

    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.snowflake_account:
        logger.info(
            "Snowflake import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return
    if not config.snowflake_pat and not config.snowflake_private_key:
        logger.info(
            "Snowflake import is not configured - skipping this module. "
            "Set --snowflake-pat-env-var or --snowflake-private-key-env-var.",
        )
        return

    client = _build_client(config)
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "ACCOUNT_ID": client.account_id,
    }
    # Surfaces this run could not read in full. Their cleanup is skipped so a
    # transient failure or a missing privilege never deletes good data.
    incomplete: set[str] = set()

    def record(name: str, complete: bool) -> None:
        if not complete:
            incomplete.add(name)

    # The account tenant first: every other node's RESOURCE edge matches it.
    record("account", account.sync(neo4j_session, client, common_job_parameters))

    # Account parameters yield the account-wide network policy, which the network
    # policy sync needs in order to mark which policy is actually in force.
    account_network_policy, complete = account_parameters.sync(
        neo4j_session, client, common_job_parameters
    )
    record("account_parameters", complete)

    # Databases and schemas next: every schema-scoped surface below walks them,
    # including the network rules that network policies reference.
    walkable_databases, complete = databases.sync(
        neo4j_session,
        client,
        _parse_databases(config.snowflake_databases),
        common_job_parameters,
    )
    record("databases", complete)
    schema_list, complete = schemas.sync(
        neo4j_session, client, walkable_databases, common_job_parameters
    )
    record("schemas", complete)

    # A database or schema that could not be listed silently truncates `schema_list`,
    # and every sync below walks exactly the schemas it is handed. Those syncs
    # therefore report complete=True in good faith while holding no objects at all
    # for the unread database. Their cleanup is scoped to the account, not to the
    # database, so left unchecked it would delete that database's tables, views,
    # tasks and the rest as though they had been dropped. The incompleteness has to
    # be propagated here, where the truncation is actually visible.
    if not databases_and_schemas_complete(incomplete):
        for name in _SCHEMA_SCOPED_SURFACES:
            incomplete.add(name)
        logger.warning(
            "Some Snowflake databases or schemas could not be listed; skipping "
            "cleanup for every schema-scoped surface so objects in the unread "
            "databases are not deleted.",
        )

    rule_list, complete = network_rules.sync(
        neo4j_session, client, schema_list, common_job_parameters
    )
    record("network_rules", complete)
    # Network policies after their rules (ALLOWS / BLOCKS) and before users, whose
    # GOVERNED_BY edge points at a policy. The rules are passed through because a
    # policy references them by bare name.
    network_policies.sync(
        neo4j_session,
        client,
        account_network_policy,
        rule_list,
        common_job_parameters,
    )

    # Identity. Roles precede users and database roles, and both precede the grant
    # sync that connects them.
    #
    # ACCOUNT_USAGE.ROLES is read once here and handed to both role syncs. It is the
    # authoritative source: the object API follows SHOW ROLES visibility and so can
    # return a partial list that looks complete, which would let cleanup delete roles
    # the collector merely could not see. None means the views are unreadable, and
    # both syncs then fall back to the object API and report incomplete.
    account_usage_roles = account_usage.get_roles(client)
    role_list, complete = roles.sync(
        neo4j_session, client, account_usage_roles, common_job_parameters
    )
    record("roles", complete)
    database_role_list, complete = database_roles.sync(
        neo4j_session,
        client,
        walkable_databases,
        account_usage_roles,
        common_job_parameters,
    )
    record("database_roles", complete)
    humans, service_users = users.sync(neo4j_session, client, common_job_parameters)
    record(
        "access_tokens",
        access_tokens.sync(
            neo4j_session, client, humans + service_users, common_job_parameters
        ),
    )
    record(
        "credentials",
        credentials.sync(neo4j_session, client, common_job_parameters),
    )

    # Compute. Resource monitors precede warehouses so the MONITORED_BY edge lands.
    for module in (
        resource_monitors,
        warehouses,
        compute_pools,
    ):
        record(
            _module_name(module),
            module.sync(neo4j_session, client, common_job_parameters),
        )

    # External volumes and integrations: the cross-cloud pivots into S3 / GCS /
    # Azure and the IAM roles Snowflake assumes.
    record(
        "external_volumes",
        external_volumes.sync(neo4j_session, client, common_job_parameters),
    )
    for module in _INTEGRATION_MODULES:
        record(
            _module_name(module),
            module.sync(neo4j_session, client, common_job_parameters),
        )

    # Schema-scoped data objects.
    for module in _SCHEMA_LEVEL_MODULES:
        record(
            _module_name(module),
            module.sync(neo4j_session, client, schema_list, common_job_parameters),
        )

    # External access integrations reference secrets and network rules, so they run
    # after both, and before the workloads that reference them.
    record(
        "external_access_integrations",
        external_access_integrations.sync(neo4j_session, client, common_job_parameters),
    )

    for module in _WORKLOAD_MODULES:
        record(
            _module_name(module),
            module.sync(neo4j_session, client, schema_list, common_job_parameters),
        )

    # Data sharing and replication: how data leaves the account.
    for module in (
        shares,
        listings,
        replication_groups,
    ):
        record(
            _module_name(module),
            module.sync(neo4j_session, client, common_job_parameters),
        )

    # Policy attachments need every attachable object already loaded.
    record(
        "policy_references",
        policy_references.sync(neo4j_session, client, common_job_parameters),
    )

    # Grants last: they read every principal and grantable object from the graph,
    # so running here means the edges resolve on the first pass.
    grants_complete = grants.sync(
        neo4j_session,
        client,
        role_list,
        {user["name"] for user in service_users},
        database_role_list,
        common_job_parameters,
    )
    account_grants_complete = account_grants.sync(
        neo4j_session, client, common_job_parameters
    )

    # Cleanup runs once, centrally, only after every sync above has completed, so a
    # mid-sync failure cannot delete stale nodes on the strength of partial data.
    _cleanup(neo4j_session, common_job_parameters, incomplete)

    # Grant edges are MatchLinks with their own scoped cleanup. Both grant sources
    # write the same HAS_PRIVILEGE edge, so the shared cleanup only runs when both
    # were read in full; otherwise it would delete edges the other source still owns.
    if grants_complete and account_grants_complete:
        grants.cleanup(neo4j_session, client.account_id, config.update_tag)
    else:
        logger.warning(
            "Skipping Snowflake grant cleanup: the grant walk was incomplete, so "
            "still-valid privilege edges are kept rather than deleted.",
        )
