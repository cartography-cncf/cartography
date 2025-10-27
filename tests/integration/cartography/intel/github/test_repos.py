from unittest.mock import patch

import cartography.intel.github.repos
from cartography.intel.github.util import PaginatedGraphqlData
from tests.data.github.collaborators_test_data import COLLABORATORS_TEST_REPOS
from tests.data.github.repos import DIRECT_COLLABORATORS
from tests.data.github.repos import GET_REPOS
from tests.data.github.repos import OUTSIDE_COLLABORATORS
from tests.integration.cartography.intel.github import test_users
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://fake.github.net/graphql/"


def _ensure_local_neo4j_has_test_data(neo4j_session):
    repo_data = cartography.intel.github.repos.transform(
        GET_REPOS,
        DIRECT_COLLABORATORS,
        OUTSIDE_COLLABORATORS,
    )
    cartography.intel.github.repos.load(
        neo4j_session,
        TEST_JOB_PARAMS,
        repo_data,
    )


def test_transform_and_load_repositories(neo4j_session):
    """
    Test that we can correctly transform and load GitHubRepository nodes to Neo4j.
    """
    repos_data = cartography.intel.github.repos.transform(
        GET_REPOS,
        DIRECT_COLLABORATORS,
        OUTSIDE_COLLABORATORS,
    )
    cartography.intel.github.repos.load_github_repos(
        neo4j_session,
        TEST_UPDATE_TAG,
        repos_data["repos"],
    )
    nodes = neo4j_session.run(
        "MATCH(repo:GitHubRepository) RETURN repo.id",
    )
    actual_nodes = {n["repo.id"] for n in nodes}
    expected_nodes = {
        "https://github.com/simpsoncorp/sample_repo",
        "https://github.com/simpsoncorp/SampleRepo2",
        "https://github.com/cartography-cncf/cartography",
    }
    assert actual_nodes == expected_nodes


def test_transform_and_load_repository_owners(neo4j_session):
    """
    Ensure we can transform and load GitHub repository owner nodes.
    """
    repos_data = cartography.intel.github.repos.transform(
        GET_REPOS,
        DIRECT_COLLABORATORS,
        OUTSIDE_COLLABORATORS,
    )
    cartography.intel.github.repos.load_github_owners(
        neo4j_session,
        TEST_UPDATE_TAG,
        repos_data["repo_owners"],
    )
    nodes = neo4j_session.run(
        "MATCH(owner:GitHubOrganization) RETURN owner.id",
    )
    actual_nodes = {n["owner.id"] for n in nodes}
    expected_nodes = {
        "https://github.com/simpsoncorp",
    }
    assert actual_nodes == expected_nodes


def test_transform_and_load_repository_languages(neo4j_session):
    """
    Ensure we can transform and load GitHub repository languages nodes.
    """
    repos_data = cartography.intel.github.repos.transform(
        GET_REPOS,
        DIRECT_COLLABORATORS,
        OUTSIDE_COLLABORATORS,
    )
    cartography.intel.github.repos.load_github_languages(
        neo4j_session,
        TEST_UPDATE_TAG,
        repos_data["repo_languages"],
    )
    nodes = neo4j_session.run(
        "MATCH(pl:ProgrammingLanguage) RETURN pl.id",
    )
    actual_nodes = {n["pl.id"] for n in nodes}
    expected_nodes = {
        "Python",
        "Makefile",
    }
    assert actual_nodes == expected_nodes


def test_repository_to_owners(neo4j_session):
    """
    Ensure that repositories are connected to owners.
    """
    _ensure_local_neo4j_has_test_data(neo4j_session)
    query = """
    MATCH(owner:GitHubOrganization)<-[:OWNER]-(repo:GitHubRepository{id:$RepositoryId})
    RETURN owner.username, repo.id, repo.name
    """
    expected_repository_id = "https://github.com/simpsoncorp/SampleRepo2"
    nodes = neo4j_session.run(
        query,
        RepositoryId=expected_repository_id,
    )
    actual_nodes = {
        (
            n["owner.username"],
            n["repo.id"],
            n["repo.name"],
        )
        for n in nodes
    }

    expected_nodes = {
        (
            "SimpsonCorp",
            "https://github.com/simpsoncorp/SampleRepo2",
            "SampleRepo2",
        ),
    }
    assert actual_nodes == expected_nodes


def test_repository_to_branches(neo4j_session):
    """
    Ensure that repositories are connected to branches.
    """
    _ensure_local_neo4j_has_test_data(neo4j_session)
    query = """
    MATCH(branch:GitHubBranch)<-[:BRANCH]-(repo:GitHubRepository{id:$RepositoryId})
    RETURN branch.name, repo.id, repo.name
    """
    expected_repository_id = "https://github.com/simpsoncorp/sample_repo"
    nodes = neo4j_session.run(
        query,
        RepositoryId=expected_repository_id,
    )
    actual_nodes = {
        (
            n["branch.name"],
            n["repo.id"],
            n["repo.name"],
        )
        for n in nodes
    }

    expected_nodes = {
        (
            "master",
            "https://github.com/simpsoncorp/sample_repo",
            "sample_repo",
        ),
    }
    assert actual_nodes == expected_nodes


def test_repository_to_languages(neo4j_session):
    """
    Ensure that repositories are connected to languages.
    """
    _ensure_local_neo4j_has_test_data(neo4j_session)
    query = """
    MATCH(lang:ProgrammingLanguage)<-[:LANGUAGE]-(repo:GitHubRepository{id:$RepositoryId})
    RETURN lang.name, repo.id, repo.name
    """
    expected_repository_id = "https://github.com/simpsoncorp/SampleRepo2"
    nodes = neo4j_session.run(
        query,
        RepositoryId=expected_repository_id,
    )
    actual_nodes = {
        (
            n["lang.name"],
            n["repo.id"],
            n["repo.name"],
        )
        for n in nodes
    }

    expected_nodes = {
        (
            "Python",
            "https://github.com/simpsoncorp/SampleRepo2",
            "SampleRepo2",
        ),
    }
    assert actual_nodes == expected_nodes


def test_repository_to_collaborators(neo4j_session):
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Ensure outside collaborators are connected to the expected repos
    nodes = neo4j_session.run(
        """
    MATCH (repo:GitHubRepository)<-[rel]-(user:GitHubUser)
    WHERE type(rel) STARTS WITH 'OUTSIDE_COLLAB_'
    RETURN repo.name, type(rel), user.username
    """,
    )
    actual_nodes = {
        (
            n["repo.name"],
            n["type(rel)"],
            n["user.username"],
        )
        for n in nodes
    }
    expected_nodes = {
        (
            "cartography",
            "OUTSIDE_COLLAB_WRITE",
            "marco-lancini",
        ),
        (
            "cartography",
            "OUTSIDE_COLLAB_READ",
            "sachafaust",
        ),
        (
            "cartography",
            "OUTSIDE_COLLAB_ADMIN",
            "SecPrez",
        ),
        (
            "cartography",
            "OUTSIDE_COLLAB_TRIAGE",
            "ramonpetgrave64",
        ),
        (
            "cartography",
            "OUTSIDE_COLLAB_MAINTAIN",
            "roshinis78",
        ),
    }
    assert actual_nodes == expected_nodes

    # Ensure direct collaborators are connected to the expected repos
    # Note how all the folks in the outside collaborators list are also in the direct collaborators list.  They
    # have both types of relationship.
    nodes = neo4j_session.run(
        """
        MATCH (repo:GitHubRepository)<-[rel]-(user:GitHubUser)
        WHERE type(rel) STARTS WITH 'DIRECT_COLLAB_'
        RETURN repo.name, type(rel), user.username
        """,
    )
    actual_nodes = {
        (
            n["repo.name"],
            n["type(rel)"],
            n["user.username"],
        )
        for n in nodes
    }
    expected_nodes = {
        (
            "SampleRepo2",
            "DIRECT_COLLAB_ADMIN",
            "direct_foo",
        ),
        (
            "cartography",
            "DIRECT_COLLAB_WRITE",
            "marco-lancini",
        ),
        (
            "cartography",
            "DIRECT_COLLAB_READ",
            "sachafaust",
        ),
        (
            "cartography",
            "DIRECT_COLLAB_ADMIN",
            "SecPrez",
        ),
        (
            "cartography",
            "DIRECT_COLLAB_TRIAGE",
            "ramonpetgrave64",
        ),
        (
            "cartography",
            "DIRECT_COLLAB_MAINTAIN",
            "roshinis78",
        ),
        (
            "cartography",
            "DIRECT_COLLAB_WRITE",
            "direct_bar",
        ),
        (
            "cartography",
            "DIRECT_COLLAB_READ",
            "direct_baz",
        ),
        (
            "cartography",
            "DIRECT_COLLAB_MAINTAIN",
            "direct_bat",
        ),
    }
    assert actual_nodes == expected_nodes


def test_pinned_python_library_to_repo(neo4j_session):
    """
    Ensure that repositories are connected to pinned Python libraries stated as dependencies in requirements.txt.
    Create the path (:RepoA)-[:REQUIRES{specifier:"0.1.0"}]->(:PythonLibrary{'Cartography'})<-[:REQUIRES]-(:RepoB),
    and verify that exactly 1 repo is connected to the PythonLibrary with a specifier (RepoA).
    """
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Note: don't query for relationship attributes in code that needs to be fast.
    query = """
    MATCH (repo:GitHubRepository)-[r:REQUIRES]->(lib:PythonLibrary{id:'cartography|0.1.0'})
    WHERE lib.version = "0.1.0"
    RETURN count(repo) as repo_count
    """
    nodes = neo4j_session.run(query)
    actual_nodes = {n["repo_count"] for n in nodes}
    expected_nodes = {1}
    assert actual_nodes == expected_nodes


def test_upinned_python_library_to_repo(neo4j_session):
    """
    Ensure that repositories are connected to un-pinned Python libraries stated as dependencies in requirements.txt.
    That is, create the path
    (:RepoA)-[r:REQUIRES{specifier:"0.1.0"}]->(:PythonLibrary{'Cartography'})<-[:REQUIRES]-(:RepoB),
    and verify that exactly 1 repo is connected to the PythonLibrary without using a pinned specifier (RepoB).
    """
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Note: don't query for relationship attributes in code that needs to be fast.
    query = """
    MATCH (repo:GitHubRepository)-[r:REQUIRES]->(lib:PythonLibrary{id:'cartography'})
    WHERE r.specifier is NULL
    RETURN count(repo) as repo_count
    """
    nodes = neo4j_session.run(query)
    actual_nodes = {n["repo_count"] for n in nodes}
    expected_nodes = {1}
    assert actual_nodes == expected_nodes


def test_setup_cfg_library_to_repo(neo4j_session):
    """
    Ensure that repositories are connected to Python libraries stated as dependencies in setup.cfg.
    and verify that exactly 2 repos are connected to the PythonLibrary.
    """
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Note: don't query for relationship attributes in code that needs to be fast.
    query = """
    MATCH (repo:GitHubRepository)-[r:REQUIRES]->(lib:PythonLibrary{id:'neo4j'})
    RETURN count(repo) as repo_count
    """
    nodes = neo4j_session.run(query)
    actual_nodes = {n["repo_count"] for n in nodes}
    expected_nodes = {2}
    assert actual_nodes == expected_nodes


def test_python_library_in_multiple_requirements_files(neo4j_session):
    """
    Ensure that repositories are connected to Python libraries stated as dependencies in
    both setup.cfg and requirements.txt. Ensures that if the dependency has different
    specifiers in each file, a separate node is created for each.
    """
    _ensure_local_neo4j_has_test_data(neo4j_session)

    query = """
    MATCH (repo:GitHubRepository)-[r:REQUIRES]->(lib:PythonLibrary{name:'okta'})
    RETURN lib.id as lib_ids
    """
    nodes = neo4j_session.run(query)
    node_ids = {n["lib_ids"] for n in nodes}
    assert len(node_ids) == 2
    assert node_ids == {"okta", "okta|0.9.0"}


@patch.object(cartography.intel.github.repos, "get")
@patch.object(cartography.intel.github.repos, "_get_repo_collaborators")
def test_collabs_sync(mock_repo_collaborators, mock_get_repos, neo4j_session):
    """
    Test that collaborators are synced correctly.
    See https://cloud-native.slack.com/archives/C080M2LRLDA/p1758092875954949.
    """
    # Arrange
    # Setup test users in Neo4j
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

    # Assert
    # Use check_rels to verify correct collaborator relationships
    # Get all DIRECT_COLLAB_ADMIN relationships
    all_admin_rels = check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "GitHubUser",
        "username",
        "DIRECT_COLLAB_ADMIN",
        rel_direction_right=False,  # User <-[DIRECT_COLLAB_ADMIN]- Repo
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
    assert (
        repo1_admin_rels == expected_repo1_rels
    ), f"Repo1 should have only hjsimpson as ADMIN, got: {repo1_admin_rels}"

    # Get all DIRECT_COLLAB_WRITE relationships
    all_write_rels = check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "GitHubUser",
        "username",
        "DIRECT_COLLAB_WRITE",
        rel_direction_right=False,  # User <-[DIRECT_COLLAB_WRITE]- Repo
    )

    # Filter to only our test repositories
    repo2_write_rels = {
        rel for rel in all_write_rels if rel[0] == "https://github.com/testorg/repo2"
    }

    # Repo2 should have WRITE relationship with lmsimpson only
    expected_repo2_rels = {("https://github.com/testorg/repo2", "lmsimpson")}
    assert (
        repo2_write_rels == expected_repo2_rels
    ), f"Repo2 should have only lmsimpson as WRITE, got: {repo2_write_rels}"

    # Critical test: Verify repo2 does NOT have hjsimpson as ADMIN (this would fail with the bug)
    # The bug would cause repo2 to also have hjsimpson with ADMIN permission
    assert (
        repo2_admin_rels == set()
    ), f"Repo2 should NOT have any ADMIN collaborators, got: {repo2_admin_rels}"


def test_sync_github_dependencies_end_to_end(neo4j_session):
    """
    Test that GitHub dependencies are correctly synced from GitHub's dependency graph to Neo4j.
    This tests the complete end-to-end flow following the cartography integration test pattern.
    """
    # Arrange - Set up test data (this calls the full transform and load pipeline)
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # _ensure_local_neo4j_has_test_data has already called sync, now we test that the sync worked. Mock GitHub API data should
    # be transofrmed and in the Neo4j database.

    # Create expected IDs with format: canonical_name|requirements
    repo_url = "https://github.com/cartography-cncf/cartography"
    react_id = "react|18.2.0"
    lodash_id = "lodash"
    django_id = "django|= 4.2.0"
    spring_core_id = "org.springframework:spring-core|5.3.21"

    # Assert - Test that new GitHub dependency graph nodes were created
    # Note: Database also contains legacy Python dependencies, so we check subset
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
    assert actual_dependency_nodes is not None
    assert expected_github_dependency_nodes.issubset(actual_dependency_nodes)

    # Assert - Test that dependencies are correctly tagged with their ecosystems
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

    # Assert - Test that repositories are connected to new GitHub dependencies
    expected_github_repo_dependency_relationships = {
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
    assert actual_repo_dependency_relationships is not None
    assert expected_github_repo_dependency_relationships.issubset(
        actual_repo_dependency_relationships
    )

    # Assert - Test that NPM, Python, and Maven ecosystems are supported
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

    # Assert - Test that GitHub dependency relationship properties are preserved
    expected_github_relationship_props = {
        (
            repo_url,
            react_id,
            "18.2.0",
            "/package.json",
        ),
        (
            repo_url,
            lodash_id,
            None,
            "/package.json",
        ),
        (
            repo_url,
            django_id,
            "= 4.2.0",
            "/requirements.txt",
        ),  # Preserves original requirements format
        (
            repo_url,
            spring_core_id,
            "5.3.21",
            "/pom.xml",
        ),
    }

    # Query only GitHub dependency graph relationships (those with manifest_path)
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

    # Assert - Test that DependencyGraphManifest nodes were created
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
    assert actual_manifest_nodes is not None
    assert expected_manifest_nodes.issubset(actual_manifest_nodes)

    # Assert - Test that repositories are connected to manifests
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
    assert actual_repo_manifest_relationships is not None
    assert expected_repo_manifest_relationships.issubset(
        actual_repo_manifest_relationships
    )

    # Assert - Test that manifests are connected to their dependencies
    expected_manifest_dependency_relationships = {
        (package_json_id, react_id),
        (package_json_id, lodash_id),
        (requirements_txt_id, django_id),
        (pom_xml_id, spring_core_id),  # Maven dependency from test data
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
    assert expected_manifest_dependency_relationships.issubset(
        actual_manifest_dependency_relationships
    )
