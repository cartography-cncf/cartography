from unittest.mock import patch

import requests

import cartography.intel.supabase.organizations
import cartography.intel.supabase.projects
import cartography.intel.supabase.storage
import tests.data.supabase.projects
import tests.data.supabase.storage
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


def _org_projects():
    """The fixture projects belonging to the organization under test."""
    return [
        p
        for p in tests.data.supabase.projects.SUPABASE_PROJECTS
        if p["organization_slug"] == TEST_ORG_SLUG
    ]


def _ensure_local_neo4j_has_test_projects(neo4j_session):
    projects = _org_projects()
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
def test_load_supabase_projects(mock_get_settings, neo4j_session):
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
    cartography.intel.supabase.projects.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        _org_projects(),
    )

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
def test_supabase_project_settings_rollup(mock_get_settings, neo4j_session):
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
        _org_projects(),
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
def test_supabase_projects_tolerate_missing_settings(
    mock_get_settings,
    neo4j_session,
):
    """
    Ensure a project whose configuration endpoints are all unavailable still loads,
    with the rolled-up properties left unset when nothing was ever recorded.
    """
    # Arrange: an organization and project not touched by any other test, so there
    # is no previously-stored posture to carry forward.
    api_session = requests.Session()
    org_slug = "unseen-org"
    project = {
        **tests.data.supabase.projects.SUPABASE_PROJECTS[0],
        "id": "unseenprojectaaaaaaa",
        "ref": "unseenprojectaaaaaaa",
        "organization_slug": org_slug,
    }
    cartography.intel.supabase.organizations.load_organizations(
        neo4j_session,
        [{"slug": org_slug, "organization_id": org_slug, "name": "Unseen"}],
        TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.supabase.projects.sync(
        neo4j_session,
        api_session,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "BASE_URL": TEST_BASE_URL,
            "ORG_SLUG": org_slug,
        },
        [project],
    )

    # Assert
    record = neo4j_session.run(
        """
        MATCH (p:SupabaseProject {id: $ref})
        RETURN p.name AS name,
               p.legacy_api_keys_enabled AS legacy_api_keys_enabled,
               p.postgrest_db_schema AS postgrest_db_schema
        """,
        ref="unseenprojectaaaaaaa",
    ).single()
    assert record["name"] == "nuclear-plant"
    assert record["legacy_api_keys_enabled"] is None
    assert record["postgrest_db_schema"] is None


def test_supabase_project_posture_is_carried_forward_when_unreadable(neo4j_session):
    """
    An unreadable configuration endpoint must not overwrite real posture with null.

    Nulling `legacy_api_keys_enabled` on a transient 403 would silently downgrade a
    security-relevant fact to "unknown, looks fine". A 200 that genuinely omits the
    field still writes null, because that is real data.
    """
    # Arrange: a successful sync records the real posture.
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    common = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_SLUG": TEST_ORG_SLUG,
    }
    with patch.object(
        cartography.intel.supabase.projects, "get_settings", return_value=_SETTINGS
    ):
        cartography.intel.supabase.projects.sync(
            neo4j_session, api_session, common, _org_projects()
        )

    # Act: every configuration endpoint goes unavailable on a later sync.
    with patch.object(
        cartography.intel.supabase.projects,
        "get_settings",
        return_value={key: None for key in _SETTINGS},
    ):
        cartography.intel.supabase.projects.sync(
            neo4j_session,
            api_session,
            {**common, "UPDATE_TAG": TEST_UPDATE_TAG + 20},
            _org_projects(),
        )

    # Assert the posture survived rather than being nulled.
    record = neo4j_session.run(
        """
        MATCH (p:SupabaseProject {id: $ref})
        RETURN p.legacy_api_keys_enabled AS legacy_api_keys_enabled,
               p.postgrest_db_schema AS postgrest_db_schema,
               p.postgrest_max_rows AS postgrest_max_rows,
               p.storage_s3_protocol_enabled AS s3,
               p.vanity_subdomain AS vanity,
               p.lastupdated AS lastupdated
        """,
        ref=TEST_PROJECT_REF,
    ).single()
    assert record["legacy_api_keys_enabled"] is True
    assert record["postgrest_db_schema"] == "public, graphql_public"
    assert record["postgrest_max_rows"] == 1000
    assert record["s3"] is True
    assert record["vanity"] == "nuclear-plant.supabase.co"
    # The node itself was still refreshed, so the staleness is visible.
    assert record["lastupdated"] == TEST_UPDATE_TAG + 20


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
    Ensure a project whose posture endpoints are unavailable still produces a
    database node, with the posture left unset when nothing was ever recorded.
    """
    # Arrange: a project not touched by any other test, so there is no stored
    # posture to carry forward.
    api_session = requests.Session()
    project = {
        **tests.data.supabase.projects.SUPABASE_PROJECTS[0],
        "id": "unseendbaaaaaaaaaaaa",
        "ref": "unseendbaaaaaaaaaaaa",
    }
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.projects.sync_database(
        neo4j_session,
        api_session,
        project,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "BASE_URL": TEST_BASE_URL,
            "ORG_SLUG": TEST_ORG_SLUG,
            "PROJECT_REF": project["ref"],
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
        id=f"{project['ref']}/postgres",
    ).single()
    assert record["host"] == "db.nuclearplantdbaaaaaa.supabase.co"
    assert record["ssl_enforced"] is None
    assert record["cidrs"] is None
    assert record["pitr_enabled"] is None


def test_supabase_database_posture_is_carried_forward_when_unreadable(neo4j_session):
    """
    An unreadable posture endpoint must not overwrite the database's real posture.

    Nulling `ssl_enforced`, `db_allowed_cidrs` or `pitr_enabled` on a transient 403
    would turn a known-bad configuration into an apparently clean one.
    """
    # Arrange: a successful sync records the real posture.
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)
    project = tests.data.supabase.projects.SUPABASE_PROJECTS[0]
    common = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_SLUG": TEST_ORG_SLUG,
        "PROJECT_REF": project["ref"],
    }
    with patch.object(
        cartography.intel.supabase.projects,
        "get_database_posture",
        return_value=_POSTURE,
    ):
        cartography.intel.supabase.projects.sync_database(
            neo4j_session, api_session, project, common
        )

    # Act: the posture endpoints go unavailable on a later sync.
    with patch.object(
        cartography.intel.supabase.projects,
        "get_database_posture",
        return_value={key: None for key in _POSTURE},
    ):
        cartography.intel.supabase.projects.sync_database(
            neo4j_session,
            api_session,
            project,
            {**common, "UPDATE_TAG": TEST_UPDATE_TAG + 20},
        )

    # Assert the posture survived rather than being nulled.
    record = neo4j_session.run(
        """
        MATCH (d:SupabaseDatabase {id: $id})
        RETURN d.ssl_enforced AS ssl_enforced,
               d.db_allowed_cidrs AS cidrs,
               d.network_restrictions_status AS status,
               d.walg_enabled AS walg,
               d.lastupdated AS lastupdated
        """,
        id=f"{project['ref']}/postgres",
    ).single()
    assert record["ssl_enforced"] is True
    assert record["cidrs"] == ["10.0.0.0/8"]
    assert record["status"] == "applied"
    assert record["walg"] is True
    assert record["lastupdated"] == TEST_UPDATE_TAG + 20


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


def test_supabase_project_cleanup_cascades_to_children(neo4j_session):
    """
    A project deleted upstream must not leave its children behind as orphans.

    Child cleanups are scoped to PROJECT_REF and only run for projects that still
    exist, so nothing would ever collect the children of a project that vanished.
    The project cleanup therefore has to cascade.
    """
    # Arrange: two projects, each with a database and a storage bucket.
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    projects = _org_projects()
    doomed_ref, surviving_ref = projects[0]["ref"], projects[1]["ref"]
    common = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_SLUG": TEST_ORG_SLUG,
    }
    with patch.object(
        cartography.intel.supabase.projects, "get_settings", return_value=_SETTINGS
    ):
        cartography.intel.supabase.projects.sync(
            neo4j_session, api_session, common, projects
        )
    for project in projects:
        with patch.object(
            cartography.intel.supabase.projects,
            "get_database_posture",
            return_value=_POSTURE,
        ):
            cartography.intel.supabase.projects.sync_database(
                neo4j_session,
                api_session,
                project,
                {**common, "PROJECT_REF": project["ref"]},
            )
        cartography.intel.supabase.storage.load_buckets(
            neo4j_session,
            cartography.intel.supabase.storage.transform_buckets(
                tests.data.supabase.storage.SUPABASE_STORAGE_BUCKETS,
                project["ref"],
            ),
            project["ref"],
            TEST_UPDATE_TAG,
        )
    assert (f"{doomed_ref}/postgres",) in check_nodes(
        neo4j_session, "SupabaseDatabase", ["id"]
    )

    # Act: the next sync no longer returns the first project.
    later_tag = TEST_UPDATE_TAG + 30
    with patch.object(
        cartography.intel.supabase.projects, "get_settings", return_value=_SETTINGS
    ):
        cartography.intel.supabase.projects.sync(
            neo4j_session,
            api_session,
            {**common, "UPDATE_TAG": later_tag},
            [projects[1]],
        )
    with patch.object(
        cartography.intel.supabase.projects,
        "get_database_posture",
        return_value=_POSTURE,
    ):
        cartography.intel.supabase.projects.sync_database(
            neo4j_session,
            api_session,
            projects[1],
            {**common, "UPDATE_TAG": later_tag, "PROJECT_REF": surviving_ref},
        )
    cartography.intel.supabase.storage.load_buckets(
        neo4j_session,
        cartography.intel.supabase.storage.transform_buckets(
            tests.data.supabase.storage.SUPABASE_STORAGE_BUCKETS,
            surviving_ref,
        ),
        surviving_ref,
        later_tag,
    )
    cartography.intel.supabase.projects.cleanup(
        neo4j_session,
        {**common, "UPDATE_TAG": later_tag},
    )

    # Assert: the deleted project and its children are gone, the survivor intact.
    project_ids = {
        row[0] for row in check_nodes(neo4j_session, "SupabaseProject", ["id"])
    }
    assert doomed_ref not in project_ids
    assert surviving_ref in project_ids

    database_ids = {
        row[0] for row in check_nodes(neo4j_session, "SupabaseDatabase", ["id"])
    }
    assert f"{doomed_ref}/postgres" not in database_ids
    assert f"{surviving_ref}/postgres" in database_ids

    bucket_ids = {
        row[0] for row in check_nodes(neo4j_session, "SupabaseStorageBucket", ["id"])
    }
    assert not any(b.startswith(f"{doomed_ref}/") for b in bucket_ids)
    assert any(b.startswith(f"{surviving_ref}/") for b in bucket_ids)


def test_supabase_database_survives_missing_enrichment(neo4j_session):
    """
    Losing the database enrichment must not delete an already-ingested database node.

    The organization listing returns projects that the creator-only /v1/projects
    response omits, so an absent `database` object means "details unavailable", not
    "database deleted". Loading nothing and then running cleanup would destroy the
    node, along with the posture recorded on it.
    """
    # Arrange: a first sync with enrichment present records the database.
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)
    project = tests.data.supabase.projects.SUPABASE_PROJECTS[0]
    common = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_SLUG": TEST_ORG_SLUG,
        "PROJECT_REF": project["ref"],
    }
    with patch.object(
        cartography.intel.supabase.projects,
        "get_database_posture",
        return_value=_POSTURE,
    ):
        cartography.intel.supabase.projects.sync_database(
            neo4j_session, api_session, project, common
        )
    database_id = f"{project['ref']}/postgres"
    assert (database_id,) in check_nodes(neo4j_session, "SupabaseDatabase", ["id"])

    # Act: the same project comes back without enrichment, on a later update tag so a
    # cleanup would consider the existing database node stale.
    unenriched = {**project, "database": None}
    with patch.object(
        cartography.intel.supabase.projects,
        "get_database_posture",
        return_value=_POSTURE,
    ):
        cartography.intel.supabase.projects.sync_database(
            neo4j_session,
            api_session,
            unenriched,
            {**common, "UPDATE_TAG": TEST_UPDATE_TAG + 40},
        )

    # Assert the node and its posture survived.
    record = neo4j_session.run(
        """
        MATCH (d:SupabaseDatabase {id: $id})
        RETURN d.host AS host, d.ssl_enforced AS ssl_enforced
        """,
        id=database_id,
    ).single()
    assert record is not None, "database node must not be deleted"
    assert record["host"] == "db.nuclearplantdbaaaaaa.supabase.co"
    assert record["ssl_enforced"] is True
