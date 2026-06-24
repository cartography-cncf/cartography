from copy import deepcopy
from unittest.mock import patch

import pytest

import cartography.intel.github.repos
from cartography.intel.github.repos import enrich_dependencies_with_lockfile_versions
from cartography.intel.github.repos import load_github_dependencies
from cartography.intel.github.util import PaginatedGraphqlData
from tests.data.github.collaborators_test_data import COLLABORATORS_TEST_REPOS
from tests.data.github.repos import DEP_MANIFESTS_BY_URL
from tests.data.github.repos import DIRECT_COLLABORATORS
from tests.data.github.repos import GET_REPOS
from tests.data.github.repos import OUTSIDE_COLLABORATORS
from tests.integration.cartography.intel.github import test_users
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://fake.github.net/graphql/"
TEST_GITHUB_ORG = "simpsoncorp"
FAKE_API_KEY = "asdf"


@pytest.fixture(autouse=True)
def _no_lockfile_fetch():
    """
    By default, the lockfile fallback finds no lockfiles, so sync() never touches
    the network. Tests that exercise the fallback patch get_file_content themselves.
    """
    with patch.object(
        cartography.intel.github.repos,
        "get_file_content",
        return_value=None,
    ):
        yield


@patch.object(
    cartography.intel.github.repos,
    "_get_dep_manifests_for_repos",
    return_value=(DEP_MANIFESTS_BY_URL, True),
)
@patch.object(
    cartography.intel.github.repos,
    "get",
    return_value=GET_REPOS,
)
@patch.object(
    cartography.intel.github.repos,
    "_get_repo_collaborators_for_multiple_repos",
)
def test_sync_github_repos(
    mock_get_collabs, mock_get_repos, mock_get_dep_manifests, neo4j_session
):
    """
    Test that GitHub repos sync correctly, creating proper nodes and relationships.
    """

    # Arrange - Mock collaborator retrieval to return test data
    def collabs_side_effect(repo_raw_data, affiliation, org, api_url, token):
        if affiliation == "DIRECT":
            return DIRECT_COLLABORATORS
        else:
            return OUTSIDE_COLLABORATORS

    mock_get_collabs.side_effect = collabs_side_effect

    # Act
    cartography.intel.github.repos.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
    )

    # Assert - Verify GitHubRepository nodes were created
    assert check_nodes(neo4j_session, "GitHubRepository", ["id"]) == {
        ("https://github.com/simpsoncorp/sample_repo",),
        ("https://github.com/simpsoncorp/SampleRepo2",),
        ("https://github.com/cartography-cncf/cartography",),
    }

    # Assert - Verify GitHubOrganization nodes were created
    assert check_nodes(neo4j_session, "GitHubOrganization", ["id"]) == {
        ("https://github.com/simpsoncorp",),
    }

    # Assert - Verify ProgrammingLanguage nodes were created
    assert check_nodes(neo4j_session, "ProgrammingLanguage", ["id"]) == {
        ("Python",),
        ("Makefile",),
    }

    # Assert - Verify OWNER relationships
    assert check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "GitHubOrganization",
        "id",
        "OWNER",
        rel_direction_right=True,
    ) == {
        (
            "https://github.com/simpsoncorp/sample_repo",
            "https://github.com/simpsoncorp",
        ),
        (
            "https://github.com/simpsoncorp/SampleRepo2",
            "https://github.com/simpsoncorp",
        ),
        (
            "https://github.com/cartography-cncf/cartography",
            "https://github.com/simpsoncorp",
        ),
    }

    # Assert - Verify BRANCH relationships
    assert check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "GitHubBranch",
        "name",
        "BRANCH",
        rel_direction_right=True,
    ) == {
        ("https://github.com/simpsoncorp/sample_repo", "master"),
        ("https://github.com/simpsoncorp/SampleRepo2", "master"),
        ("https://github.com/cartography-cncf/cartography", "master"),
    }

    # Assert - Verify LANGUAGE relationships
    assert check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "ProgrammingLanguage",
        "name",
        "LANGUAGE",
        rel_direction_right=True,
    ) == {
        ("https://github.com/simpsoncorp/sample_repo", "Python"),
        ("https://github.com/simpsoncorp/SampleRepo2", "Python"),
        ("https://github.com/cartography-cncf/cartography", "Python"),
        ("https://github.com/cartography-cncf/cartography", "Makefile"),
    }


@patch.object(
    cartography.intel.github.repos,
    "_get_dep_manifests_for_repos",
    return_value=(DEP_MANIFESTS_BY_URL, True),
)
@patch.object(
    cartography.intel.github.repos,
    "get",
    return_value=GET_REPOS,
)
@patch.object(
    cartography.intel.github.repos,
    "_get_repo_collaborators_for_multiple_repos",
)
def test_sync_github_repo_collaborators(
    mock_get_collabs, mock_get_repos, mock_get_dep_manifests, neo4j_session
):
    """
    Test that GitHub repo collaborators sync correctly with proper relationships.
    """

    # Arrange
    def collabs_side_effect(repo_raw_data, affiliation, org, api_url, token):
        if affiliation == "DIRECT":
            return DIRECT_COLLABORATORS
        else:
            return OUTSIDE_COLLABORATORS

    mock_get_collabs.side_effect = collabs_side_effect

    # Act
    cartography.intel.github.repos.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
    )

    # Assert - Verify outside collaborator relationships
    # OUTSIDE_COLLAB_WRITE
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "username",
        "GitHubRepository",
        "name",
        "OUTSIDE_COLLAB_WRITE",
        rel_direction_right=True,
    ) == {
        ("marco-lancini", "cartography"),
    }

    # OUTSIDE_COLLAB_READ
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "username",
        "GitHubRepository",
        "name",
        "OUTSIDE_COLLAB_READ",
        rel_direction_right=True,
    ) == {
        ("sachafaust", "cartography"),
    }

    # OUTSIDE_COLLAB_ADMIN
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "username",
        "GitHubRepository",
        "name",
        "OUTSIDE_COLLAB_ADMIN",
        rel_direction_right=True,
    ) == {
        ("SecPrez", "cartography"),
    }

    # OUTSIDE_COLLAB_TRIAGE
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "username",
        "GitHubRepository",
        "name",
        "OUTSIDE_COLLAB_TRIAGE",
        rel_direction_right=True,
    ) == {
        ("ramonpetgrave64", "cartography"),
    }

    # OUTSIDE_COLLAB_MAINTAIN
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "username",
        "GitHubRepository",
        "name",
        "OUTSIDE_COLLAB_MAINTAIN",
        rel_direction_right=True,
    ) == {
        ("roshinis78", "cartography"),
    }

    # Assert - Verify direct collaborator relationships
    # DIRECT_COLLAB_ADMIN
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "username",
        "GitHubRepository",
        "name",
        "DIRECT_COLLAB_ADMIN",
        rel_direction_right=True,
    ) == {
        ("direct_foo", "SampleRepo2"),
        ("SecPrez", "cartography"),
    }

    # DIRECT_COLLAB_WRITE
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "username",
        "GitHubRepository",
        "name",
        "DIRECT_COLLAB_WRITE",
        rel_direction_right=True,
    ) == {
        ("marco-lancini", "cartography"),
        ("direct_bar", "cartography"),
    }

    # DIRECT_COLLAB_READ
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "username",
        "GitHubRepository",
        "name",
        "DIRECT_COLLAB_READ",
        rel_direction_right=True,
    ) == {
        ("sachafaust", "cartography"),
        ("direct_baz", "cartography"),
    }

    # DIRECT_COLLAB_TRIAGE
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "username",
        "GitHubRepository",
        "name",
        "DIRECT_COLLAB_TRIAGE",
        rel_direction_right=True,
    ) == {
        ("ramonpetgrave64", "cartography"),
    }

    # DIRECT_COLLAB_MAINTAIN
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "username",
        "GitHubRepository",
        "name",
        "DIRECT_COLLAB_MAINTAIN",
        rel_direction_right=True,
    ) == {
        ("roshinis78", "cartography"),
        ("direct_bat", "cartography"),
    }


@patch.object(
    cartography.intel.github.repos,
    "_get_dep_manifests_for_repos",
    return_value=(DEP_MANIFESTS_BY_URL, True),
)
@patch.object(
    cartography.intel.github.repos,
    "get",
    return_value=GET_REPOS,
)
@patch.object(
    cartography.intel.github.repos,
    "_get_repo_collaborators_for_multiple_repos",
)
def test_sync_github_dependencies(
    mock_get_collabs, mock_get_repos, mock_get_dep_manifests, neo4j_session
):
    """
    Test that GitHub dependencies from dependency graph are correctly synced.
    """

    # Arrange
    def collabs_side_effect(repo_raw_data, affiliation, org, api_url, token):
        if affiliation == "DIRECT":
            return DIRECT_COLLABORATORS
        else:
            return OUTSIDE_COLLABORATORS

    mock_get_collabs.side_effect = collabs_side_effect

    # Act
    cartography.intel.github.repos.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
    )

    # Assert - Verify Dependency nodes from GitHub dependency graph
    repo_url = "https://github.com/cartography-cncf/cartography"
    react_id = "react|18.2.0"
    lodash_id = "lodash"
    django_id = "django|= 4.2.0"
    spring_core_id = "org.springframework:spring-core|5.3.21"

    expected_github_dependency_nodes = {
        (react_id, "react", "18.2.0", "npm"),
        (lodash_id, "lodash", None, "npm"),
        (django_id, "django", "= 4.2.0", "pip"),
        (spring_core_id, "org.springframework:spring-core", "5.3.21", "maven"),
    }
    actual_dependency_nodes = check_nodes(
        neo4j_session,
        "Dependency",
        ["id", "name", "requirements", "ecosystem"],
    )
    assert expected_github_dependency_nodes.issubset(actual_dependency_nodes)

    # Assert - Verify REQUIRES relationships
    expected_repo_dependency_relationships = {
        (repo_url, react_id),
        (repo_url, lodash_id),
        (repo_url, django_id),
        (repo_url, spring_core_id),
    }
    actual_repo_dependency_relationships = check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "Dependency",
        "id",
        "REQUIRES",
    )
    assert expected_repo_dependency_relationships.issubset(
        actual_repo_dependency_relationships
    )

    # Assert - Verify new ontology fields (normalized_id, version, type, purl)
    expected_ontology_fields = {
        (react_id, "npm|react|18.2.0", "18.2.0", "npm", "pkg:npm/react@18.2.0"),
        (lodash_id, None, None, None, None),
        (django_id, "pypi|django|4.2.0", "4.2.0", "pypi", "pkg:pypi/django@4.2.0"),
        (
            spring_core_id,
            "maven|org.springframework/spring-core|5.3.21",
            "5.3.21",
            "maven",
            "pkg:maven/org.springframework/spring-core@5.3.21",
        ),
    }
    actual_ontology_fields = check_nodes(
        neo4j_session,
        "Dependency",
        ["id", "normalized_id", "version", "type", "purl"],
    )
    assert expected_ontology_fields.issubset(actual_ontology_fields)


@patch.object(
    cartography.intel.github.repos,
    "get_file_content",
    return_value='{"packages": {"node_modules/lodash": {"version": "4.17.21"}}}',
)
@patch.object(
    cartography.intel.github.repos,
    "_get_dep_manifests_for_repos",
    return_value=(DEP_MANIFESTS_BY_URL, True),
)
@patch.object(
    cartography.intel.github.repos,
    "get",
    return_value=GET_REPOS,
)
@patch.object(
    cartography.intel.github.repos,
    "_get_repo_collaborators_for_multiple_repos",
)
def test_sync_github_dependencies_lockfile_fallback(
    mock_get_collabs,
    mock_get_repos,
    mock_get_dep_manifests,
    mock_get_file_content,
    neo4j_session,
):
    """
    The range-only `lodash` dependency (no exact version in the dependency graph)
    is upgraded to an exact version from package-lock.json: the loaded Dependency
    node gains a version and a normalized_id and is tagged source="lockfile".
    """

    def collabs_side_effect(repo_raw_data, affiliation, org, api_url, token):
        return (
            DIRECT_COLLABORATORS if affiliation == "DIRECT" else OUTSIDE_COLLABORATORS
        )

    mock_get_collabs.side_effect = collabs_side_effect

    cartography.intel.github.repos.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
    )

    # lodash had no exact version from the dependency graph; the lockfile recovers it.
    expected = {
        ("lodash", "4.17.21", "npm|lodash|4.17.21", "lockfile", "exact"),
    }
    actual = check_nodes(
        neo4j_session,
        "Dependency",
        ["id", "version", "normalized_id", "source", "version_confidence"],
    )
    assert expected.issubset(actual)


def test_load_dependencies_shared_id_lockfile_conflict_not_corrupted(neo4j_session):
    """
    Two manifests reference the same `lodash|^4.0.0` but their co-located lockfiles
    pin different exact versions. They load into a single shared Dependency node
    (keyed by id), so enrichment must decline: the loaded node keeps a null
    normalized_id rather than being silently pinned to one manifest's version.
    """
    shared_id = "lodash|^4.0.0"
    dependencies = [
        {
            "id": shared_id,
            "name": "lodash",
            "original_name": "lodash",
            "requirements": "^4.0.0",
            "ecosystem": "npm",
            "package_manager": "NPM",
            "manifest_file": "package.json",
            "manifest_path": "/package.json",
            "manifest_id": "https://github.com/test-org/monorepo#/package.json",
            "repo_url": "https://github.com/test-org/monorepo",
            "version": None,
            "type": None,
            "purl": None,
            "normalized_id": None,
            "source": "dependency_graph",
            "version_confidence": "range",
        },
        {
            "id": shared_id,
            "name": "lodash",
            "original_name": "lodash",
            "requirements": "^4.0.0",
            "ecosystem": "npm",
            "package_manager": "NPM",
            "manifest_file": "package.json",
            "manifest_path": "/services/api/package.json",
            "manifest_id": "https://github.com/test-org/monorepo#/services/api/package.json",
            "repo_url": "https://github.com/test-org/monorepo",
            "version": None,
            "type": None,
            "purl": None,
            "normalized_id": None,
            "source": "dependency_graph",
            "version_confidence": "range",
        },
    ]

    lockfiles = {
        "package-lock.json": '{"packages": {"node_modules/lodash": {"version": "4.17.21"}}}',
        "services/api/package-lock.json": '{"packages": {"node_modules/lodash": {"version": "3.10.1"}}}',
    }

    def fake_get_file_content(token, owner, repo, path, base_url):
        return lockfiles.get(path)

    with patch.object(
        cartography.intel.github.repos,
        "get_file_content",
        side_effect=fake_get_file_content,
    ):
        enrich_dependencies_with_lockfile_versions(
            dependencies, FAKE_API_KEY, TEST_GITHUB_URL
        )

    load_github_dependencies(neo4j_session, TEST_UPDATE_TAG, dependencies)

    # Exactly one shared node, and it was not pinned to either conflicting version.
    rows = neo4j_session.run(
        "MATCH (d:Dependency {id: $id}) RETURN d.normalized_id AS nid, d.version AS version",
        id=shared_id,
    ).data()
    assert len(rows) == 1
    assert rows[0]["nid"] is None
    assert rows[0]["version"] is None


def test_load_dependencies_shared_id_exact_conflict_not_corrupted(neo4j_session):
    """
    Two manifests resolve the same `lodash|^4.0.0` to different exact versions
    directly from the dependency graph (no lockfile). They merge into one node,
    so the loader's reconciliation clears the exact version and the node carries a
    null normalized_id rather than being pinned to one manifest's version.
    """
    shared_id = "lodash|^4.0.0"
    dependencies = [
        {
            "id": shared_id,
            "name": "lodash",
            "original_name": "lodash",
            "requirements": "^4.0.0",
            "ecosystem": "npm",
            "package_manager": "NPM",
            "manifest_file": "package.json",
            "manifest_path": "/package.json",
            "manifest_id": "https://github.com/test-org/monorepo#/package.json",
            "repo_url": "https://github.com/test-org/monorepo",
            "version": "4.17.21",
            "type": "npm",
            "purl": "pkg:npm/lodash@4.17.21",
            "normalized_id": "npm|lodash|4.17.21",
            "source": "dependency_graph",
            "version_confidence": "exact",
        },
        {
            "id": shared_id,
            "name": "lodash",
            "original_name": "lodash",
            "requirements": "^4.0.0",
            "ecosystem": "npm",
            "package_manager": "NPM",
            "manifest_file": "package.json",
            "manifest_path": "/services/api/package.json",
            "manifest_id": "https://github.com/test-org/monorepo#/services/api/package.json",
            "repo_url": "https://github.com/test-org/monorepo",
            "version": "3.10.1",
            "type": "npm",
            "purl": "pkg:npm/lodash@3.10.1",
            "normalized_id": "npm|lodash|3.10.1",
            "source": "dependency_graph",
            "version_confidence": "exact",
        },
    ]

    load_github_dependencies(neo4j_session, TEST_UPDATE_TAG, dependencies)

    rows = neo4j_session.run(
        "MATCH (d:Dependency {id: $id}) RETURN d.normalized_id AS nid, d.version AS version",
        id=shared_id,
    ).data()
    assert len(rows) == 1
    assert rows[0]["nid"] is None
    assert rows[0]["version"] is None


@patch.object(
    cartography.intel.github.repos,
    "_get_dep_manifests_for_repos",
    return_value=(DEP_MANIFESTS_BY_URL, True),
)
@patch.object(
    cartography.intel.github.repos,
    "get",
    return_value=GET_REPOS,
)
@patch.object(
    cartography.intel.github.repos,
    "_get_repo_collaborators_for_multiple_repos",
)
def test_sync_github_manifests(
    mock_get_collabs, mock_get_repos, mock_get_dep_manifests, neo4j_session
):
    """
    Test that GitHub dependency manifests are correctly synced.
    """

    # Arrange
    def collabs_side_effect(repo_raw_data, affiliation, org, api_url, token):
        if affiliation == "DIRECT":
            return DIRECT_COLLABORATORS
        else:
            return OUTSIDE_COLLABORATORS

    mock_get_collabs.side_effect = collabs_side_effect

    # Act
    cartography.intel.github.repos.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
    )

    # Assert - Verify DependencyGraphManifest nodes
    repo_url = "https://github.com/cartography-cncf/cartography"
    package_json_id = f"{repo_url}#/package.json"
    requirements_txt_id = f"{repo_url}#/requirements.txt"
    pom_xml_id = f"{repo_url}#/pom.xml"

    expected_manifest_nodes = {
        (package_json_id, "/package.json", "package.json", 2, repo_url),
        (requirements_txt_id, "/requirements.txt", "requirements.txt", 1, repo_url),
        (pom_xml_id, "/pom.xml", "pom.xml", 1, repo_url),
    }
    actual_manifest_nodes = check_nodes(
        neo4j_session,
        "DependencyGraphManifest",
        ["id", "blob_path", "filename", "dependencies_count", "repo_url"],
    )
    assert expected_manifest_nodes.issubset(actual_manifest_nodes)

    # Assert - Verify HAS_MANIFEST relationships
    expected_repo_manifest_relationships = {
        (repo_url, package_json_id),
        (repo_url, requirements_txt_id),
        (repo_url, pom_xml_id),
    }
    actual_repo_manifest_relationships = check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "DependencyGraphManifest",
        "id",
        "HAS_MANIFEST",
    )
    assert expected_repo_manifest_relationships.issubset(
        actual_repo_manifest_relationships
    )

    # Assert - Verify HAS_DEP relationships between manifests and dependencies
    react_id = "react|18.2.0"
    lodash_id = "lodash"
    django_id = "django|= 4.2.0"
    spring_core_id = "org.springframework:spring-core|5.3.21"

    expected_manifest_dependency_relationships = {
        (package_json_id, react_id),
        (package_json_id, lodash_id),
        (requirements_txt_id, django_id),
        (pom_xml_id, spring_core_id),
    }
    actual_manifest_dependency_relationships = check_rels(
        neo4j_session,
        "DependencyGraphManifest",
        "id",
        "Dependency",
        "id",
        "HAS_DEP",
    )
    assert expected_manifest_dependency_relationships.issubset(
        actual_manifest_dependency_relationships
    )


@patch.object(
    cartography.intel.github.repos,
    "_get_dep_manifests_for_repos",
    return_value=(DEP_MANIFESTS_BY_URL, True),
)
@patch.object(
    cartography.intel.github.repos,
    "get",
    return_value=GET_REPOS,
)
@patch.object(
    cartography.intel.github.repos,
    "_get_repo_collaborators_for_multiple_repos",
)
def test_sync_github_branch_protection_rules(
    mock_get_collabs, mock_get_repos, mock_get_dep_manifests, neo4j_session
):
    """
    Test that GitHub branch protection rules are correctly synced.
    """

    # Arrange
    def collabs_side_effect(repo_raw_data, affiliation, org, api_url, token):
        if affiliation == "DIRECT":
            return DIRECT_COLLABORATORS
        else:
            return OUTSIDE_COLLABORATORS

    mock_get_collabs.side_effect = collabs_side_effect

    # Act
    cartography.intel.github.repos.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
    )

    # Assert - Verify GitHubBranchProtectionRule nodes
    repo_url = "https://github.com/cartography-cncf/cartography"
    branch_protection_rule_id = "BPR_kwDOAbc123=="

    expected_branch_protection_rule_nodes = {
        (branch_protection_rule_id, "main", False, True, 2),
    }
    actual_branch_protection_rule_nodes = check_nodes(
        neo4j_session,
        "GitHubBranchProtectionRule",
        [
            "id",
            "pattern",
            "allows_deletions",
            "requires_approving_reviews",
            "required_approving_review_count",
        ],
    )
    assert expected_branch_protection_rule_nodes.issubset(
        actual_branch_protection_rule_nodes
    )

    # Assert - Verify HAS_RULE relationships
    expected_repo_branch_protection_rule_relationships = {
        (repo_url, branch_protection_rule_id),
    }
    actual_repo_branch_protection_rule_relationships = check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "GitHubBranchProtectionRule",
        "id",
        "HAS_RULE",
    )
    assert expected_repo_branch_protection_rule_relationships.issubset(
        actual_repo_branch_protection_rule_relationships
    )


@patch.object(
    cartography.intel.github.repos,
    "_get_dep_manifests_for_repos",
    return_value=(DEP_MANIFESTS_BY_URL, True),
)
@patch.object(
    cartography.intel.github.repos,
    "get",
    return_value=GET_REPOS,
)
@patch.object(
    cartography.intel.github.repos,
    "_get_repo_collaborators_for_multiple_repos",
)
def test_sync_github_rulesets(
    mock_get_collabs, mock_get_repos, mock_get_dep_manifests, neo4j_session
):
    """
    Test that GitHub repository rulesets and rules are correctly synced.
    """

    def collabs_side_effect(repo_raw_data, affiliation, org, api_url, token):
        if affiliation == "DIRECT":
            return DIRECT_COLLABORATORS
        else:
            return OUTSIDE_COLLABORATORS

    mock_get_collabs.side_effect = collabs_side_effect

    cartography.intel.github.repos.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
    )

    repo_url = "https://github.com/cartography-cncf/cartography"
    ruleset_id = "RRS_lACkVXNlcs4AXenizgBRqVA"

    expected_ruleset_nodes = {
        (ruleset_id, "production-ruleset", "BRANCH", "ACTIVE"),
    }
    actual_ruleset_nodes = check_nodes(
        neo4j_session,
        "GitHubRuleset",
        ["id", "name", "target", "enforcement"],
    )
    assert actual_ruleset_nodes == expected_ruleset_nodes

    assert (repo_url, ruleset_id) in check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "GitHubRuleset",
        "id",
        "HAS_RULESET",
    )

    assert ("https://github.com/simpsoncorp", ruleset_id) in check_rels(
        neo4j_session,
        "GitHubOrganization",
        "id",
        "GitHubRuleset",
        "id",
        "RESOURCE",
    )

    actual_rule_nodes = check_nodes(
        neo4j_session,
        "GitHubRulesetRule",
        [
            "id",
            "type",
            "parameters_required_approving_review_count",
            "parameters_require_code_owner_review",
        ],
    )
    expected_rule_nodes = {
        ("RRU_kwDORule001", "DELETION", None, None),
        ("RRU_kwDORule002", "PULL_REQUEST", 2, True),
        ("RRU_kwDORule003", "REQUIRED_STATUS_CHECKS", None, None),
    }
    assert actual_rule_nodes == expected_rule_nodes

    assert (ruleset_id, "RRU_kwDORule002") in check_rels(
        neo4j_session,
        "GitHubRuleset",
        "id",
        "GitHubRulesetRule",
        "id",
        "CONTAINS_RULE",
    )


@patch.object(
    cartography.intel.github.repos,
    "_get_dep_manifests_for_repos",
    return_value=(DEP_MANIFESTS_BY_URL, True),
)
@patch.object(cartography.intel.github.repos, "get")
@patch.object(
    cartography.intel.github.repos,
    "_get_repo_collaborators_for_multiple_repos",
)
def test_sync_github_rulesets_cleanup(
    mock_get_collabs, mock_get_repos, mock_get_dep_manifests, neo4j_session
):
    """
    Test that ruleset cleanup is org-scoped.
    """

    def collabs_side_effect(repo_raw_data, affiliation, org, api_url, token):
        if affiliation == "DIRECT":
            return DIRECT_COLLABORATORS
        else:
            return OUTSIDE_COLLABORATORS

    mock_get_collabs.side_effect = collabs_side_effect

    mock_get_repos.return_value = GET_REPOS

    cartography.intel.github.repos.sync(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
    )

    repos_without_rulesets = deepcopy(GET_REPOS)
    repos_without_rulesets[2]["rulesets"] = {"nodes": []}
    mock_get_repos.return_value = repos_without_rulesets

    cartography.intel.github.repos.sync(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1},
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
    )

    assert check_nodes(neo4j_session, "GitHubRuleset", ["id"]) == set()
    assert check_nodes(neo4j_session, "GitHubRulesetRule", ["id"]) == set()


@patch.object(
    cartography.intel.github.repos,
    "_get_dep_manifests_for_repos",
    return_value=({}, True),
)
@patch.object(cartography.intel.github.repos, "get")
@patch.object(cartography.intel.github.repos, "_get_repo_collaborators")
def test_sync_collaborators_per_repo(
    mock_repo_collaborators, mock_get_repos, mock_get_dep_manifests, neo4j_session
):
    """
    Test that collaborators are synced correctly per repository.
    Verifies that collaborator permissions are not incorrectly shared across repos.
    See https://cloud-native.slack.com/archives/C080M2LRLDA/p1758092875954949.
    """
    # Arrange - Setup test users in Neo4j
    test_users._ensure_local_neo4j_has_test_data(neo4j_session)

    # Use test repo data from external file
    mock_get_repos.return_value = COLLABORATORS_TEST_REPOS

    def collaborators_side_effect(*args):
        repo = args[3]
        affiliation = args[4]

        if affiliation == "OUTSIDE":
            return PaginatedGraphqlData(nodes=[], edges=[])

        # Return different collaborators for each repo
        if repo == "repo1":
            nodes = [
                {
                    "url": "https://github.com/hjsimpson",
                    "login": "hjsimpson",
                    "name": "Homer Simpson",
                    "email": "homer@example.com",
                    "company": None,
                }
            ]
            edges = [{"permission": "ADMIN"}]
        elif repo == "repo2":
            nodes = [
                {
                    "url": "https://github.com/lmsimpson",
                    "login": "lmsimpson",
                    "name": "Lisa Simpson",
                    "email": "lisa@example.com",
                    "company": None,
                }
            ]
            edges = [{"permission": "WRITE"}]
        else:
            nodes = []
            edges = []

        return PaginatedGraphqlData(nodes=nodes, edges=edges)

    mock_repo_collaborators.side_effect = collaborators_side_effect

    # Act
    cartography.intel.github.repos.sync(
        neo4j_session, TEST_JOB_PARAMS, "some_key", "http://localhost", "testorg"
    )

    # Assert - Get all DIRECT_COLLAB_ADMIN relationships
    all_admin_rels = check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "GitHubUser",
        "username",
        "DIRECT_COLLAB_ADMIN",
        rel_direction_right=False,
    )

    # Filter to only our test repositories
    repo1_admin_rels = {
        rel for rel in all_admin_rels if rel[0] == "https://github.com/testorg/repo1"
    }
    repo2_admin_rels = {
        rel for rel in all_admin_rels if rel[0] == "https://github.com/testorg/repo2"
    }

    # Repo1 should have ADMIN relationship with hjsimpson only
    expected_repo1_rels = {("https://github.com/testorg/repo1", "hjsimpson")}
    assert repo1_admin_rels == expected_repo1_rels

    # Get all DIRECT_COLLAB_WRITE relationships
    all_write_rels = check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "GitHubUser",
        "username",
        "DIRECT_COLLAB_WRITE",
        rel_direction_right=False,
    )

    # Filter to only our test repositories
    repo2_write_rels = {
        rel for rel in all_write_rels if rel[0] == "https://github.com/testorg/repo2"
    }

    # Repo2 should have WRITE relationship with lmsimpson only
    expected_repo2_rels = {("https://github.com/testorg/repo2", "lmsimpson")}
    assert repo2_write_rels == expected_repo2_rels

    # Critical test: Verify repo2 does NOT have hjsimpson as ADMIN
    assert repo2_admin_rels == set()


@patch.object(
    cartography.intel.github.repos,
    "_get_dep_manifests_for_repos",
    return_value=(DEP_MANIFESTS_BY_URL, True),
)
@patch.object(
    cartography.intel.github.repos,
    "get",
    return_value=GET_REPOS,
)
@patch.object(
    cartography.intel.github.repos,
    "_get_repo_collaborators_for_multiple_repos",
)
def test_sync_github_python_requirements(
    mock_get_collabs, mock_get_repos, mock_get_dep_manifests, neo4j_session
):
    """
    Test that Python requirements from requirements.txt and setup.cfg are synced.
    Note: repos with dependencyGraphManifests skip requirements.txt/setup.cfg parsing.
    """

    # Arrange
    def collabs_side_effect(repo_raw_data, affiliation, org, api_url, token):
        if affiliation == "DIRECT":
            return DIRECT_COLLABORATORS
        else:
            return OUTSIDE_COLLABORATORS

    mock_get_collabs.side_effect = collabs_side_effect

    # Act
    cartography.intel.github.repos.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
    )

    # Assert - Verify PythonLibrary nodes were created
    # sample_repo and SampleRepo2 have requirements.txt/setup.cfg but no dependencyGraphManifests
    # cartography has dependencyGraphManifests so it skips requirements.txt/setup.cfg parsing
    expected_python_libraries = {
        ("cartography",),
        ("cartography|0.1.0",),
        ("neo4j",),
        ("okta",),
        ("okta|0.9.0",),
    }
    actual_python_libraries = check_nodes(neo4j_session, "PythonLibrary", ["id"])
    assert expected_python_libraries.issubset(actual_python_libraries)

    # Assert - Verify REQUIRES relationships for Python libraries
    sample_repo_url = "https://github.com/simpsoncorp/sample_repo"
    expected_requires_rels = {
        (sample_repo_url, "cartography"),
        (sample_repo_url, "cartography|0.1.0"),
        (sample_repo_url, "neo4j"),
        (sample_repo_url, "okta"),
        (sample_repo_url, "okta|0.9.0"),
    }
    actual_requires_rels = check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "PythonLibrary",
        "id",
        "REQUIRES",
    )
    assert expected_requires_rels.issubset(actual_requires_rels)
