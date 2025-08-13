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
    # Act - setup data using the sync function
    cartography.intel.github.repos.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORG,
    )

    # Assert if all repository nodes and relationships are created as expected
    _test_repository_nodes(neo4j_session)  # GitHubRepository nodes
    _test_owner_nodes_and_relationships(
        neo4j_session
    )  # GitHubRepository -[:OWNER]-> GitHubOrganization/GitHubUser
    _test_branch_relationships(
        neo4j_session
    )  # GitHubRepository -[:BRANCH]-> GitHubBranch
    _test_language_relationships(
        neo4j_session
    )  # GitHubRepository -[:LANGUAGE]-> ProgrammingLanguage
    _test_collaborator_relationships(
        neo4j_session
    )  # GitHubUser -[:DIRECT_COLLAB_*, OUTSIDE_COLLAB_*]-> GitHubRepository
    _test_python_dependencies(
        neo4j_session
    )  # GitHubRepository -[:REQUIRES]-> PythonLibrary
    _test_github_dependencies(
        neo4j_session
    )  # GitHubRepository -[:REQUIRES]-> Dependency
    _test_dependency_manifests(
        neo4j_session
    )  # GitHubRepository -[:HAS_MANIFEST]-> DependencyGraphManifest -[:HAS_DEP]-> Dependency
    _test_dependency_relationship_properties(
        neo4j_session
    )  # REQUIRES relationship properties


def _test_repository_nodes(neo4j_session):
    """
    Test that we correctly transform and load GitHubRepository nodes to Neo4j.
    Tests all repository properties to ensure complete coverage.
    """
    # Test repository nodes exist
    expected_repo_nodes = {
        ("https://github.com/simpsoncorp/sample_repo",),
        ("https://github.com/simpsoncorp/SampleRepo2",),
        ("https://github.com/cartography-cncf/cartography",),
        ("https://github.com/johndoe/personal-repo",),
        ("https://github.com/simpsoncorp/another-repo",),
    }
    actual_repo_nodes = check_nodes(neo4j_session, "GitHubRepository", ["id"])
    assert actual_repo_nodes == expected_repo_nodes

    # Test all core repository properties are populated (no None values)
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

    # Verify no essential properties are None
    for repo_data in repo_properties:
        essential_props = repo_data[:17]  # All properties except optional ones
        assert all(
            prop is not None for prop in essential_props[:1]
        ), "ID should not be None"
        assert all(
            prop is not None for prop in essential_props[1:7]
        ), "Core text properties should not be None"
        assert all(
            isinstance(prop, bool) for prop in essential_props[8:12]
        ), "Boolean flags should be boolean"
        assert all(
            prop is not None for prop in essential_props[12:17]
        ), "URL and date properties should not be None"

    # Test specific property values for sample repository
    sample_repo = next(
        props
        for props in repo_properties
        if props[0] == "https://github.com/simpsoncorp/sample_repo"
    )
    (
        repo_id,
        name,
        fullname,
        description,
        primarylang,
        homepage,
        defaultbranch,
        defaultbranchid,
        private,
        disabled,
        archived,
        locked,
        giturl,
        url,
        sshurl,
        createdat,
        updatedat,
    ) = sample_repo

    # Validate all properties have expected values
    assert repo_id == "https://github.com/simpsoncorp/sample_repo"
    assert name == "sample_repo"
    assert fullname == "simpsoncorp/sample_repo"
    assert description == "My description"
    assert primarylang == "Python"
    assert homepage == ""
    assert defaultbranch == "master"
    assert (
        defaultbranchid == "https://github.com/simpsoncorp/sample_repo:branch_ref_id=="
    )
    assert private is True
    assert disabled is False
    assert archived is False
    assert locked is True
    # assert giturl == "git://github.com:simpsoncorp:sample_repo.git"  buggy url conversion
    assert url == "https://github.com/simpsoncorp/sample_repo"
    assert sshurl == "git@github.com:simpsoncorp/sample_repo.git"
    assert createdat == "2011-02-15T18:40:15Z"
    assert updatedat == "2020-01-02T20:10:09Z"


def _test_owner_nodes_and_relationships(neo4j_session):
    """
    Ensure we can transform and load GitHub repository owner nodes.
    Ensure that repositories are connected to owners.
    """
    # Assert - Organization owners
    expected_owner_nodes = {
        ("https://github.com/simpsoncorp",),
    }
    actual_owner_nodes = check_nodes(neo4j_session, "GitHubOrganization", ["id"])
    assert actual_owner_nodes == expected_owner_nodes

    # Assert - User owners
    expected_user_owner_nodes = {
        ("https://github.com/johndoe",),
    }
    actual_user_owner_nodes = check_nodes(neo4j_session, "GitHubUser", ["id"])
    assert expected_user_owner_nodes.issubset(
        actual_user_owner_nodes
    )  # Subset because users from collaborators also exist

    # Assert - Repository to organization owners relationship
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

    # Assert - Repository to user owners relationship
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


def _test_branch_relationships(neo4j_session):
    """
    Ensure that repositories are connected to branches.
    """
    expected_branch_rels = {
        ("https://github.com/simpsoncorp/sample_repo",),
    }
    branch_query = """
        MATCH (branch:GitHubBranch)<-[:BRANCH]-(repo:GitHubRepository{id:$RepositoryId})
        RETURN repo.id
        """
    nodes = neo4j_session.run(
        branch_query, RepositoryId="https://github.com/simpsoncorp/sample_repo"
    )
    assert {(n["repo.id"],) for n in nodes} == expected_branch_rels


def _test_language_relationships(neo4j_session):
    """
    Ensure we can transform and load GitHub repository languages nodes.
    Ensure that repositories are connected to languages.
    """
    expected_languages = {
        ("Python",),
        ("Makefile",),
    }
    actual_languages = check_nodes(neo4j_session, "ProgrammingLanguage", ["id"])
    assert expected_languages.issubset(actual_languages)

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


def _test_collaborator_relationships(neo4j_session):
    """
    Test all collaborator permission relationships (both outside and direct).
    Note how all the folks in the outside collaborators list are also in the direct collaborators list.
    They have both types of relationship.
    """
    # Assert - Outside collaborators
    expected_outside = {
        ("cartography", "OUTSIDE_COLLAB_WRITE", "marco-lancini"),
        ("cartography", "OUTSIDE_COLLAB_READ", "sachafaust"),
        ("cartography", "OUTSIDE_COLLAB_ADMIN", "SecPrez"),
        ("cartography", "OUTSIDE_COLLAB_TRIAGE", "ramonpetgrave64"),
        ("cartography", "OUTSIDE_COLLAB_MAINTAIN", "roshinis78"),
    }
    nodes = neo4j_session.run(
        """
        MATCH (repo:GitHubRepository)<-[rel]-(user:GitHubUser)
        WHERE type(rel) STARTS WITH 'OUTSIDE_COLLAB_'
        RETURN repo.name, type(rel), user.username
        """
    )
    actual_outside = {
        (n["repo.name"], n["type(rel)"], n["user.username"]) for n in nodes
    }
    assert actual_outside == expected_outside

    # Assert - Direct collaborators
    expected_direct = {
        ("SampleRepo2", "DIRECT_COLLAB_ADMIN", "direct_foo"),
        ("cartography", "DIRECT_COLLAB_WRITE", "marco-lancini"),
        ("cartography", "DIRECT_COLLAB_READ", "sachafaust"),
        ("cartography", "DIRECT_COLLAB_ADMIN", "SecPrez"),
        ("cartography", "DIRECT_COLLAB_TRIAGE", "ramonpetgrave64"),
        ("cartography", "DIRECT_COLLAB_MAINTAIN", "roshinis78"),
        ("cartography", "DIRECT_COLLAB_WRITE", "direct_bar"),
        ("cartography", "DIRECT_COLLAB_READ", "direct_baz"),
        ("cartography", "DIRECT_COLLAB_MAINTAIN", "direct_bat"),
    }
    nodes = neo4j_session.run(
        """
        MATCH (repo:GitHubRepository)<-[rel]-(user:GitHubUser)
        WHERE type(rel) STARTS WITH 'DIRECT_COLLAB_'
        RETURN repo.name, type(rel), user.username
        """
    )
    actual_direct = {
        (n["repo.name"], n["type(rel)"], n["user.username"]) for n in nodes
    }
    assert actual_direct == expected_direct


def _test_python_dependencies(neo4j_session):
    """
    Ensure that repositories are connected to pinned Python libraries stated as dependencies in requirements.txt.
    Create the path (:RepoA)-[:REQUIRES{specifier:"0.1.0"}]->(:PythonLibrary{'Cartography'})<-[:REQUIRES]-(:RepoB),
    and verify that exactly 1 repo is connected to the PythonLibrary with a specifier (RepoA).

    Ensure that repositories are connected to un-pinned Python libraries stated as dependencies in requirements.txt.
    That is, create the path (:RepoA)-[r:REQUIRES{specifier:"0.1.0"}]->(:PythonLibrary{'Cartography'})<-[:REQUIRES]-(:RepoB),
    and verify that exactly 1 repo is connected to the PythonLibrary without using a pinned specifier (RepoB).

    Ensure that repositories are connected to Python libraries stated as dependencies in setup.cfg
    and verify that exactly 2 repos are connected to the PythonLibrary.

    Ensure that repositories are connected to Python libraries stated as dependencies in
    both setup.cfg and requirements.txt. Ensures that if the dependency has different
    specifiers in each file, a separate node is created for each.
    """
    # Act - Test pinned dependencies
    query_pinned = """
        MATCH (repo:GitHubRepository)-[r:REQUIRES]->(lib:PythonLibrary{id:'cartography|0.1.0'})
        WHERE lib.version = "0.1.0"
        RETURN count(repo) as repo_count
        """
    nodes = neo4j_session.run(query_pinned)
    # Assert
    assert {n["repo_count"] for n in nodes} == {1}

    # Act - Test unpinned dependencies
    query_unpinned = """
        MATCH (repo:GitHubRepository)-[r:REQUIRES]->(lib:PythonLibrary{id:'cartography'})
        WHERE r.specifier is NULL
        RETURN count(repo) as repo_count
        """
    nodes = neo4j_session.run(query_unpinned)
    # Assert
    assert {n["repo_count"] for n in nodes} == {1}

    # Act - Test setup.cfg dependencies
    query_setup_cfg = """
        MATCH (repo:GitHubRepository)-[r:REQUIRES]->(lib:PythonLibrary{id:'neo4j'})
        RETURN count(repo) as repo_count
        """
    nodes = neo4j_session.run(query_setup_cfg)
    # Assert
    assert {n["repo_count"] for n in nodes} == {2}

    # Act - Test Python libraries in multiple requirements files
    # Ensures that if the dependency has different specifiers in each file,
    # a separate node is created for each
    query_multiple_files = """
        MATCH (repo:GitHubRepository)-[r:REQUIRES]->(lib:PythonLibrary{name:'okta'})
        RETURN lib.id as lib_ids
        """
    nodes = neo4j_session.run(query_multiple_files)
    node_ids = {n["lib_ids"] for n in nodes}
    # Assert
    assert len(node_ids) == 2
    assert node_ids == {"okta", "okta|0.9.0"}


def _test_github_dependencies(neo4j_session):
    """
    Test that GitHub dependencies are correctly synced from GitHub's dependency graph to Neo4j.
    This tests the complete end-to-end flow following the cartography integration test pattern.
    """
    # Arrange
    repo_url = "https://github.com/cartography-cncf/cartography"
    react_id = "react|18.2.0"
    lodash_id = "lodash"
    django_id = "django|4.2.0"
    spring_core_id = "org.springframework:spring-core|5.3.21"

    # Act - Test dependency nodes
    expected_dependency_nodes = {
        (react_id, "react", "18.2.0", "npm"),
        (lodash_id, "lodash", None, "npm"),
        (django_id, "django", "4.2.0", "pip"),
        (spring_core_id, "org.springframework:spring-core", "5.3.21", "maven"),
    }
    actual_dependency_nodes = check_nodes(
        neo4j_session, "Dependency", ["id", "name", "version", "ecosystem"]
    )
    # Assert
    assert actual_dependency_nodes is not None
    assert expected_dependency_nodes.issubset(actual_dependency_nodes)

    # Act - Test that dependencies are correctly tagged with their ecosystems
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
    # Assert
    assert actual_ecosystem_tags is not None
    assert expected_ecosystem_tags.issubset(actual_ecosystem_tags)

    # Act - Test repository to dependency relationships
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
    # Assert
    assert actual_repo_dependency_relations is not None
    assert expected_repo_dependency_relations.issubset(actual_repo_dependency_relations)

    # Act - Test that NPM, Python, and Maven ecosystems are supported
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
    # Assert
    assert actual_ecosystem_nodes is not None
    assert expected_ecosystem_support.issubset(actual_ecosystem_nodes)


def _test_dependency_manifests(neo4j_session):
    """
    Test that DependencyGraphManifest nodes were created.
    Test that repositories are connected to manifests.
    Test that manifests are connected to their dependencies.
    """
    # Arrange
    repo_url = "https://github.com/cartography-cncf/cartography"
    react_id = "react|18.2.0"
    lodash_id = "lodash"
    django_id = "django|4.2.0"
    spring_core_id = "org.springframework:spring-core|5.3.21"

    package_json_id = f"{repo_url}#/package.json"
    requirements_txt_id = f"{repo_url}#/requirements.txt"
    pom_xml_id = f"{repo_url}#/pom.xml"

    # Act - Test manifest nodes
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
    # Assert
    assert actual_manifest_nodes is not None
    assert expected_manifest_nodes.issubset(actual_manifest_nodes)

    # Act - Test repository to manifest relationships
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
    # Assert
    assert actual_repo_manifest_relationships is not None
    assert expected_repo_manifest_rels.issubset(actual_repo_manifest_relationships)

    # Act - Test manifest to dependency relationships
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
    # Assert
    assert actual_manifest_dependency_relationships is not None
    assert expected_manifest_dep_rels.issubset(actual_manifest_dependency_relationships)


def _test_dependency_relationship_properties(neo4j_session):
    """
    Test that GitHub dependency relationship properties are preserved.
    Preserves original requirements format.
    """
    # Arrange
    repo_url = "https://github.com/cartography-cncf/cartography"
    react_id = "react|18.2.0"
    lodash_id = "lodash"
    django_id = "django|4.2.0"
    spring_core_id = "org.springframework:spring-core|5.3.21"

    expected_github_relationship_props = {
        (repo_url, react_id, "18.2.0", "/package.json"),
        (repo_url, lodash_id, "^4.17.21", "/package.json"),
        (repo_url, django_id, "==4.2.0", "/requirements.txt"),
        (repo_url, spring_core_id, "5.3.21", "/pom.xml"),
    }

    # Act
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

    # Assert
    assert expected_github_relationship_props.issubset(actual_github_relationship_props)
