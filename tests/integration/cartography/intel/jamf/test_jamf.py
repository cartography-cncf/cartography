import cartography.intel.jamf.computers
import tests.data.jamf.computers

TEST_UPDATE_TAG = 123456789


def test_load_jamf_computer_group_data(neo4j_session):
    _ensure_local_neo4j_has_test_computergroup_data(neo4j_session)

    # Test that the Redshift cluster node was created
    expected_nodes = {
        123,
        234,
        345,
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:JamfComputerGroup) RETURN n.id;
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == expected_nodes


def _ensure_local_neo4j_has_test_computergroup_data(neo4j_session):
    """Pre-load the Neo4j instance with test computer group data"""
    groups = tests.data.jamf.computers.GROUPS
    cartography.intel.jamf.computers.load_computer_groups(
        groups,
        neo4j_session,
        TEST_UPDATE_TAG,
    )
