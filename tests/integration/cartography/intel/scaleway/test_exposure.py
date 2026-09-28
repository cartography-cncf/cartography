"""Tests for the Scaleway internet exposure analysis jobs."""

import cartography.util
from cartography.analysis.ontology.analysis import WORKLOAD_HAS_RUNTIME_IMAGE
from cartography.analysis.scaleway.analysis import SCALEWAY_EXPOSURE_JOBS
from tests.integration.util import check_rels

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
    inst-default   public IP, SG default-accepts, NO rule   -> direct
    inst-default-nopubip  same group but no public IP       -> not exposed
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
        ("inst-default", ["fip-6"], "running", None),
        ("inst-default-nopubip", [], "running", None),
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
            SET sg.inbound_default_policy = 'drop', sg.lastupdated = $tag
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

    # A group whose inbound default policy accepts, carrying no rule whatsoever: the only
    # thing that can mark its members exposed is the default policy itself.
    for instance_id in ("inst-default", "inst-default-nopubip"):
        neo4j_session.run(
            """
            MATCH (i:ScalewayInstance{id: $iid})
            MERGE (sg:ScalewaySecurityGroup{id: 'sg-default-accept'})
            SET sg.inbound_default_policy = 'accept', sg.lastupdated = $tag
            MERGE (i)-[m:MEMBER_OF_SCALEWAY_SECURITY_GROUP]->(sg)
            SET m.lastupdated = $tag
            """,
            iid=instance_id,
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


def _create_loadbalancer_graph(neo4j_session):
    """
    Build three load balancers, all in the same project as the instances above.

    lb-public   public IP + a frontend routing to a backend whose pool holds
                inst-lb-private's private IP and inst-lb-public's flexible IP -> exposed
    lb-private  no public IP (private-network only)                           -> not exposed
    lb-nofront  public IP but no frontend listening                           -> not exposed

    inst-orphan sits in a backend pool that no frontend routes to, so it must stay
    unexposed even though its IP is in a pool.
    """
    for instance_id, private_ip in [
        ("inst-lb-private", "172.16.0.10"),
        ("inst-lb-public", None),
        ("inst-orphan", "172.16.0.99"),
        ("inst-lb-stopped", "172.16.0.10"),
    ]:
        neo4j_session.run(
            """
            MATCH (p:ScalewayProject{id: $pid})
            MERGE (i:ScalewayInstance{id: $iid})
            SET i.public_ips = [],
                i.state = (CASE WHEN $iid ENDS WITH '-stopped' THEN 'stopped' ELSE 'running' END),
                i.private_ip = $private_ip,
                i.lastupdated = $tag
            MERGE (p)-[r:RESOURCE]->(i)
            SET r.lastupdated = $tag
            """,
            pid=TEST_PROJECT_ID,
            iid=instance_id,
            private_ip=private_ip,
            tag=TEST_UPDATE_TAG,
        )

    # inst-lb-public is reached through its flexible IP rather than a private IP.
    neo4j_session.run(
        """
        MATCH (i:ScalewayInstance{id: 'inst-lb-public'})
        MERGE (fip:ScalewayFlexibleIp{id: 'fip-lb'})
        SET fip.address = '51.159.9.9', fip.lastupdated = $tag
        MERGE (fip)-[r:IDENTIFIES]->(i)
        SET r.lastupdated = $tag
        """,
        tag=TEST_UPDATE_TAG,
    )

    # exposed_internet is set by transform_loadbalancers, so it is seeded here the way the
    # loader would write it rather than derived by a job.
    # (lb id, public ip, has frontend, exposed_internet)
    for lb_id, ip_address, has_frontend, exposed in [
        ("lb-public", "51.159.0.1", True, True),
        ("lb-private", None, True, False),
        ("lb-nofront", "51.159.0.2", False, False),
    ]:
        neo4j_session.run(
            """
            MATCH (p:ScalewayProject{id: $pid})
            MERGE (lb:ScalewayLoadBalancer{id: $lbid})
            SET lb.ip_address = $ip_address,
                lb.exposed_internet = $exposed,
                lb.lastupdated = $tag
            MERGE (p)-[r:RESOURCE]->(lb)
            SET r.lastupdated = $tag
            """,
            pid=TEST_PROJECT_ID,
            lbid=lb_id,
            ip_address=ip_address,
            exposed=exposed,
            tag=TEST_UPDATE_TAG,
        )
        if not has_frontend:
            continue
        neo4j_session.run(
            """
            MATCH (p:ScalewayProject{id: $pid})
            MATCH (lb:ScalewayLoadBalancer{id: $lbid})
            MERGE (f:ScalewayLBFrontend{id: $fid})
            SET f.inbound_port = 80, f.lastupdated = $tag
            MERGE (lb)-[h:HAS]->(f)
            SET h.lastupdated = $tag
            MERGE (b:ScalewayLBBackend{id: $bid})
            SET b.pool = ['172.16.0.10', '51.159.9.9'], b.lastupdated = $tag
            MERGE (lb)-[hb:HAS]->(b)
            SET hb.lastupdated = $tag
            MERGE (f)-[rt:ROUTES_TO]->(b)
            SET rt.lastupdated = $tag
            MERGE (p)-[rf:RESOURCE]->(f)
            SET rf.lastupdated = $tag
            MERGE (p)-[rb:RESOURCE]->(b)
            SET rb.lastupdated = $tag
            """,
            pid=TEST_PROJECT_ID,
            lbid=lb_id,
            fid=f"front-{lb_id}",
            bid=f"back-{lb_id}",
            tag=TEST_UPDATE_TAG,
        )

    # An orphan backend on lb-public that no frontend routes to.
    neo4j_session.run(
        """
        MATCH (p:ScalewayProject{id: $pid})
        MATCH (lb:ScalewayLoadBalancer{id: 'lb-public'})
        MERGE (b:ScalewayLBBackend{id: 'back-orphan'})
        SET b.pool = ['172.16.0.99'], b.lastupdated = $tag
        MERGE (lb)-[h:HAS]->(b)
        SET h.lastupdated = $tag
        MERGE (p)-[r:RESOURCE]->(b)
        SET r.lastupdated = $tag
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

    # Restricted to this scenario's own instances: the neo4j_session fixture is
    # module-scoped, so other tests in this file add instances of their own.
    verdicts = {
        row["id"]: (row["exposed"], row["types"])
        for row in neo4j_session.run(
            """
            MATCH (i:ScalewayInstance)
            WHERE i.id STARTS WITH 'inst-' AND NOT i.id STARTS WITH 'inst-lb'
              AND i.id <> 'inst-orphan'
            RETURN i.id AS id,
                   i.exposed_internet AS exposed,
                   i.exposed_internet_type AS types
            """,
        )
    }
    assert verdicts == {
        "inst-direct": (True, ["direct"]),
        "inst-pat": (True, ["pat"]),
        # A default-accept group needs no explicit rule to let traffic through.
        "inst-default": (True, ["direct"]),
        "inst-default-nopubip": (False, None),
        "inst-outbound": (False, None),
        "inst-drop": (False, None),
        "inst-scoped": (False, None),
        "inst-nopubip": (False, None),
        "inst-stopped": (False, None),
    }


def test_scaleway_lb_expose_edges_and_instance_propagation(neo4j_session):
    # Arrange
    _create_base_graph(neo4j_session)
    _create_loadbalancer_graph(neo4j_session)

    # Act
    _run_exposure_jobs(neo4j_session)

    # Resolved through both a private IP and a flexible IP; the orphan backend yields none.
    assert check_rels(
        neo4j_session,
        "ScalewayLoadBalancer",
        "id",
        "ScalewayInstance",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {
        ("lb-public", "inst-lb-private"),
        ("lb-public", "inst-lb-public"),
    }

    # And the exposure verdict propagates onto those instances with the `lb` path.
    types = {
        row["id"]: row["types"]
        for row in neo4j_session.run(
            """
            MATCH (i:ScalewayInstance)
            WHERE i.id IN ['inst-lb-private', 'inst-lb-public', 'inst-orphan']
            RETURN i.id AS id, i.exposed_internet_type AS types
            """,
        )
    }
    assert types == {
        "inst-lb-private": ["lb"],
        "inst-lb-public": ["lb"],
        "inst-orphan": None,
    }


def test_scaleway_stopped_instance_behind_a_load_balancer_is_not_exposed(neo4j_session):
    """A stopped instance is not a live attack surface, whichever path reaches it.

    inst-lb-stopped shares inst-lb-private's IP and so sits in the same backend pool; only
    its state differs.
    """
    # Arrange
    _create_base_graph(neo4j_session)
    _create_loadbalancer_graph(neo4j_session)

    # Act
    _run_exposure_jobs(neo4j_session)

    # Assert: no verdict and no EXPOSE edge, unlike its running twin.
    result = neo4j_session.run(
        """
        MATCH (i:ScalewayInstance{id: 'inst-lb-stopped'})
        RETURN i.exposed_internet AS exposed,
               i.exposed_internet_type AS types,
               exists((:ScalewayLoadBalancer)-[:EXPOSE]->(i)) AS has_edge
        """,
    ).single()
    assert result["exposed"] is False
    assert result["types"] is None
    assert result["has_edge"] is False


def test_scaleway_container_exposure_reaches_has_runtime_image(neo4j_session):
    """A Scaleway container's exposed_internet reaches HAS_RUNTIME_IMAGE.

    The container verdict itself is set by transform (asserted in test_serverless.py); this
    covers the hand-off to the ontology roll-up, which saw nothing for Scaleway before.
    """
    # ScalewayServerlessContainer carries both ComputeService and Container, so the ontology
    # job's *0..6 lower bound of 0 matches it with no WORKLOAD_PARENT hop.
    _create_base_graph(neo4j_session)
    for suffix, privacy in [("public", "public"), ("private", "private")]:
        neo4j_session.run(
            """
            MATCH (p:ScalewayProject{id: $pid})
            MERGE (c:ScalewayServerlessContainer:ComputeService:Container{id: $cid})
            SET c.privacy = $privacy,
                c.exposed_internet = ($privacy = 'public'),
                c._ont_state = 'ready',
                c.lastupdated = $tag
            MERGE (p)-[r:RESOURCE]->(c)
            SET r.lastupdated = $tag
            MERGE (img:Image:ScalewayContainerRegistryImage{id: $imgid})
            SET img.lastupdated = $tag
            MERGE (c)-[ri:RESOLVED_IMAGE]->(img)
            SET ri.lastupdated = $tag
            """,
            pid=TEST_PROJECT_ID,
            cid=f"e2e-container-{suffix}",
            imgid=f"sha256:e2e-{suffix}",
            privacy=privacy,
            tag=TEST_UPDATE_TAG,
        )

    # Act
    _run_exposure_jobs(neo4j_session)
    cartography.util.run_typed_analysis_job(
        WORKLOAD_HAS_RUNTIME_IMAGE, neo4j_session, COMMON_JOB_PARAMETERS
    )

    # Assert
    edges = {
        (row["cid"], row["exposed"])
        for row in neo4j_session.run(
            """
            MATCH (c:ScalewayServerlessContainer)-[r:HAS_RUNTIME_IMAGE]->(:Image)
            WHERE c.id STARTS WITH 'e2e-container-'
            RETURN c.id AS cid, r.exposed_internet AS exposed
            """,
        )
    }
    assert edges == {
        ("e2e-container-public", True),
        ("e2e-container-private", False),
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
