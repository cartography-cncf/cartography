from string import Template
from typing import List

import neo4j

TEST_REPO_ID = "https://github.com/org/repository"
TEST_REPO_FULL_NAME = "org/repository"
TEST_REPO_NAME = "repository"
TEST_UPDATE_TAG = 123456789


def check_nodes_as_list(
    neo4j_session: neo4j.Session, node_label: str, attrs: List[str],
):
    """
    Like tests.integration.util.check_nodes()` but returns a list instead of a set.
    """
    if not attrs:
        raise ValueError(
            "`attrs` passed to check_nodes() must have at least one element.",
        )

    attrs = ", ".join(f"n.{attr}" for attr in attrs)
    query_template = Template("MATCH (n:$NodeLabel) RETURN $Attrs")
    result = neo4j_session.run(
        query_template.safe_substitute(NodeLabel=node_label, Attrs=attrs),
    )
    return sum([row.values() for row in result], [])


def create_github_repos(neo4j_session):
    # Creates a set of GitHub repositories in the graph
    neo4j_session.run(
        """
        MERGE (repo:GitHubRepository{id: $repo_id, fullname: $repo_fullname, name: $repo_name})
        ON CREATE SET repo.firstseen = timestamp()
        SET repo.lastupdated = $update_tag
        SET repo.archived = false
        """,
        repo_id=TEST_REPO_ID,
        repo_fullname=TEST_REPO_FULL_NAME,
        update_tag=TEST_UPDATE_TAG,
        repo_name=TEST_REPO_NAME,
    )


def create_dependency_nodes(neo4j_session):
    # Creates a set of dependency nodes in the graph
    neo4j_session.run(
        """
        MERGE (dep:Dependency{id: $dep_id})
        ON CREATE SET dep.firstseen = timestamp()
        SET dep.lastupdated = $update_tag
        """,
        dep_id="moment|2.29.2",
        update_tag=TEST_UPDATE_TAG,
    )


def create_cve_nodes(neo4j_session):
    # Creates a set of CVE nodes in the graph
    neo4j_session.run(
        """
        MERGE (cve:CVE{id: $cve_id})
        ON CREATE SET cve.firstseen = timestamp()
        SET cve.lastupdated = $update_tag
        """,
        cve_id="CVE-2022-31129",
        update_tag=TEST_UPDATE_TAG,
    )
