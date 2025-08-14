from unittest.mock import patch

import cartography.intel.github.repos
from tests.data.github.repos import DIRECT_COLLABORATORS
from tests.data.github.repos import GET_REPOS
from tests.data.github.repos import OUTSIDE_COLLABORATORS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://fake.github.net/graphql/"
FAKE_API_KEY = "fake-key"
TEST_ORG = "simpsoncorp"


@patch.object(
    cartography.intel.github.repos,
    "get",
    return_value=GET_REPOS,
)
@patch.object(
    cartography.intel.github.repos,
    "_get_repo_collaborators_for_multiple_repos",
    side_effect=[DIRECT_COLLABORATORS, OUTSIDE_COLLABORATORS],
)
def test_sync_repos(mock_collabs, mock_get, neo4j_session):
    # Arrange
    cartography.intel.github.repos.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORG,
    )

    # Act - Repository nodes exist and are correctly loaded
    expected_repo_nodes = {
        ("https://github.com/simpsoncorp/sample_repo",),
        ("https://github.com/simpsoncorp/SampleRepo2",),
        ("https://github.com/cartography-cncf/cartography",),
        ("https://github.com/johndoe/personal-repo",),
        ("https://github.com/simpsoncorp/another-repo",),
    }
    actual_repo_nodes = check_nodes(neo4j_session, "GitHubRepository", ["id"])

    assert actual_repo_nodes == expected_repo_nodes

    # Act - All core repository properties are populated (no None values)
    core_properties = [
        "id",
        "name",
        "fullname",
        "description",
        "primarylanguage",
        "homepage",
        "defaultbranch",
        "defaultbranchid",
        "private",
        "disabled",
        "archived",
        "locked",
        "giturl",
        "url",
        "sshurl",
        "createdat",
        "updatedat",
    ]
    repo_properties = check_nodes(neo4j_session, "GitHubRepository", core_properties)

    assert repo_properties is not None
    assert len(repo_properties) == 5

    # Act - Specific property values for sample repository
    expected_sample_repo = (
        "https://github.com/simpsoncorp/sample_repo",
        "sample_repo",
        "simpsoncorp/sample_repo",
        "My description",
        "Python",
        "",
        "master",
        "https://github.com/simpsoncorp/sample_repo:branch_ref_id==",
        True,
        False,
        False,
        True,
        "git://github.com:simpsoncorp:sample_repo.git",  # this is incorrect but will be patched with the correct format
        "https://github.com/simpsoncorp/sample_repo",
        "git@github.com:simpsoncorp/sample_repo.git",
        "2011-02-15T18:40:15Z",
        "2020-01-02T20:10:09Z",
    )

    assert expected_sample_repo in repo_properties

    # Ensure we can transform and load GitHub repository owner nodes.
    # Ensure that repositories are connected to owners.
    # Act - Organization owner nodes
    expected_owner_nodes = {
        ("https://github.com/simpsoncorp",),
    }
    actual_owner_nodes = check_nodes(neo4j_session, "GitHubOrganization", ["id"])

    assert actual_owner_nodes == expected_owner_nodes

    # Act - User owner nodes
    expected_user_owner_nodes = {
        ("https://github.com/johndoe",),
    }
    actual_user_owner_nodes = check_nodes(neo4j_session, "GitHubUser", ["id"])

    assert expected_user_owner_nodes.issubset(actual_user_owner_nodes)

    # Act - Repository to organization owner relationships
    expected_repo_owner_rels = {
        (
            "https://github.com/simpsoncorp/SampleRepo2",
            "https://github.com/simpsoncorp",
        ),
    }
    actual_repo_owner_rels = check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "GitHubOrganization",
        "id",
        "OWNER",
        rel_direction_right=True,
    )
    assert expected_repo_owner_rels.issubset(actual_repo_owner_rels)

    # Act - Repository to user owner relationships
    expected_repo_user_owner_rels = {
        ("https://github.com/johndoe/personal-repo", "https://github.com/johndoe"),
    }
    actual_repo_user_owner_rels = check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "GitHubUser",
        "id",
        "OWNER",
        rel_direction_right=True,
    )

    assert expected_repo_user_owner_rels.issubset(actual_repo_user_owner_rels)

    # Ensure that repositories are connected to branches.
    # Act - Repository to branch relationships
    expected_branch_rels = {
        (
            "https://github.com/simpsoncorp/sample_repo",
            "master",
        ),
    }
    actual_branch_rels = check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "GitHubBranch",
        "name",
        "BRANCH",
        rel_direction_right=True,
    )

    assert expected_branch_rels.issubset(actual_branch_rels)

    # Ensure we can transform and load GitHub repository languages nodes.
    # Ensure that repositories are connected to languages.
    # Act - Programming language nodes
    expected_languages = {
        ("Python",),
        ("Makefile",),
    }
    actual_languages = check_nodes(neo4j_session, "ProgrammingLanguage", ["id"])

    assert expected_languages.issubset(actual_languages)

    # Act - Repository to programming language relationships
    expected_repo_language_rels = {
        ("https://github.com/simpsoncorp/SampleRepo2", "Python"),
    }
    actual_repo_language_rels = check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "ProgrammingLanguage",
        "id",
        "LANGUAGE",
    )

    assert expected_repo_language_rels.issubset(actual_repo_language_rels)

    # Test all collaborator permission relationships (both outside and direct).
    # Note how all the folks in the outside collaborators list are also in the direct collaborators list.
    # They have both types of relationship.
    def _collect_repo_user_rels(labels: list[str]) -> set[tuple[str, str]]:
        rels: set[tuple[str, str]] = set()
        for lbl in labels:
            rels |= check_rels(
                neo4j_session,
                "GitHubRepository",
                "id",
                "GitHubUser",
                "id",
                lbl,
                rel_direction_right=False,
            )
        return rels

    # Act - Outside collaborator relationships (all permission types)
    expected_outside = {
        (
            "https://github.com/cartography-cncf/cartography",
            "https://github.com/marco-lancini",
        ),
        (
            "https://github.com/cartography-cncf/cartography",
            "https://github.com/sachafaust",
        ),
        (
            "https://github.com/cartography-cncf/cartography",
            "https://github.com/SecPrez",
        ),
        (
            "https://github.com/cartography-cncf/cartography",
            "https://github.com/ramonpetgrave64",
        ),
        (
            "https://github.com/cartography-cncf/cartography",
            "https://github.com/roshinis78",
        ),
    }
    outside_labels = [
        "OUTSIDE_COLLAB_ADMIN",
        "OUTSIDE_COLLAB_READ",
        "OUTSIDE_COLLAB_WRITE",
        "OUTSIDE_COLLAB_TRIAGE",
        "OUTSIDE_COLLAB_MAINTAIN",
    ]
    actual_outside = _collect_repo_user_rels(outside_labels)

    assert expected_outside.issubset(actual_outside)

    # Act - Direct collaborator relationships (all permission types)
    expected_direct = {
        (
            "https://github.com/cartography-cncf/cartography",
            "https://github.com/marco-lancini",
        ),
        (
            "https://github.com/cartography-cncf/cartography",
            "https://github.com/sachafaust",
        ),
        (
            "https://github.com/cartography-cncf/cartography",
            "https://github.com/SecPrez",
        ),
        (
            "https://github.com/cartography-cncf/cartography",
            "https://github.com/ramonpetgrave64",
        ),
        (
            "https://github.com/cartography-cncf/cartography",
            "https://github.com/roshinis78",
        ),
        (
            "https://github.com/cartography-cncf/cartography",
            "https://github.com/direct_bar",
        ),
        (
            "https://github.com/cartography-cncf/cartography",
            "https://github.com/direct_baz",
        ),
        (
            "https://github.com/cartography-cncf/cartography",
            "https://github.com/direct_bat",
        ),
        ("https://github.com/simpsoncorp/SampleRepo2", "https://github.com/direct_foo"),
    }
    direct_labels = [
        "DIRECT_COLLAB_ADMIN",
        "DIRECT_COLLAB_READ",
        "DIRECT_COLLAB_WRITE",
        "DIRECT_COLLAB_TRIAGE",
        "DIRECT_COLLAB_MAINTAIN",
    ]
    actual_direct = _collect_repo_user_rels(direct_labels)

    assert expected_direct.issubset(actual_direct)

    # Arrange - Get all REQUIRES relationships for Python library testing
    all_requires = check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "PythonLibrary",
        "id",
        "REQUIRES",
    )

    # Test pinned dependencies - ensure repositories are connected to pinned Python libraries
    # Pinned libraries have version encoded in their ID (e.g. "cartography|0.1.0")
    pinned_rels = {
        (repo, lib) for (repo, lib) in all_requires if lib == "cartography|0.1.0"
    }

    assert len(pinned_rels) == 1

    # Test unpinned dependencies - ensure repositories are connected to un-pinned Python libraries
    # Unpinned libraries just use the base name without version suffix
    unpinned_rels = {
        (repo, lib) for (repo, lib) in all_requires if lib == "cartography"
    }

    assert len(unpinned_rels) == 1

    # Act - Python libraries from setup.cfg dependencies
    neo4j_rels = {(repo, lib) for (repo, lib) in all_requires if lib == "neo4j"}

    assert len(neo4j_rels) == 2

    # Act - Python libraries in multiple requirements files
    # Ensures that if the dependency has different specifiers in each file, a separate node is created for each
    okta_requires = {r for (_, r) in all_requires if r in ["okta", "okta|0.9.0"]}

    assert okta_requires == {"okta", "okta|0.9.0"}

    # Arrange - GitHub dependencies test data
    repo_url = "https://github.com/cartography-cncf/cartography"
    react_id = "react|18.2.0"
    lodash_id = "lodash"
    django_id = "django|4.2.0"
    spring_core_id = "org.springframework:spring-core|5.3.21"

    # Act - GitHub dependency nodes are correctly synced
    expected_dependency_nodes = {
        (react_id, "react", "18.2.0", "npm"),
        (lodash_id, "lodash", None, "npm"),
        (django_id, "django", "4.2.0", "pip"),
        (spring_core_id, "org.springframework:spring-core", "5.3.21", "maven"),
    }
    actual_dependency_nodes = check_nodes(
        neo4j_session, "Dependency", ["id", "name", "version", "ecosystem"]
    )

    assert actual_dependency_nodes is not None
    assert expected_dependency_nodes.issubset(actual_dependency_nodes)

    # Act - Dependencies are correctly tagged with their ecosystems
    expected_ecosystem_tags = {
        (react_id, "npm"),
        (lodash_id, "npm"),
        (django_id, "pip"),
        (spring_core_id, "maven"),
    }
    actual_ecosystem_tags = check_nodes(
        neo4j_session,
        "Dependency",
        ["id", "ecosystem"],
    )

    assert actual_ecosystem_tags is not None
    assert expected_ecosystem_tags.issubset(actual_ecosystem_tags)

    # Act - Repository to dependency relationships
    expected_repo_dependency_relations = {
        (repo_url, react_id),
        (repo_url, lodash_id),
        (repo_url, django_id),
        (repo_url, spring_core_id),
    }
    actual_repo_dependency_relations = check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "Dependency",
        "id",
        "REQUIRES",
    )

    assert actual_repo_dependency_relations is not None
    assert expected_repo_dependency_relations.issubset(actual_repo_dependency_relations)

    # Act - NPM, Python, and Maven ecosystems are supported
    expected_ecosystem_support = {
        (react_id, "npm"),
        (lodash_id, "npm"),
        (django_id, "pip"),
        (spring_core_id, "maven"),
    }
    actual_ecosystem_nodes = check_nodes(
        neo4j_session,
        "Dependency",
        ["id", "ecosystem"],
    )

    assert actual_ecosystem_nodes is not None
    assert expected_ecosystem_support.issubset(actual_ecosystem_nodes)

    # Test that DependencyGraphManifest nodes were created.
    # Test that repositories are connected to manifests.
    # Test that manifests are connected to their dependencies.
    package_json_id = f"{repo_url}#/package.json"
    requirements_txt_id = f"{repo_url}#/requirements.txt"
    pom_xml_id = f"{repo_url}#/pom.xml"

    # Act - DependencyGraphManifest nodes are created
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

    assert actual_manifest_nodes is not None
    assert expected_manifest_nodes.issubset(actual_manifest_nodes)

    # Act - Repository to manifest relationships
    expected_repo_manifest_rels = {
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

    assert actual_repo_manifest_relationships is not None
    assert expected_repo_manifest_rels.issubset(actual_repo_manifest_relationships)

    # Act - Manifest to dependency relationships
    expected_manifest_dep_rels = {
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

    assert actual_manifest_dependency_relationships is not None
    assert expected_manifest_dep_rels.issubset(actual_manifest_dependency_relationships)

    # Arrange - Dependency relationship properties test data
    expected_github_relationship_props = {
        (repo_url, react_id, "18.2.0", "/package.json"),
        (repo_url, lodash_id, "^4.17.21", "/package.json"),
        (repo_url, django_id, "==4.2.0", "/requirements.txt"),
        (repo_url, spring_core_id, "5.3.21", "/pom.xml"),
    }

    # Act - GitHub dependency relationship properties are preserved
    result = neo4j_session.run(
        """
        MATCH (repo:GitHubRepository)-[r:REQUIRES]->(dep:Dependency)
        WHERE r.manifest_path IS NOT NULL
        RETURN repo.id as repo_id, dep.id as dep_id, r.requirements as requirements, r.manifest_path as manifest_path
        ORDER BY repo.id, dep.id
        """
    )
    actual_github_relationship_props = {
        (
            record["repo_id"],
            record["dep_id"],
            record["requirements"],
            record["manifest_path"],
        )
        for record in result
    }

    assert expected_github_relationship_props.issubset(actual_github_relationship_props)
