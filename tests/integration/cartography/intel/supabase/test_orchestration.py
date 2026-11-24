"""
End-to-end tests for the module entry point.

The per-domain tests exercise each sync in isolation, which leaves the fan-out
itself untested: how projects are enumerated, and where the cascading project
cleanup sits relative to the per-project loop. Both of those are where a project
can be wrongly deleted, so they are covered here.
"""

from contextlib import ExitStack
from unittest.mock import patch

import pytest
import requests

import cartography.intel.supabase
import tests.data.supabase.apikeys
import tests.data.supabase.organizations
import tests.data.supabase.projects
from cartography.config import Config
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 987650000
TEST_ORG_SLUG = "simpson-corp"
TEST_BASE_URL = "https://api.fake-supabase.com"


# The session is module-scoped, so without this a test would see the graph the
# previous one left behind.
@pytest.fixture(autouse=True)
def _empty_graph(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _config(update_tag, organizations=None):
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        supabase_access_token="fake-token",
        # Configured with a trailing slash, which must not reach the endpoints.
        supabase_base_url=f"{TEST_BASE_URL}/",
        supabase_organizations=organizations,
    )


def _project_scoped(result, unreachable_refs):
    """
    Stub a project-scoped getter. The refs in ``unreachable_refs`` behave like a
    stopped project in production: HTTP 500 until the retries give up.
    """

    def get(api_session, base_url, project_ref):
        assert base_url == TEST_BASE_URL
        if project_ref in unreachable_refs:
            raise requests.exceptions.RetryError("too many 500 error responses")
        return result

    return get


def _project_scoped_endpoints(api_keys):
    """
    Every project-scoped getter, with what it returns for a running project. Only the
    API keys return data, which keeps these tests about the fan-out rather than about
    child ingestion.
    """
    return [
        (cartography.intel.supabase.projects, "get_settings", {}),
        (cartography.intel.supabase.projects, "get_database_posture", {}),
        (cartography.intel.supabase.apikeys, "get", api_keys),
        (cartography.intel.supabase.apikeys, "get_signing_keys", None),
        (cartography.intel.supabase.functions, "get", None),
        (cartography.intel.supabase.functions, "get_secrets", None),
        (cartography.intel.supabase.storage, "get", None),
        (cartography.intel.supabase.auth, "get", None),
        (cartography.intel.supabase.auth, "get_sso_providers", None),
        (cartography.intel.supabase.auth, "get_third_party_auth", None),
        (cartography.intel.supabase.network, "get", None),
        (cartography.intel.supabase.network, "get_custom_hostname", None),
        (cartography.intel.supabase.branches, "get", None),
        (cartography.intel.supabase.advisors, "get", None),
    ]


def _run(
    neo4j_session,
    update_tag,
    org_projects,
    orgs=None,
    organizations=None,
    api_keys=None,
    unreachable_refs=frozenset(),
):
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
        ExitStack() as stack,
    ):
        for module, name, result in _project_scoped_endpoints(api_keys):
            stack.enter_context(
                patch.object(
                    module,
                    name,
                    side_effect=_project_scoped(result, unreachable_refs),
                ),
            )
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
    # invented for it, while the enriched, running one does get its database. The
    # paused kwik-e-mart project is not read at all.
    assert check_nodes(neo4j_session, "SupabaseDatabase", ["id"]) == {
        ("nuclearplantdbaaaaaa/postgres",),
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


def test_orchestration_stopped_project_does_not_block_later_projects(neo4j_session):
    """
    A paused project has no running instance, so its project-scoped endpoints answer
    HTTP 500 until the retries give up. Reading them aborted the whole sync and left
    every project listed after the paused one unsynced. The projects around it must
    still sync, including their cleanup, while the paused project keeps the children
    it had when it last ran.
    """
    # Arrange: a first sync while the kwik-e-mart project is still running.
    org_projects = tests.data.supabase.projects.SUPABASE_ORG_PROJECTS["projects"]
    api_keys = tests.data.supabase.apikeys.SUPABASE_API_KEYS
    _run(
        neo4j_session,
        TEST_UPDATE_TAG,
        [{**p, "status": "ACTIVE_HEALTHY"} for p in org_projects],
        api_keys=api_keys,
    )

    # Act: kwik-e-mart is now paused and its endpoints fail, while every running
    # project is down to a single API key.
    _run(
        neo4j_session,
        TEST_UPDATE_TAG + 3,
        org_projects,
        api_keys=api_keys[:1],
        unreachable_refs={"kwikemartdbbbbbbbbbb"},
    )

    # Assert: the running projects lost their removed keys; the paused one kept all of
    # its keys, still attached to it.
    assert check_nodes(neo4j_session, "SupabaseApiKey", ["id"]) == {
        ("nuclearplantdbaaaaaa/key-publishable-1",),
        ("sharedprojectdddddddd/key-publishable-1",),
        ("kwikemartdbbbbbbbbbb/key-publishable-1",),
        ("kwikemartdbbbbbbbbbb/key-secret-1",),
        ("kwikemartdbbbbbbbbbb/legacy",),
        ("kwikemartdbbbbbbbbbb/service_role",),
    }
    assert check_rels(
        neo4j_session,
        "SupabaseProject",
        "id",
        "SupabaseApiKey",
        "id",
        "RESOURCE",
    ) == {
        ("nuclearplantdbaaaaaa", "nuclearplantdbaaaaaa/key-publishable-1"),
        ("sharedprojectdddddddd", "sharedprojectdddddddd/key-publishable-1"),
        ("kwikemartdbbbbbbbbbb", "kwikemartdbbbbbbbbbb/key-publishable-1"),
        ("kwikemartdbbbbbbbbbb", "kwikemartdbbbbbbbbbb/key-secret-1"),
        ("kwikemartdbbbbbbbbbb", "kwikemartdbbbbbbbbbb/legacy"),
        ("kwikemartdbbbbbbbbbb", "kwikemartdbbbbbbbbbb/service_role"),
    }
