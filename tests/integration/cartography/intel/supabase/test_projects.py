from unittest.mock import patch

import requests

import cartography.intel.supabase.projects
import tests.data.supabase.projects
from tests.integration.cartography.intel.supabase.test_organizations import (
    _ensure_local_neo4j_has_test_organizations,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_SLUG = "simpson-corp"
TEST_PROJECT_REF = "nuclearplantdbaaaaaa"
TEST_BASE_URL = "https://api.fake-supabase.com"

_SETTINGS = {
    "legacy_api_keys": tests.data.supabase.projects.SUPABASE_LEGACY_API_KEYS,
    "postgrest": tests.data.supabase.projects.SUPABASE_POSTGREST_CONFIG,
    "storage": tests.data.supabase.projects.SUPABASE_STORAGE_CONFIG,
    "realtime": tests.data.supabase.projects.SUPABASE_REALTIME_CONFIG,
    "vanity_subdomain": tests.data.supabase.projects.SUPABASE_VANITY_SUBDOMAIN,
}

_POSTURE = {
    "ssl_enforcement": tests.data.supabase.projects.SUPABASE_SSL_ENFORCEMENT,
    "network_restrictions": tests.data.supabase.projects.SUPABASE_NETWORK_RESTRICTIONS,
    "backups": tests.data.supabase.projects.SUPABASE_DATABASE_BACKUPS,
}


def _ensure_local_neo4j_has_test_projects(neo4j_session):
    projects = [
        p
        for p in tests.data.supabase.projects.SUPABASE_PROJECTS
        if p["organization_slug"] == TEST_ORG_SLUG
    ]
    cartography.intel.supabase.projects.load_projects(
        neo4j_session,
        cartography.intel.supabase.projects.transform_projects(
            projects,
            {p["ref"]: _SETTINGS for p in projects},
        ),
        TEST_ORG_SLUG,
        TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_test_databases(neo4j_session):
    project = tests.data.supabase.projects.SUPABASE_PROJECTS[0]
    cartography.intel.supabase.projects.load_databases(
        neo4j_session,
        cartography.intel.supabase.projects.transform_database(project, _POSTURE),
        project["ref"],
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.supabase.projects,
    "get_settings",
    return_value=_SETTINGS,
)
@patch.object(
    cartography.intel.supabase.projects,
    "get",
    return_value=tests.data.supabase.projects.SUPABASE_PROJECTS,
)
def test_load_supabase_projects(mock_get, mock_get_settings, neo4j_session):
    """
    Ensure projects are filtered to the organization in scope, loaded with their
    rolled-up settings, and attached to the organization.
    """
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_SLUG": TEST_ORG_SLUG,
    }
    _ensure_local_neo4j_has_test_organizations(neo4j_session)

    # Act
    projects = cartography.intel.supabase.projects.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert the monorail project in the other organization was filtered out
    assert {p["ref"] for p in projects} == {
        "nuclearplantdbaaaaaa",
        "kwikemartdbbbbbbbbbb",
    }

    expected_nodes = {
        ("nuclearplantdbaaaaaa", "nuclear-plant", "us-east-2", "ACTIVE_HEALTHY"),
        ("kwikemartdbbbbbbbbbb", "kwik-e-mart", "eu-west-1", "INACTIVE"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "SupabaseProject",
            ["id", "name", "region", "status"],
        )
        == expected_nodes
    )

    # Assert projects are attached to the organization
    expected_rels = {
        ("nuclearplantdbaaaaaa", TEST_ORG_SLUG),
        ("kwikemartdbbbbbbbbbb", TEST_ORG_SLUG),
    }
    assert (
        check_rels(
            neo4j_session,
            "SupabaseProject",
            "id",
            "SupabaseOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )


@patch.object(
    cartography.intel.supabase.projects,
    "get_settings",
    return_value=_SETTINGS,
)
@patch.object(
    cartography.intel.supabase.projects,
    "get",
    return_value=tests.data.supabase.projects.SUPABASE_PROJECTS,
)
def test_supabase_project_settings_rollup(mock_get, mock_get_settings, neo4j_session):
    """
    Ensure the per-project configuration endpoints are rolled up onto the project
    node, and that the PostgREST jwt_secret is not.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)

    # Act
    cartography.intel.supabase.projects.sync(
        neo4j_session,
        api_session,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "BASE_URL": TEST_BASE_URL,
            "ORG_SLUG": TEST_ORG_SLUG,
        },
    )

    # Assert
    record = neo4j_session.run(
        """
        MATCH (p:SupabaseProject {id: $ref})
        RETURN p.legacy_api_keys_enabled AS legacy_api_keys_enabled,
               p.postgrest_db_schema AS postgrest_db_schema,
               p.postgrest_max_rows AS postgrest_max_rows,
               p.storage_s3_protocol_enabled AS storage_s3_protocol_enabled,
               p.storage_file_size_limit AS storage_file_size_limit,
               p.realtime_private_only AS realtime_private_only,
               p.vanity_subdomain AS vanity_subdomain,
               p.jwt_secret AS jwt_secret
        """,
        ref=TEST_PROJECT_REF,
    ).single()
    assert record["legacy_api_keys_enabled"] is True
    assert record["postgrest_db_schema"] == "public, graphql_public"
    assert record["postgrest_max_rows"] == 1000
    assert record["storage_s3_protocol_enabled"] is True
    assert record["storage_file_size_limit"] == 52428800
    assert record["realtime_private_only"] is False
    assert record["vanity_subdomain"] == "nuclear-plant.supabase.co"
    # The PostgREST response carries jwt_secret; it must never be ingested.
    assert record["jwt_secret"] is None


@patch.object(
    cartography.intel.supabase.projects,
    "get_settings",
    return_value={
        "legacy_api_keys": None,
        "postgrest": None,
        "storage": None,
        "realtime": None,
        "vanity_subdomain": None,
    },
)
@patch.object(
    cartography.intel.supabase.projects,
    "get",
    return_value=tests.data.supabase.projects.SUPABASE_PROJECTS,
)
def test_supabase_projects_tolerate_missing_settings(
    mock_get,
    mock_get_settings,
    neo4j_session,
):
    """
    Ensure a project whose configuration endpoints are all plan-gated still loads,
    with the rolled-up properties left unset.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)

    # Act
    cartography.intel.supabase.projects.sync(
        neo4j_session,
        api_session,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "BASE_URL": TEST_BASE_URL,
            "ORG_SLUG": TEST_ORG_SLUG,
        },
    )

    # Assert
    record = neo4j_session.run(
        """
        MATCH (p:SupabaseProject {id: $ref})
        RETURN p.name AS name,
               p.legacy_api_keys_enabled AS legacy_api_keys_enabled,
               p.postgrest_db_schema AS postgrest_db_schema
        """,
        ref=TEST_PROJECT_REF,
    ).single()
    assert record["name"] == "nuclear-plant"
    assert record["legacy_api_keys_enabled"] is None
    assert record["postgrest_db_schema"] is None


@patch.object(
    cartography.intel.supabase.projects,
    "get_database_posture",
    return_value=_POSTURE,
)
def test_load_supabase_database(mock_get_posture, neo4j_session):
    """
    Ensure the project's Postgres database is loaded with its network, TLS and
    backup posture, and attached to the project.
    """
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_SLUG": TEST_ORG_SLUG,
        "PROJECT_REF": TEST_PROJECT_REF,
    }
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.projects.sync_database(
        neo4j_session,
        api_session,
        tests.data.supabase.projects.SUPABASE_PROJECTS[0],
        common_job_parameters,
    )

    # Assert
    expected_nodes = {
        (
            f"{TEST_PROJECT_REF}/postgres",
            "db.nuclearplantdbaaaaaa.supabase.co",
            "17.6.1.147",
            True,
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "SupabaseDatabase",
            ["id", "host", "version", "ssl_enforced"],
        )
        == expected_nodes
    )

    # Assert posture landed
    record = neo4j_session.run(
        """
        MATCH (d:SupabaseDatabase {id: $id})
        RETURN d.db_allowed_cidrs AS cidrs,
               d.network_restrictions_status AS status,
               d.pitr_enabled AS pitr_enabled,
               d.walg_enabled AS walg_enabled,
               d.latest_backup_at AS latest_backup_at
        """,
        id=f"{TEST_PROJECT_REF}/postgres",
    ).single()
    assert record["cidrs"] == ["10.0.0.0/8"]
    assert record["status"] == "applied"
    assert record["pitr_enabled"] is False
    assert record["walg_enabled"] is True
    # The most recent of the two backups in the fixture.
    assert record["latest_backup_at"].to_native().day == 26

    # Assert the database is attached to its project
    assert check_rels(
        neo4j_session,
        "SupabaseDatabase",
        "id",
        "SupabaseProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(f"{TEST_PROJECT_REF}/postgres", TEST_PROJECT_REF)}


@patch.object(
    cartography.intel.supabase.projects,
    "get_database_posture",
    return_value={
        "ssl_enforcement": None,
        "network_restrictions": None,
        "backups": None,
    },
)
def test_supabase_database_tolerates_missing_posture(mock_get_posture, neo4j_session):
    """
    Ensure a free-tier project, where the posture endpoints are plan-gated, still
    produces a database node.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.projects.sync_database(
        neo4j_session,
        api_session,
        tests.data.supabase.projects.SUPABASE_PROJECTS[0],
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "BASE_URL": TEST_BASE_URL,
            "ORG_SLUG": TEST_ORG_SLUG,
            "PROJECT_REF": TEST_PROJECT_REF,
        },
    )

    # Assert
    record = neo4j_session.run(
        """
        MATCH (d:SupabaseDatabase {id: $id})
        RETURN d.host AS host,
               d.ssl_enforced AS ssl_enforced,
               d.db_allowed_cidrs AS cidrs,
               d.pitr_enabled AS pitr_enabled
        """,
        id=f"{TEST_PROJECT_REF}/postgres",
    ).single()
    assert record["host"] == "db.nuclearplantdbaaaaaa.supabase.co"
    assert record["ssl_enforced"] is None
    assert record["cidrs"] is None
    assert record["pitr_enabled"] is None


@patch.object(
    cartography.intel.supabase.projects,
    "get_database_posture",
    return_value=_POSTURE,
)
def test_supabase_database_ontology_labels(mock_get_posture, neo4j_session):
    """
    Ensure the Database semantic label and its _ont_* properties are applied.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.projects.sync_database(
        neo4j_session,
        api_session,
        tests.data.supabase.projects.SUPABASE_PROJECTS[0],
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "BASE_URL": TEST_BASE_URL,
            "ORG_SLUG": TEST_ORG_SLUG,
            "PROJECT_REF": TEST_PROJECT_REF,
        },
    )

    # Assert
    record = neo4j_session.run(
        """
        MATCH (d:SupabaseDatabase:Database {id: $id})
        RETURN d._ont_type AS db_type,
               d._ont_endpoint AS endpoint,
               d._ont_version AS version,
               d._ont_location AS location,
               d._ont_source AS source
        """,
        id=f"{TEST_PROJECT_REF}/postgres",
    ).single()
    assert record["db_type"] == "postgres"
    assert record["endpoint"] == "db.nuclearplantdbaaaaaa.supabase.co"
    assert record["version"] == "17.6.1.147"
    assert record["location"] == "us-east-2"
    assert record["source"] == "supabase"
