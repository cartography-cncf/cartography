"""
Tests for the Scaleway internet exposure analysis jobs.

These build up the prerequisite graph state and then run the analysis jobs against it,
asserting the resulting exposed_internet / exposed_internet_type properties.
"""

import cartography.util
from cartography.analysis.scaleway.analysis import SCALEWAY_EXPOSURE_JOBS
from tests.integration.util import check_nodes

TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMETERS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "ORG_ID": "0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
}


def _create_base_graph(neo4j_session):
    """
    Build one instance per exposure scenario, all inside a single project.

    inst-direct    public IP + inbound accept 0.0.0.0/0     -> direct
    inst-outbound  public IP, but only an OUTBOUND accept   -> not exposed
    inst-drop      public IP, but the inbound rule DROPs    -> not exposed
    inst-scoped    public IP, inbound accept from one CIDR  -> not exposed
    inst-nopubip   open inbound rule but no public IP       -> not exposed
    inst-stopped   public IP + open inbound rule, stopped   -> not exposed
    inst-pat       no public IP, reached by a gateway PAT   -> pat
    """
    neo4j_session.run(
        "MERGE (p:ScalewayProject{id: $pid}) SET p.lastupdated = $tag",
        pid=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )

    # (instance id, public_ips, state, private_ip)
    instances = [
        ("inst-direct", ["fip-1"], "running", None),
        ("inst-outbound", ["fip-2"], "running", None),
        ("inst-drop", ["fip-3"], "running", None),
        ("inst-scoped", ["fip-4"], "running", None),
        ("inst-nopubip", [], "running", None),
        ("inst-stopped", ["fip-5"], "stopped", None),
        ("inst-pat", [], "running", "192.168.1.10"),
    ]
    for instance_id, public_ips, state, private_ip in instances:
        neo4j_session.run(
            """
            MATCH (p:ScalewayProject{id: $pid})
            MERGE (i:ScalewayInstance{id: $iid})
            SET i.public_ips = $public_ips,
                i.state = $state,
                i.private_ip = $private_ip,
                i.lastupdated = $tag
            MERGE (p)-[r:RESOURCE]->(i)
            SET r.lastupdated = $tag
            """,
            pid=TEST_PROJECT_ID,
            iid=instance_id,
            public_ips=public_ips,
            state=state,
            private_ip=private_ip,
            tag=TEST_UPDATE_TAG,
        )

    # (security group id, member instance id, rule direction, action, ip_range)
    groups = [
        ("sg-direct", "inst-direct", "inbound", "accept", "0.0.0.0/0"),
        ("sg-outbound", "inst-outbound", "outbound", "accept", "0.0.0.0/0"),
        ("sg-drop", "inst-drop", "inbound", "drop", "0.0.0.0/0"),
        ("sg-scoped", "inst-scoped", "inbound", "accept", "10.0.0.0/8"),
        ("sg-nopubip", "inst-nopubip", "inbound", "accept", "0.0.0.0/0"),
        ("sg-stopped", "inst-stopped", "inbound", "accept", "0.0.0.0/0"),
    ]
    for sg_id, instance_id, direction, action, ip_range in groups:
        neo4j_session.run(
            """
            MATCH (i:ScalewayInstance{id: $iid})
            MERGE (sg:ScalewaySecurityGroup{id: $sgid})
            SET sg.lastupdated = $tag
            MERGE (i)-[m:MEMBER_OF_SCALEWAY_SECURITY_GROUP]->(sg)
            SET m.lastupdated = $tag
            MERGE (rule:ScalewaySecurityGroupRule{id: $rid})
            SET rule.direction = $direction,
                rule.action = $action,
                rule.ip_range = $ip_range,
                rule.protocol = 'tcp',
                rule.dest_port_from = 22,
                rule.dest_port_to = 22,
                rule.lastupdated = $tag
            MERGE (rule)-[rm:MEMBER_OF_SCALEWAY_SECURITY_GROUP]->(sg)
            SET rm.lastupdated = $tag
            """,
            iid=instance_id,
            sgid=sg_id,
            rid=f"rule-{sg_id}",
            direction=direction,
            action=action,
            ip_range=ip_range,
            tag=TEST_UPDATE_TAG,
        )

    # Public gateway PAT rule forwarding to inst-pat's private IP.
    neo4j_session.run(
        """
        MATCH (p:ScalewayProject{id: $pid})
        MERGE (gw:ScalewayPublicGateway{id: 'gw-1'})
        SET gw.lastupdated = $tag
        MERGE (p)-[r:RESOURCE]->(gw)
        SET r.lastupdated = $tag
        MERGE (pat:ScalewayPublicGatewayPatRule{id: 'pat-1'})
        SET pat.private_ip = '192.168.1.10',
            pat.private_port = 22,
            pat.public_port = 2222,
            pat.protocol = 'tcp',
            pat.lastupdated = $tag
        MERGE (gw)-[h:HAS]->(pat)
        SET h.lastupdated = $tag
        """,
        pid=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )


def _run_exposure_jobs(neo4j_session):
    for job in SCALEWAY_EXPOSURE_JOBS:
        cartography.util.run_typed_analysis_job(
            job, neo4j_session, COMMON_JOB_PARAMETERS
        )


def test_scaleway_instance_exposure(neo4j_session):
    # Arrange
    _create_base_graph(neo4j_session)

    # Act
    _run_exposure_jobs(neo4j_session)

    # Assert: only the directly-open instance and the PAT-reachable one are exposed,
    # and every other instance carries an explicit false rather than a null.
    # exposed_internet_type is asserted separately because check_nodes cannot hash a
    # list-valued property.
    assert check_nodes(
        neo4j_session,
        "ScalewayInstance",
        ["id", "exposed_internet"],
    ) == {
        ("inst-direct", True),
        ("inst-pat", True),
        ("inst-outbound", False),
        ("inst-drop", False),
        ("inst-scoped", False),
        ("inst-nopubip", False),
        ("inst-stopped", False),
    }
    types = {
        row["id"]: row["types"]
        for row in neo4j_session.run(
            """
            MATCH (i:ScalewayInstance)
            RETURN i.id AS id, i.exposed_internet_type AS types
            """,
        )
    }
    assert types == {
        "inst-direct": ["direct"],
        "inst-pat": ["pat"],
        "inst-outbound": None,
        "inst-drop": None,
        "inst-scoped": None,
        "inst-nopubip": None,
        "inst-stopped": None,
    }


def test_scaleway_instance_exposure_accumulates_types(neo4j_session):
    """An instance open directly AND reachable through a PAT rule records both paths."""
    # Arrange
    _create_base_graph(neo4j_session)
    # Give inst-direct a private IP matching the PAT rule so both statements hit it.
    neo4j_session.run(
        "MATCH (i:ScalewayInstance{id: 'inst-direct'}) SET i.private_ip = '192.168.1.10'",
    )

    # Act
    _run_exposure_jobs(neo4j_session)

    # Assert
    result = neo4j_session.run(
        "MATCH (i:ScalewayInstance{id: 'inst-direct'}) RETURN i.exposed_internet_type AS types",
    ).single()
    assert sorted(result["types"]) == ["direct", "pat"]


def test_scaleway_instance_exposure_cleanup_clears_stale_verdict(neo4j_session):
    """Closing the security group must clear the property, not leave it stuck at true."""
    # Arrange
    _create_base_graph(neo4j_session)
    _run_exposure_jobs(neo4j_session)

    # Act: the instance loses its public IP, so it is no longer directly reachable.
    neo4j_session.run(
        "MATCH (i:ScalewayInstance{id: 'inst-direct'}) SET i.public_ips = []",
    )
    _run_exposure_jobs(neo4j_session)

    # Assert
    result = neo4j_session.run(
        """
        MATCH (i:ScalewayInstance{id: 'inst-direct'})
        RETURN i.exposed_internet AS exposed, i.exposed_internet_type AS types
        """,
    ).single()
    assert result["exposed"] is False
    assert result["types"] is None
