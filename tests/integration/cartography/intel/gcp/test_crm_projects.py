from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp
import cartography.intel.gcp.crm
import cartography.intel.gcp.iam
import tests.data.gcp.crm
from cartography.client.core.tx import load
from cartography.config import Config
from cartography.intel.gcp.iam import transform_org_roles
from cartography.models.gcp.crm.projects import GCPStandaloneProjectSchema
from cartography.models.gcp.iam import GCPStandalonePredefinedRoleSchema
from cartography.models.gcp.policy_bindings import GCPPolicyBindingSchema
from tests.integration import settings
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "ORG_RESOURCE_NAME": "organizations/1337",
}


def _make_fake_credentials():
    """Create a mock GCP credentials object for testing."""
    creds = MagicMock()
    creds.quota_project_id = "test-quota-project"
    creds.universe_domain = "googleapis.com"
    return creds


@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
    return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
)
@patch.object(
    cartography.intel.gcp.crm.folders,
    "get_gcp_folders",
    return_value=tests.data.gcp.crm.GCP_FOLDERS,
)
@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects",
    return_value=tests.data.gcp.crm.GCP_PROJECTS,
)
def test_sync_gcp_projects(
    _mock_get_projects, _mock_get_folders, _mock_get_orgs, neo4j_session
) -> None:
    """Test sync_gcp_projects creates project nodes with relationships to folders and org."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Sync org first
    cartography.intel.gcp.crm.orgs.sync_gcp_organizations(
        neo4j_session, TEST_UPDATE_TAG, COMMON_JOB_PARAMS
    )

    # Sync folders
    folders = cartography.intel.gcp.crm.folders.sync_gcp_folders(
        neo4j_session,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
        org_resource_name="organizations/1337",
    )

    # Sync projects
    cartography.intel.gcp.crm.projects.sync_gcp_projects(
        neo4j_session,
        "organizations/1337",
        folders,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify project nodes
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {("project-abc",)}

    # Verify project -> folder PARENT relationship
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPFolder",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("project-abc", "folders/1414")}

    # Verify folder -> org PARENT relationship (validates hierarchy)
    assert check_rels(
        neo4j_session,
        "GCPFolder",
        "id",
        "GCPOrganization",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("folders/1414", "organizations/1337")}


@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
    return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
)
@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects",
    return_value=tests.data.gcp.crm.GCP_PROJECTS_WITHOUT_PARENT,
)
def test_sync_gcp_projects_without_parent(
    _mock_get_projects, _mock_get_orgs, neo4j_session
) -> None:
    """Test sync_gcp_projects handles projects without folder parent correctly."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Sync org first
    cartography.intel.gcp.crm.orgs.sync_gcp_organizations(
        neo4j_session, TEST_UPDATE_TAG, COMMON_JOB_PARAMS
    )

    # Sync projects with no folders
    cartography.intel.gcp.crm.projects.sync_gcp_projects(
        neo4j_session,
        "organizations/1337",
        [],  # No folders
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify project nodes
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {("project-abc",)}

    # Verify no project -> folder PARENT relationship
    assert (
        check_rels(
            neo4j_session,
            "GCPProject",
            "id",
            "GCPFolder",
            "id",
            "PARENT",
            rel_direction_right=True,
        )
        == set()
    )


@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
    return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
)
@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects",
    return_value=tests.data.gcp.crm.GCP_PROJECTS_WITH_ORG_PARENT,
)
def test_sync_gcp_projects_with_org_parent(
    _mock_get_projects, _mock_get_orgs, neo4j_session
) -> None:
    """Test sync_gcp_projects handles projects with org as direct parent correctly."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Sync org first
    cartography.intel.gcp.crm.orgs.sync_gcp_organizations(
        neo4j_session, TEST_UPDATE_TAG, COMMON_JOB_PARAMS
    )

    # Sync projects with org as direct parent
    cartography.intel.gcp.crm.projects.sync_gcp_projects(
        neo4j_session,
        "organizations/1337",
        [],  # No folders
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify project nodes
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {("project-abc",)}

    # Verify project -> org PARENT relationship
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPOrganization",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("project-abc", "organizations/1337")}

    # Verify org -> project RESOURCE relationship
    assert check_rels(
        neo4j_session,
        "GCPOrganization",
        "id",
        "GCPProject",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {("organizations/1337", "project-abc")}

    # Verify no project -> folder PARENT relationship
    assert (
        check_rels(
            neo4j_session,
            "GCPProject",
            "id",
            "GCPFolder",
            "id",
            "PARENT",
            rel_direction_right=True,
        )
        == set()
    )


@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects_by_ids",
    return_value=tests.data.gcp.crm.GCP_STANDALONE_PROJECTS,
)
def test_sync_gcp_projects_by_ids_standalone(_mock_get_projects, neo4j_session) -> None:
    """A project synced directly by ID loads even with no organization in the graph."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    projects = cartography.intel.gcp.crm.projects.sync_gcp_projects_by_ids(
        neo4j_session,
        ["standalone-project"],
        TEST_UPDATE_TAG,
    )

    assert projects == tests.data.gcp.crm.GCP_STANDALONE_PROJECTS

    # Project node exists and was stamped with the update tag.
    assert check_nodes(neo4j_session, "GCPProject", ["id", "lastupdated"]) == {
        ("standalone-project", TEST_UPDATE_TAG)
    }

    # No organization was synced, so there must be no org node and no edges to one.
    assert check_nodes(neo4j_session, "GCPOrganization", ["id"]) == set()
    assert (
        check_rels(
            neo4j_session,
            "GCPOrganization",
            "id",
            "GCPProject",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == set()
    )


@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
    return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
)
@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects_by_ids",
    return_value=tests.data.gcp.crm.GCP_STANDALONE_PROJECTS_WITH_ORG_PARENT,
)
def test_sync_gcp_projects_by_ids_links_existing_parent_org(
    _mock_get_projects, _mock_get_orgs, neo4j_session
) -> None:
    """
    When a directly-synced project has an org parent that already exists in the graph,
    the optional PARENT edge is created, but the org->project RESOURCE edge (which only
    the org-based path creates) is not.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # The org node already exists (e.g. from a prior org-based sync).
    cartography.intel.gcp.crm.orgs.sync_gcp_organizations(
        neo4j_session, TEST_UPDATE_TAG, COMMON_JOB_PARAMS
    )

    cartography.intel.gcp.crm.projects.sync_gcp_projects_by_ids(
        neo4j_session,
        ["standalone-project"],
        TEST_UPDATE_TAG,
    )

    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {("standalone-project",)}

    # project -> org PARENT edge is created because the org node exists.
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPOrganization",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("standalone-project", "organizations/1337")}

    # The standalone schema has no sub-resource relationship, so no org->project
    # RESOURCE edge is created.
    assert (
        check_rels(
            neo4j_session,
            "GCPOrganization",
            "id",
            "GCPProject",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == set()
    )


@patch.object(
    cartography.intel.gcp,
    "get_gcp_credentials",
    return_value=_make_fake_credentials(),
)
@patch.object(cartography.intel.gcp, "_run_gcp_global_analysis_jobs")
@patch.object(
    cartography.intel.gcp,
    "_sync_project_resources",
    return_value=cartography.intel.gcp.GCPProjectResourcesSyncResult(
        policy_bindings_cleanup_safe=True,
    ),
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_predefined_roles",
    return_value=[
        {
            "name": "roles/owner",
            "includedPermissions": ["resourcemanager.projects.get"],
        },
    ],
)
@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects_by_ids",
    return_value=tests.data.gcp.crm.GCP_STANDALONE_PROJECTS,
)
@patch.object(cartography.intel.gcp.crm.orgs, "get_gcp_organizations")
def test_start_gcp_ingestion_standalone_project_ids(
    mock_get_orgs,
    mock_get_projects_by_ids,
    _mock_get_predefined_roles,
    mock_sync_resources,
    mock_run_analysis,
    _mock_get_creds,
    neo4j_session,
) -> None:
    """
    start_gcp_ingestion with config.gcp_project_ids set takes the standalone path:
    parses the IDs, skips org/folder discovery, syncs the projects directly, resolves
    predefined-role permissions, and reuses the shared post-sync analysis jobs.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    config = Config(
        neo4j_uri=settings.get("NEO4J_URL"),
        update_tag=TEST_UPDATE_TAG,
        # Leading/trailing spaces and a blank entry exercise the ID parsing/trim logic.
        gcp_project_ids=" standalone-project , ",
    )

    cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    # IDs are parsed with whitespace trimmed and blank entries dropped.
    mock_get_projects_by_ids.assert_called_once()
    assert mock_get_projects_by_ids.call_args.args[0] == ["standalone-project"]

    # Organization/folder discovery is bypassed entirely in this path.
    mock_get_orgs.assert_not_called()

    # The project node was loaded via the standalone path.
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {("standalone-project",)}

    # Predefined-role nodes are loaded (so GRANTS_ROLE matchlinks from policy bindings
    # can resolve), even though there is no organization in the graph.
    assert ("roles/owner",) in check_nodes(neo4j_session, "GCPRole", ["id"])

    # Project resources are synced, and the predefined-role permission map is threaded
    # through so bindings to predefined roles (roles/owner, ...) resolve to permissions.
    mock_sync_resources.assert_called_once()
    assert mock_sync_resources.call_args.kwargs["org_role_permissions_by_name"] == {
        "roles/owner": ["resourcemanager.projects.get"],
    }

    # The shared post-sync analysis jobs still run.
    mock_run_analysis.assert_called_once()


@patch.object(
    cartography.intel.gcp,
    "get_gcp_credentials",
    return_value=_make_fake_credentials(),
)
@patch.object(cartography.intel.gcp, "_run_gcp_global_analysis_jobs")
@patch.object(cartography.intel.gcp, "_sync_project_resources")
@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects_by_ids",
    return_value=[],
)
@patch.object(cartography.intel.gcp.crm.orgs, "get_gcp_organizations")
def test_start_gcp_ingestion_standalone_no_projects_returns_early(
    mock_get_orgs,
    _mock_get_projects_by_ids,
    mock_sync_resources,
    mock_run_analysis,
    _mock_get_creds,
    neo4j_session,
) -> None:
    """
    When no projects resolve for the requested IDs, the standalone path returns early:
    it neither syncs resources nor runs analysis jobs, and never falls back to org
    discovery.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    config = Config(
        neo4j_uri=settings.get("NEO4J_URL"),
        update_tag=TEST_UPDATE_TAG,
        gcp_project_ids="missing-project",
    )

    cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    mock_get_orgs.assert_not_called()
    mock_sync_resources.assert_not_called()
    mock_run_analysis.assert_not_called()


def test_standalone_predefined_role_enables_grants_role_edge(neo4j_session) -> None:
    """
    Loading predefined roles in the standalone path lets a policy binding that references
    a predefined role resolve its GRANTS_ROLE matchlink - the edge that would be missing
    if only the permission map (and not the GCPRole node) were synced.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Predefined role node, loaded exactly as the standalone path loads it.
    predefined_roles = transform_org_roles(
        [
            {
                "name": "roles/owner",
                "includedPermissions": ["resourcemanager.projects.get"],
            },
        ],
    )
    load(
        neo4j_session,
        GCPStandalonePredefinedRoleSchema(),
        predefined_roles,
        lastupdated=TEST_UPDATE_TAG,
    )

    # A standalone project to own the policy binding.
    load(
        neo4j_session,
        GCPStandaloneProjectSchema(),
        [
            {
                "projectId": "standalone-project",
                "projectNumber": "999",
                "name": "Standalone Project",
                "lifecycleState": "ACTIVE",
                "parent_org": None,
                "parent_folder": None,
            },
        ],
        lastupdated=TEST_UPDATE_TAG,
    )

    # A policy binding that grants the predefined role on the project.
    load(
        neo4j_session,
        GCPPolicyBindingSchema(),
        [
            {
                "id": "standalone-project/roles/owner",
                "role": "roles/owner",
                "resource": "standalone-project",
                "resource_type": "project",
                "members": [],
                "wif_pools": [],
                "domains": [],
                "is_public": False,
                "has_condition": False,
                "condition_title": None,
                "condition_expression": None,
            },
        ],
        lastupdated=TEST_UPDATE_TAG,
        PROJECT_ID="standalone-project",
    )

    # The GRANTS_ROLE matchlink resolved because the predefined GCPRole node exists.
    assert check_rels(
        neo4j_session,
        "GCPPolicyBinding",
        "id",
        "GCPRole",
        "id",
        "GRANTS_ROLE",
        rel_direction_right=True,
    ) == {("standalone-project/roles/owner", "roles/owner")}


@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects_by_ids",
    return_value=tests.data.gcp.crm.GCP_STANDALONE_PROJECTS_WITH_ORG_PARENT,
)
def test_sync_gcp_projects_by_ids_absent_parent_creates_no_edge(
    _mock_get_projects, neo4j_session
) -> None:
    """
    A standalone project whose parent references an org/folder that is not in the graph
    creates no PARENT edge, locking in the "skipped otherwise" matchlink behavior.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # The parent org (organizations/1337) is intentionally NOT synced, so it is absent.
    cartography.intel.gcp.crm.projects.sync_gcp_projects_by_ids(
        neo4j_session,
        ["standalone-project"],
        TEST_UPDATE_TAG,
    )

    # The project loads regardless of the missing parent.
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {("standalone-project",)}

    # The referenced parent node does not exist, so no parent node and no PARENT edge.
    assert check_nodes(neo4j_session, "GCPOrganization", ["id"]) == set()
    assert (
        check_rels(
            neo4j_session,
            "GCPProject",
            "id",
            "GCPOrganization",
            "id",
            "PARENT",
            rel_direction_right=True,
        )
        == set()
    )


@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
    return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
)
@patch.object(cartography.intel.gcp.crm.projects, "get_gcp_projects_by_ids")
def test_sync_gcp_projects_by_ids_reconciles_stale_parent_edge(
    mock_get_projects, _mock_get_orgs, neo4j_session
) -> None:
    """
    When a standalone project becomes parentless (or changes parent), its previous PARENT
    edge is reconciled away on the next sync, even though the standalone schema runs no
    scoped relationship cleanup of its own.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Org node exists so the initial PARENT edge can be created.
    cartography.intel.gcp.crm.orgs.sync_gcp_organizations(
        neo4j_session, TEST_UPDATE_TAG, COMMON_JOB_PARAMS
    )

    # First sync: the project belongs to the org, so a PARENT edge is created.
    mock_get_projects.return_value = (
        tests.data.gcp.crm.GCP_STANDALONE_PROJECTS_WITH_ORG_PARENT
    )
    cartography.intel.gcp.crm.projects.sync_gcp_projects_by_ids(
        neo4j_session,
        ["standalone-project"],
        TEST_UPDATE_TAG,
    )
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPOrganization",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("standalone-project", "organizations/1337")}

    # Second sync with a newer tag: the project is now parentless. The stale PARENT edge
    # (still stamped with the old tag) must be reconciled away.
    mock_get_projects.return_value = tests.data.gcp.crm.GCP_STANDALONE_PROJECTS
    cartography.intel.gcp.crm.projects.sync_gcp_projects_by_ids(
        neo4j_session,
        ["standalone-project"],
        TEST_UPDATE_TAG + 1,
    )
    assert (
        check_rels(
            neo4j_session,
            "GCPProject",
            "id",
            "GCPOrganization",
            "id",
            "PARENT",
            rel_direction_right=True,
        )
        == set()
    )
    # Only the edge was reconciled; the project node itself survives.
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {("standalone-project",)}
