import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.supabase.util import get_json
from cartography.intel.supabase.util import iso_to_datetime
from cartography.intel.supabase.util import TOLERATED_STATUSES
from cartography.intel.supabase.util import warn_unavailable
from cartography.models.supabase.database import SupabaseDatabaseSchema
from cartography.models.supabase.project import SupabaseProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


# The project properties each configuration endpoint feeds. When an endpoint is
# unavailable its group is carried forward from the graph rather than overwritten
# with null: see _carry_forward().
PROJECT_POSTURE_FIELDS: dict[str, tuple[str, ...]] = {
    "legacy_api_keys": ("legacy_api_keys_enabled",),
    "postgrest": (
        "postgrest_db_schema",
        "postgrest_max_rows",
        "postgrest_db_extra_search_path",
    ),
    "storage": ("storage_file_size_limit", "storage_s3_protocol_enabled"),
    "realtime": ("realtime_private_only", "realtime_presence_enabled"),
    "vanity_subdomain": ("vanity_subdomain", "vanity_subdomain_status"),
}

# Same idea for the database node's posture endpoints.
DATABASE_POSTURE_FIELDS: dict[str, tuple[str, ...]] = {
    "ssl_enforcement": ("ssl_enforced",),
    "network_restrictions": (
        "network_restrictions_status",
        "db_allowed_cidrs",
        "db_allowed_cidrs_v6",
    ),
    "backups": ("pitr_enabled", "walg_enabled", "latest_backup_at"),
}


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    projects: list[dict[str, Any]],
) -> None:
    """
    Sync the given projects, which the caller has already filtered to the
    organization currently in scope.

    The project list is passed in rather than fetched here because GET /v1/projects
    is global: fetching it once and grouping by organization avoids one redundant
    request per organization.

    Cleanup is deliberately not run here. Stale projects must be removed only after
    their children have been synced, and with a cascade, so a project deleted
    upstream does not leave orphaned children behind. See cleanup().
    """
    base_url = common_job_parameters["BASE_URL"]
    org_slug = common_job_parameters["ORG_SLUG"]

    settings = {
        p["ref"]: get_settings(api_session, base_url, p["ref"]) for p in projects
    }
    stored = get_stored_properties(
        neo4j_session,
        "SupabaseProject",
        [p["ref"] for p in projects],
        _all_fields(PROJECT_POSTURE_FIELDS),
    )

    transformed = transform_projects(projects, settings, stored)
    load_projects(
        neo4j_session,
        transformed,
        org_slug,
        common_job_parameters["UPDATE_TAG"],
    )


def _all_fields(groups: dict[str, tuple[str, ...]]) -> list[str]:
    return [field for fields in groups.values() for field in fields]


def get_stored_properties(
    neo4j_session: neo4j.Session,
    label: str,
    node_ids: list[str],
    fields: list[str],
) -> dict[str, dict[str, Any]]:
    """
    Read the currently-stored values of ``fields`` for the given node ids.

    Used to preserve last-known-good posture when a configuration endpoint cannot
    be read. Returns {node id: {field: value}}; ids not yet in the graph are absent.
    """
    if not node_ids or not fields:
        return {}
    projection = ", ".join(f"n.`{field}` AS `{field}`" for field in fields)
    records = neo4j_session.run(
        f"MATCH (n:{label}) WHERE n.id IN $node_ids RETURN n.id AS id, {projection}",
        node_ids=node_ids,
    )
    return {r["id"]: {field: r[field] for field in fields} for r in records}


def _carry_forward(
    record: dict[str, Any],
    groups: dict[str, tuple[str, ...]],
    responses: dict[str, Any],
    stored: dict[str, Any],
) -> None:
    """
    For each configuration group whose endpoint was unreadable, restore the values
    already in the graph instead of leaving the freshly-computed ``None``.

    Overwriting real posture with null on a transient 403 or a lost entitlement
    would silently downgrade security-relevant fields (``ssl_enforced``,
    ``legacy_api_keys_enabled``, ``pitr_enabled``) to "unknown, looks fine". A 200
    that genuinely omits a field still writes null, because that is real data.

    The tradeoff is that a feature deliberately turned off keeps its last value
    until the endpoint is readable again; a stale value carrying its original
    meaning beats a null that reads as "not configured".
    """
    for group, fields in groups.items():
        if responses.get(group) is not None:
            continue
        for field in fields:
            if field in stored:
                record[field] = stored[field]


_ORG_PROJECTS_PAGE_SIZE = 100


@timeit
def get_org_projects(
    api_session: requests.Session,
    base_url: str,
    org_slug: str,
) -> list[dict[str, Any]]:
    """
    List the projects belonging to an organization.

    This is the authority for which projects exist, because it is the only endpoint
    documented as organization-scoped. GET /v1/projects returns "all projects you've
    previously created", so a project created by another member of the same
    organization is absent from it. Enumerating from that endpoint would make a
    colleague's project look deleted and, with the cascading project cleanup, take
    its database, keys, buckets and findings with it on every sync.

    The endpoint is offset-paginated, and truncating it would have exactly the same
    effect as missing a project, so every page is fetched.
    """
    projects: list[dict[str, Any]] = []
    offset = 0
    while True:
        page = get_json(
            api_session,
            f"{base_url}/v1/organizations/{org_slug}/projects"
            f"?offset={offset}&limit={_ORG_PROJECTS_PAGE_SIZE}",
        )
        batch = (page or {}).get("projects") or []
        projects.extend(batch)
        if len(batch) < _ORG_PROJECTS_PAGE_SIZE:
            return projects
        offset += _ORG_PROJECTS_PAGE_SIZE


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    """
    List the projects the token's own user created.

    Used only to enrich the organization-scoped listing: this response carries the
    `database` object (host, version, engine, release channel) that the org-scoped
    one omits. It is deliberately not used to decide which projects exist. See
    get_org_projects().
    """
    return get_json(api_session, f"{base_url}/v1/projects")


def merge_project(
    org_project: dict[str, Any],
    org_slug: str,
    enrichment: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Combine an organization-scoped project entry with the richer global-listing
    entry for the same ref, when one is available.

    Membership and identity always come from the organization-scoped entry.
    ``database`` is enrichment-only, so for a project created by another member it
    stays absent and transform_database() skips the database node with a warning
    rather than inventing values.
    """
    enrichment = enrichment or {}
    return {
        "ref": org_project["ref"],
        "name": org_project["name"],
        "region": org_project["region"],
        "status": org_project["status"],
        # The org-scoped listing calls this inserted_at; the global one created_at.
        "created_at": enrichment.get("created_at") or org_project.get("inserted_at"),
        "organization_slug": org_slug,
        "database": enrichment.get("database"),
    }


@timeit
def get_settings(
    api_session: requests.Session,
    base_url: str,
    project_ref: str,
) -> dict[str, Any]:
    """
    Fetch the project-level configuration that is rolled up onto the project node.
    Each of these is independently plan-gated or beta, so tolerate the "unavailable"
    statuses and carry on with whatever the API does return.
    """
    project_url = f"{base_url}/v1/projects/{project_ref}"
    return {
        "legacy_api_keys": get_json(
            api_session,
            f"{project_url}/api-keys/legacy",
            tolerate=TOLERATED_STATUSES,
        ),
        # NOTE: this response also carries `jwt_secret`, which is deliberately
        # dropped in transform_projects and never written to the graph.
        "postgrest": get_json(
            api_session,
            f"{project_url}/postgrest",
            tolerate=TOLERATED_STATUSES,
        ),
        "storage": get_json(
            api_session,
            f"{project_url}/config/storage",
            tolerate=TOLERATED_STATUSES,
        ),
        "realtime": get_json(
            api_session,
            f"{project_url}/config/realtime",
            tolerate=TOLERATED_STATUSES,
        ),
        "vanity_subdomain": get_json(
            api_session,
            f"{project_url}/vanity-subdomain",
            tolerate=TOLERATED_STATUSES,
        ),
    }


def transform_projects(
    projects: list[dict[str, Any]],
    settings: dict[str, dict[str, Any]],
    stored: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for project in projects:
        project_settings = settings.get(project["ref"], {})
        legacy_api_keys = project_settings.get("legacy_api_keys") or {}
        postgrest = project_settings.get("postgrest") or {}
        storage = project_settings.get("storage") or {}
        realtime = project_settings.get("realtime") or {}
        vanity = project_settings.get("vanity_subdomain") or {}
        storage_features = storage.get("features") or {}

        record = {
            "ref": project["ref"],
            "name": project["name"],
            "region": project["region"],
            "status": project["status"],
            "created_at": iso_to_datetime(project["created_at"]),
            "organization_slug": project["organization_slug"],
            "legacy_api_keys_enabled": legacy_api_keys.get("enabled"),
            "postgrest_db_schema": postgrest.get("db_schema"),
            "postgrest_max_rows": postgrest.get("max_rows"),
            "postgrest_db_extra_search_path": postgrest.get(
                "db_extra_search_path",
            ),
            "storage_file_size_limit": storage.get("fileSizeLimit"),
            "storage_s3_protocol_enabled": (
                storage_features.get("s3Protocol") or {}
            ).get(
                "enabled",
            ),
            "realtime_private_only": realtime.get("private_only"),
            "realtime_presence_enabled": realtime.get("presence_enabled"),
            "vanity_subdomain": vanity.get("custom_domain"),
            "vanity_subdomain_status": vanity.get("status"),
        }
        _carry_forward(
            record,
            PROJECT_POSTURE_FIELDS,
            project_settings,
            (stored or {}).get(project["ref"], {}),
        )
        result.append(record)
    return result


@timeit
def load_projects(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_slug: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SupabaseProjectSchema(),
        data,
        lastupdated=update_tag,
        ORG_SLUG=org_slug,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove projects that no longer exist in the organization, and their children.

    Must run after every project's children have been synced. ``cascade_delete``
    is required: child cleanups are scoped to ``PROJECT_REF`` and only run for
    projects that still exist, so without the cascade a project deleted upstream
    would have its node removed and leave its database, keys, buckets, functions
    and findings behind as unreachable orphans. Same reasoning as the GCP project
    and folder cleanups.
    """
    GraphJob.from_node_schema(
        SupabaseProjectSchema(),
        common_job_parameters,
        cascade_delete=True,
    ).run(neo4j_session)


@timeit
def sync_database(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    project: dict[str, Any],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync the single Postgres database backing the project in scope, along with its
    network, TLS and backup posture.
    """
    # No enrichment means the database details were unreadable, not that the database
    # was deleted: the organization listing returns projects that the creator-only
    # /v1/projects response omits. Loading nothing and then cleaning up would delete a
    # database node ingested by an earlier sync, so skip both.
    if not project.get("database"):
        warn_unavailable("database details", project["ref"])
        return

    posture = get_database_posture(
        api_session,
        common_job_parameters["BASE_URL"],
        project["ref"],
    )
    stored = get_stored_properties(
        neo4j_session,
        "SupabaseDatabase",
        [f"{project['ref']}/postgres"],
        _all_fields(DATABASE_POSTURE_FIELDS),
    )
    transformed = transform_database(project, posture, stored)
    load_databases(
        neo4j_session,
        transformed,
        project["ref"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup_databases(neo4j_session, common_job_parameters)


@timeit
def get_database_posture(
    api_session: requests.Session,
    base_url: str,
    project_ref: str,
) -> dict[str, Any]:
    project_url = f"{base_url}/v1/projects/{project_ref}"
    return {
        "ssl_enforcement": get_json(
            api_session,
            f"{project_url}/ssl-enforcement",
            tolerate=TOLERATED_STATUSES,
        ),
        "network_restrictions": get_json(
            api_session,
            f"{project_url}/network-restrictions",
            tolerate=TOLERATED_STATUSES,
        ),
        "backups": get_json(
            api_session,
            f"{project_url}/database/backups",
            tolerate=TOLERATED_STATUSES,
        ),
    }


def transform_database(
    project: dict[str, Any],
    posture: dict[str, Any],
    stored: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    database = project.get("database") or {}
    if not database:
        logger.warning(
            "Supabase project %s returned no database object - skipping database node.",
            project["ref"],
        )
        return []

    ssl_enforcement = posture.get("ssl_enforcement") or {}
    network_restrictions = posture.get("network_restrictions") or {}
    restrictions_config = network_restrictions.get("config") or {}
    backups = posture.get("backups") or {}
    backup_entries = backups.get("backups") or []
    latest_backup_at = max(
        (b["inserted_at"] for b in backup_entries if b.get("inserted_at")),
        default=None,
    )

    database_id = f"{project['ref']}/postgres"
    record = {
        "id": database_id,
        "name": f"{project['name']} (postgres)",
        "host": database["host"],
        "version": database["version"],
        "postgres_engine": database["postgres_engine"],
        "release_channel": database["release_channel"],
        "region": project["region"],
        "ssl_enforced": (ssl_enforcement.get("currentConfig") or {}).get("database"),
        "network_restrictions_status": network_restrictions.get("status"),
        "db_allowed_cidrs": restrictions_config.get("dbAllowedCidrs"),
        "db_allowed_cidrs_v6": restrictions_config.get("dbAllowedCidrsV6"),
        "pitr_enabled": backups.get("pitr_enabled"),
        "walg_enabled": backups.get("walg_enabled"),
        "latest_backup_at": iso_to_datetime(latest_backup_at),
    }
    _carry_forward(
        record,
        DATABASE_POSTURE_FIELDS,
        posture,
        (stored or {}).get(database_id, {}),
    )
    return [record]


@timeit
def load_databases(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_ref: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SupabaseDatabaseSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_REF=project_ref,
    )


@timeit
def cleanup_databases(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SupabaseDatabaseSchema(), common_job_parameters).run(
        neo4j_session,
    )
