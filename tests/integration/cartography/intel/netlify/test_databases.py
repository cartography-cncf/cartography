from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j
import requests

import cartography.intel.netlify.databases
import cartography.intel.netlify.sites
import tests.data.netlify.databases
import tests.data.netlify.misc
import tests.data.netlify.sites
from tests.integration.cartography.intel.netlify.common import common_job_parameters
from tests.integration.cartography.intel.netlify.common import (
    create_test_netlify_account,
)
from tests.integration.cartography.intel.netlify.common import find_secret_in_graph
from tests.integration.cartography.intel.netlify.common import TEST_ACCOUNT_ID
from tests.integration.cartography.intel.netlify.common import TEST_BASE_URL
from tests.integration.cartography.intel.netlify.common import TEST_SITE_ID
from tests.integration.cartography.intel.netlify.common import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

_BRANCH_NODE_ID = f"{TEST_SITE_ID}|production"
_SNAPSHOT_ID = "c1c17d7053c60b4be4c87501"
# The password out of the plaintext connection string the API really returns.
_DB_PASSWORD = "ElXmQJhA8559cktljB3sWQK-woJPfvbc"


@patch.object(
    cartography.intel.netlify.databases,
    "get_netlify_database_snapshots",
    return_value=tests.data.netlify.misc.NETLIFY_DATABASE_SNAPSHOTS,
)
@patch.object(
    cartography.intel.netlify.databases,
    "get_netlify_database_branches",
    return_value=tests.data.netlify.databases.NETLIFY_DATABASE_BRANCHES,
)
def test_sync_netlify_databases(
    mock_branches,
    mock_snapshots,
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    create_test_netlify_account(neo4j_session)
    cartography.intel.netlify.sites.load_netlify_sites(
        neo4j_session,
        cartography.intel.netlify.sites.transform_netlify_sites(
            tests.data.netlify.sites.NETLIFY_SITES,
        ),
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    api_session = MagicMock(spec=requests.Session)

    # Act
    cartography.intel.netlify.databases.sync_netlify_databases(
        neo4j_session,
        api_session,
        TEST_BASE_URL,
        TEST_ACCOUNT_ID,
        tests.data.netlify.sites.NETLIFY_SITES,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert Nodes: the id is site-scoped because "production" is the branch id on every
    # Netlify DB, so the raw branch_id collides across sites.
    assert check_nodes(
        neo4j_session,
        "NetlifyDatabaseBranch",
        ["id", "branch_id", "name", "state"],
    ) == {(_BRANCH_NODE_ID, "production", "production", "ready")}

    # Assert the nested compute endpoint was flattened
    assert check_nodes(
        neo4j_session,
        "NetlifyDatabaseBranch",
        [
            "compute_state",
            "compute_min_cu",
            "compute_max_cu",
            "compute_suspend_timeout_seconds",
        ],
    ) == {("active", 0.25, 0.25, 300)}

    # Assert only the role names survived, not the URLs they key
    assert neo4j_session.run(
        "MATCH (b:NetlifyDatabaseBranch) RETURN b.connection_roles AS roles",
    ).single()["roles"] == ["netlifydb_readonly"]

    # Assert Nodes: snapshots, with a name derived from the branch and point in time
    assert check_nodes(
        neo4j_session,
        "NetlifyDatabaseSnapshot",
        ["id", "name", "manual"],
    ) == {(_SNAPSHOT_ID, "production@2026-07-30T17:59:00Z", True)}

    # Assert Relationships
    assert check_rels(
        neo4j_session,
        "NetlifySite",
        "id",
        "NetlifyDatabaseBranch",
        "id",
        "HAS_DATABASE_BRANCH",
    ) == {(TEST_SITE_ID, _BRANCH_NODE_ID)}
    assert check_rels(
        neo4j_session,
        "NetlifyDatabaseBranch",
        "id",
        "NetlifyDatabaseSnapshot",
        "id",
        "HAS_SNAPSHOT",
    ) == {(_BRANCH_NODE_ID, _SNAPSHOT_ID)}

    # Assert the ontology labels and their projected properties
    assert check_nodes(
        neo4j_session,
        "Database",
        ["id", "_ont_name", "_ont_type", "_ont_encrypted", "_ont_source"],
    ) == {(_BRANCH_NODE_ID, "production", "postgres", True, "netlify")}
    assert check_nodes(
        neo4j_session,
        "Snapshot",
        ["id", "_ont_public", "_ont_encrypted", "_ont_source_id"],
    ) == {(_SNAPSHOT_ID, False, True, _BRANCH_NODE_ID)}

    # This is the point of the whole module's secret handling: the branches endpoint hands back a
    # plaintext Postgres URL, password included, and none of it may reach the graph.
    assert find_secret_in_graph(neo4j_session, _DB_PASSWORD) == []
    assert find_secret_in_graph(neo4j_session, "postgresql://") == []


def test_databases_are_only_fetched_for_sites_that_have_one(
    neo4j_session: neo4j.Session,
) -> None:
    """
    The branches and snapshots endpoints exist on every site, so without the `has_database` gate
    each site would cost two requests just to learn it has no database.
    """
    # Arrange
    create_test_netlify_account(neo4j_session)
    api_session = MagicMock(spec=requests.Session)
    without_database = [
        {**tests.data.netlify.sites.NETLIFY_SITES[0], "has_database": False},
    ]

    # Act
    with patch.object(
        cartography.intel.netlify.databases,
        "get_netlify_database_branches",
    ) as mock_branches:
        cartography.intel.netlify.databases.sync_netlify_databases(
            neo4j_session,
            api_session,
            TEST_BASE_URL,
            TEST_ACCOUNT_ID,
            without_database,
            TEST_UPDATE_TAG,
            common_job_parameters(),
        )

    # Assert
    mock_branches.assert_not_called()
