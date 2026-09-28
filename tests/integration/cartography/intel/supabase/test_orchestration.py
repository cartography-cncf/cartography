"""
End-to-end tests for the module entry point.

The per-domain tests exercise each sync in isolation, which leaves the fan-out
itself untested: how projects are enumerated, and where the cascading project
cleanup sits relative to the per-project loop. Both of those are where a project
can be wrongly deleted, so they are covered here.
"""

from unittest.mock import patch

import cartography.intel.supabase
import tests.data.supabase.organizations
import tests.data.supabase.projects
from cartography.config import Config
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 987650000
TEST_ORG_SLUG = "simpson-corp"
TEST_BASE_URL = "https://api.fake-supabase.com"


def _config(update_tag, organizations=None):
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        supabase_access_token="fake-token",
        supabase_base_url=TEST_BASE_URL,
        supabase_organizations=organizations,
    )


def _run(neo4j_session, update_tag, org_projects, orgs=None, organizations=None):
    """Run the entry point with every outbound call stubbed at its module boundary."""
    orgs = (
        orgs
        if orgs is not None
        else [tests.data.supabase.organizations.SUPABASE_ORGANIZATIONS[0]]
    )
    details = tests.data.supabase.organizations.SUPABASE_ORGANIZATION_DETAILS
    with (
        patch.object(
            cartography.intel.supabase.organizations, "get", return_value=orgs
        ),
        patch.object(
            cartography.intel.supabase.organizations,
            "get_details",
            side_effect=lambda s, u, slug: details[slug],
        ),
        patch.object(
            cartography.intel.supabase.organizations, "get_members", return_value=[]
        ),
        patch.object(
            cartography.intel.supabase.projects,
            "get",
            return_value=tests.data.supabase.projects.SUPABASE_PROJECTS,
        ),
        patch.object(
            cartography.intel.supabase.projects,
            "get_org_projects",
            return_value=org_projects,
        ),
        patch.object(
            cartography.intel.supabase.projects,
            "get_settings",
            return_value={},
        ),
        patch.object(
            cartography.intel.supabase.projects,
            "get_database_posture",
            return_value={},
        ),
        # Every project-scoped child endpoint is unavailable, which keeps this test
        # about the fan-out rather than about child ingestion.
        patch.object(cartography.intel.supabase.apikeys, "get", return_value=None),
        patch.object(
            cartography.intel.supabase.apikeys, "get_signing_keys", return_value=None
        ),
        patch.object(cartography.intel.supabase.functions, "get", return_value=None),
        patch.object(
            cartography.intel.supabase.functions, "get_secrets", return_value=None
        ),
        patch.object(cartography.intel.supabase.storage, "get", return_value=None),
        patch.object(cartography.intel.supabase.auth, "get", return_value=None),
        patch.object(
            cartography.intel.supabase.auth, "get_sso_providers", return_value=None
        ),
        patch.object(
            cartography.intel.supabase.auth, "get_third_party_auth", return_value=None
        ),
        patch.object(cartography.intel.supabase.network, "get", return_value=None),
        patch.object(
            cartography.intel.supabase.network, "get_custom_hostname", return_value=None
        ),
        patch.object(cartography.intel.supabase.branches, "get", return_value=None),
        patch.object(cartography.intel.supabase.advisors, "get", return_value=None),
    ):
        cartography.intel.supabase.start_supabase_ingestion(
            neo4j_session,
            _config(update_tag, organizations),
        )


def test_orchestration_keeps_projects_created_by_other_members(neo4j_session):
    """
    A project created by another organization member is absent from /v1/projects but
    present in the organization listing. It must be ingested, and above all it must
    survive the cascading project cleanup: treating it as deleted would destroy its
    whole subtree on every sync.
    """
    # Act
    _run(
        neo4j_session,
        TEST_UPDATE_TAG,
        tests.data.supabase.projects.SUPABASE_ORG_PROJECTS["projects"],
    )

    # Assert all three organization projects exist, including the shared one that the
    # enrichment listing never returned.
    assert check_nodes(neo4j_session, "SupabaseProject", ["id"]) == {
        ("nuclearplantdbaaaaaa",),
        ("kwikemartdbbbbbbbbbb",),
        ("sharedprojectdddddddd",),
    }

    # The shared project has no database object to enrich from, so no database node is
    # invented for it, while the enriched one does get its database.
    assert check_nodes(neo4j_session, "SupabaseDatabase", ["id"]) == {
        ("nuclearplantdbaaaaaa/postgres",),
        ("kwikemartdbbbbbbbbbb/postgres",),
    }


def test_orchestration_removes_projects_the_organization_no_longer_lists(
    neo4j_session,
):
    """
    A project genuinely removed from the organization must be cleaned up, together
    with its children, on the next sync.
    """
    # Arrange: a first sync with all three projects.
    all_org_projects = tests.data.supabase.projects.SUPABASE_ORG_PROJECTS["projects"]
    _run(neo4j_session, TEST_UPDATE_TAG, all_org_projects)
    assert ("sharedprojectdddddddd",) in check_nodes(
        neo4j_session, "SupabaseProject", ["id"]
    )

    # Act: the organization no longer lists the shared project.
    _run(
        neo4j_session,
        TEST_UPDATE_TAG + 1,
        [p for p in all_org_projects if p["ref"] != "sharedprojectdddddddd"],
    )

    # Assert
    remaining = {
        row[0] for row in check_nodes(neo4j_session, "SupabaseProject", ["id"])
    }
    assert "sharedprojectdddddddd" not in remaining
    assert {"nuclearplantdbaaaaaa", "kwikemartdbbbbbbbbbb"} <= remaining


def test_orchestration_organization_disappearing_between_syncs(neo4j_session):
    """
    An organization the token loses access to stops being refreshed.

    Its subtree is deliberately left in place: SupabaseOrganization declares no
    relationships of its own, so the data model generates no cleanup query for it
    (the same situation as GCPOrganization). This test pins that documented
    behaviour so a future change to it is a deliberate, visible decision.
    """
    # Arrange: both organizations sync, each with its own project.
    both_orgs = tests.data.supabase.organizations.SUPABASE_ORGANIZATIONS
    org_projects = tests.data.supabase.projects.SUPABASE_ORG_PROJECTS["projects"][:1]
    _run(neo4j_session, TEST_UPDATE_TAG, org_projects, orgs=both_orgs)
    assert check_nodes(neo4j_session, "SupabaseOrganization", ["id"]) == {
        ("simpson-corp",),
        ("burns-industries",),
    }

    # Act: the token loses access to the second organization.
    _run(
        neo4j_session,
        TEST_UPDATE_TAG + 2,
        org_projects,
        orgs=[both_orgs[0]],
    )

    # Assert: the stale organization root is still present, unrefreshed.
    record = neo4j_session.run(
        """
        MATCH (o:SupabaseOrganization {id: 'burns-industries'})
        RETURN o.lastupdated AS lastupdated
        """,
    ).single()
    assert record is not None, (
        "stale organization roots are currently retained; if root cleanup is added, "
        "this expectation must be updated deliberately"
    )
    assert record["lastupdated"] == TEST_UPDATE_TAG
