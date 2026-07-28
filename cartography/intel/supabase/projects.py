import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.supabase.util import get_json
from cartography.intel.supabase.util import iso_to_datetime
from cartography.intel.supabase.util import TOLERATED_STATUSES
from cartography.models.supabase.database import SupabaseDatabaseSchema
from cartography.models.supabase.project import SupabaseProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Sync the projects belonging to the organization currently in scope and return
    them so the caller can fan out per project.
    """
    base_url = common_job_parameters["BASE_URL"]
    org_slug = common_job_parameters["ORG_SLUG"]

    projects = [
        p for p in get(api_session, base_url) if p["organization_slug"] == org_slug
    ]
    settings = {
        p["ref"]: get_settings(api_session, base_url, p["ref"]) for p in projects
    }

    transformed = transform_projects(projects, settings)
    load_projects(
        neo4j_session,
        transformed,
        org_slug,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return projects


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    """
    List every project the token can see. This endpoint (unlike the org-scoped one)
    carries `organization_slug`, `created_at` and the primary `database` object, so
    it is the single source of truth for both the project and database nodes.
    """
    return get_json(api_session, f"{base_url}/v1/projects")


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

        result.append(
            {
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
            },
        )
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
    GraphJob.from_node_schema(SupabaseProjectSchema(), common_job_parameters).run(
        neo4j_session,
    )


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
    posture = get_database_posture(
        api_session,
        common_job_parameters["BASE_URL"],
        project["ref"],
    )
    transformed = transform_database(project, posture)
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

    return [
        {
            "id": f"{project['ref']}/postgres",
            "name": f"{project['name']} (postgres)",
            "host": database["host"],
            "version": database["version"],
            "postgres_engine": database["postgres_engine"],
            "release_channel": database["release_channel"],
            "region": project["region"],
            "ssl_enforced": (ssl_enforcement.get("currentConfig") or {}).get(
                "database"
            ),
            "network_restrictions_status": network_restrictions.get("status"),
            "db_allowed_cidrs": restrictions_config.get("dbAllowedCidrs"),
            "db_allowed_cidrs_v6": restrictions_config.get("dbAllowedCidrsV6"),
            "pitr_enabled": backups.get("pitr_enabled"),
            "walg_enabled": backups.get("walg_enabled"),
            "latest_backup_at": iso_to_datetime(latest_backup_at),
        },
    ]


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
