import cartography.intel.crowdstrike.spotlight
import tests.data.crowdstrike.endpoints
import tests.data.crowdstrike.spotlight

TEST_UPDATE_TAG = 123456789


def test_load_vulnerability_data(neo4j_session, *args):
    # First load the host data, so we can test relationships
    host_data = tests.data.crowdstrike.endpoints.GET_HOSTS
    cartography.intel.crowdstrike.endpoints.load_host_data(
        neo4j_session,
        host_data,
        TEST_UPDATE_TAG,
    )

    vulnerability_data = tests.data.crowdstrike.spotlight.GET_SPOTLIGHT_VULNERABILITIES
    cartography.intel.crowdstrike.spotlight.load_vulnerability_data(
        neo4j_session,
        vulnerability_data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "00000000000000000000000000000000",
            "00000000000000000000000000000000_00000000000000000000000000000000",
            "CVE-2019-5094",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (h:CrowdstrikeHost)-[:HAS_VULNERABILITY]->(v:SpotlightVulnerability)-[:HAS_CVE]->(c:CVE)
        RETURN h.id, v.id, c.id
        """,
    )
    actual_nodes = {
        (
            n["h.id"],
            n["v.id"],
            n["c.id"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes
