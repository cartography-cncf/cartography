import cartography.intel.github
from tests.data.github.repos import DIRECT_COLLABORATORS
from tests.data.github.repos import GET_REPOS
from tests.data.github.repos import OUTSIDE_COLLABORATORS


TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {'UPDATE_TAG': TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://fake.github.net/graphql/"


def _ensure_local_neo4j_has_test_data(neo4j_session):
    repo_data = cartography.intel.github.repos.transform(GET_REPOS, DIRECT_COLLABORATORS, OUTSIDE_COLLABORATORS)
    cartography.intel.github.repos.load(
        neo4j_session,
        TEST_JOB_PARAMS,
        repo_data,
    )


def test_transform_and_load_repositories(neo4j_session):
    """
    Test that we can correctly transform and load GitHubRepository nodes to Neo4j.
    """
    repos_data = cartography.intel.github.repos.transform(GET_REPOS, DIRECT_COLLABORATORS, OUTSIDE_COLLABORATORS)
    cartography.intel.github.repos.load_github_repos(
        neo4j_session,
        TEST_UPDATE_TAG,
        repos_data['repos'],
    )
    nodes = neo4j_session.run(
        "MATCH(repo:GitHubRepository) RETURN repo.id",
    )
    actual_nodes = {n['repo.id'] for n in nodes}
    expected_nodes = {
        "https://github.com/example_org/sample_repo",
        "https://github.com/example_org/SampleRepo2",
        "https://github.com/lyft/cartography",
    }
    assert actual_nodes == expected_nodes


def test_transform_and_load_repository_owners(neo4j_session):
    """
    Ensure we can transform and load GitHub repository owner nodes.
    """
    repos_data = cartography.intel.github.repos.transform(GET_REPOS, DIRECT_COLLABORATORS, OUTSIDE_COLLABORATORS)
    cartography.intel.github.repos.load_github_owners(
        neo4j_session,
        TEST_UPDATE_TAG,
        repos_data['repo_owners'],
    )
    nodes = neo4j_session.run(
        "MATCH(owner:GitHubOrganization) RETURN owner.id",
    )
    actual_nodes = {n['owner.id'] for n in nodes}
    expected_nodes = {
        'https://github.com/example_org',
    }
    assert actual_nodes == expected_nodes


def test_transform_and_load_repository_languages(neo4j_session):
    """
    Ensure we can transform and load GitHub repository languages nodes.
    """
    repos_data = cartography.intel.github.repos.transform(GET_REPOS, DIRECT_COLLABORATORS, OUTSIDE_COLLABORATORS)
    cartography.intel.github.repos.load_github_languages(
        neo4j_session,
        TEST_UPDATE_TAG,
        repos_data['repo_languages'],
    )
    nodes = neo4j_session.run(
        "MATCH(pl:ProgrammingLanguage) RETURN pl.id",
    )
    actual_nodes = {n['pl.id'] for n in nodes}
    expected_nodes = {
        'Python', 'Makefile',
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
    expected_repository_id = 'https://github.com/example_org/SampleRepo2'
    nodes = neo4j_session.run(
        query,
        RepositoryId=expected_repository_id,
    )
    actual_nodes = {
        (
            n['owner.username'],
            n['repo.id'],
            n['repo.name'],
        ) for n in nodes
    }

    expected_nodes = {
        (
            'example_org',
            'https://github.com/example_org/SampleRepo2',
            'SampleRepo2',
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
    expected_repository_id = 'https://github.com/example_org/sample_repo'
    nodes = neo4j_session.run(
        query,
        RepositoryId=expected_repository_id,
    )
    actual_nodes = {
        (
            n['branch.name'],
            n['repo.id'],
            n['repo.name'],
        ) for n in nodes
    }

    expected_nodes = {
        (
            'master',
            'https://github.com/example_org/sample_repo',
            'sample_repo',
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
    expected_repository_id = 'https://github.com/example_org/SampleRepo2'
    nodes = neo4j_session.run(
        query,
        RepositoryId=expected_repository_id,
    )
    actual_nodes = {
        (
            n['lang.name'],
            n['repo.id'],
            n['repo.name'],
        ) for n in nodes
    }

    expected_nodes = {
        (
            'Python',
            'https://github.com/example_org/SampleRepo2',
            'SampleRepo2',
        ),
    }
    assert actual_nodes == expected_nodes


def test_repository_to_collaborators(neo4j_session):
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Ensure outside collaborators are connected to the expected repos
    nodes = neo4j_session.run("""
    MATCH (repo:GitHubRepository)<-[rel]-(user:GitHubUser)
    WHERE type(rel) STARTS WITH 'OUTSIDE_COLLAB_'
    RETURN repo.name, type(rel), user.username
    """)
    actual_nodes = {
        (
            n['repo.name'],
            n['type(rel)'],
            n['user.username'],
        ) for n in nodes
    }
    expected_nodes = {
        (
            'cartography',
            'OUTSIDE_COLLAB_WRITE',
            'marco-lancini',
        ),
        (
            'cartography',
            'OUTSIDE_COLLAB_READ',
            'sachafaust',
        ),
        (
            'cartography',
            'OUTSIDE_COLLAB_ADMIN',
            'SecPrez',
        ),
        (
            'cartography',
            'OUTSIDE_COLLAB_TRIAGE',
            'ramonpetgrave64',
        ),
        (
            'cartography',
            'OUTSIDE_COLLAB_MAINTAIN',
            'roshinis78',
        ),
    }
    assert actual_nodes == expected_nodes

    # Ensure direct collaborators are connected to the expected repos
    # Note how all the folks in the outside collaborators list are also in the direct collaborators list.  They
    # have both types of relationship.
    nodes = neo4j_session.run("""
        MATCH (repo:GitHubRepository)<-[rel]-(user:GitHubUser)
        WHERE type(rel) STARTS WITH 'DIRECT_COLLAB_'
        RETURN repo.name, type(rel), user.username
        """)
    actual_nodes = {
        (
            n['repo.name'],
            n['type(rel)'],
            n['user.username'],
        ) for n in nodes
    }
    expected_nodes = {
        (
            'SampleRepo2',
            'DIRECT_COLLAB_ADMIN',
            'direct_foo',
        ),
        (
            'cartography',
            'DIRECT_COLLAB_WRITE',
            'marco-lancini',
        ),
        (
            'cartography',
            'DIRECT_COLLAB_READ',
            'sachafaust',
        ),
        (
            'cartography',
            'DIRECT_COLLAB_ADMIN',
            'SecPrez',
        ),
        (
            'cartography',
            'DIRECT_COLLAB_TRIAGE',
            'ramonpetgrave64',
        ),
        (
            'cartography',
            'DIRECT_COLLAB_MAINTAIN',
            'roshinis78',
        ),
        (
            'cartography',
            'DIRECT_COLLAB_WRITE',
            'direct_bar',
        ),
        (
            'cartography',
            'DIRECT_COLLAB_READ',
            'direct_baz',
        ),
        (
            'cartography',
            'DIRECT_COLLAB_MAINTAIN',
            'direct_bat',
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
    actual_nodes = {n['repo_count'] for n in nodes}
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
    actual_nodes = {n['repo_count'] for n in nodes}
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
    actual_nodes = {n['repo_count'] for n in nodes}
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
    node_ids = {n['lib_ids'] for n in nodes}
    assert len(node_ids) == 2
    assert node_ids == {'okta', 'okta|0.9.0'}
