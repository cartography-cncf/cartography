import cartography.intel.ontology.dnsrecords

TEST_UPDATE_TAG = 123456789
LB_DNS_NAME = "mylb-1234567890.us-east-1.elb.amazonaws.com"


def test_sync_keeps_route53_owned_dns_points_to_relationships(neo4j_session):
    """
    The route53 loader owns (:AWSDNSRecord)-[:DNS_POINTS_TO]->(:AWSLoadBalancerV2) and stamps
    it with the AWS run's update tag. An ontology sync running as a separate cartography run
    has a different update tag, so its cleanup must skip AWSDNSRecord-sourced edges instead of
    deleting and waiting for the next AWS sync to recreate them.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    aws_tag = TEST_UPDATE_TAG - 1

    neo4j_session.run(
        """
        MERGE (lb:AWSLoadBalancerV2 {id: $lb_dns_name})
        SET lb.dnsname = $lb_dns_name,
            lb.lastupdated = $aws_tag

        MERGE (owned:AWSDNSRecord:DNSRecord {id: 'HOSTED_ZONE/elbv2.example.com/ALIAS'})
        SET owned.name = 'elbv2.example.com',
            owned.value = $lb_dns_name,
            // _ont_value is populated on AWSDNSRecord in production, and the ontology match
            // filters on it first. Without it this node would be skipped before the
            // AWSDNSRecord guard is ever reached, and the assertions below would hold even if
            // that guard regressed.
            owned._ont_value = $lb_dns_name,
            owned.lastupdated = $aws_tag

        MERGE (stale:DNSRecord {id: 'generic-record-pointing-elsewhere'})
        SET stale._ont_value = 'gone.example.com',
            stale.lastupdated = $aws_tag

        MERGE (owned)-[owned_rel:DNS_POINTS_TO]->(lb)
        SET owned_rel.lastupdated = $aws_tag

        MERGE (stale)-[stale_rel:DNS_POINTS_TO]->(lb)
        SET stale_rel.lastupdated = $aws_tag
        """,
        lb_dns_name=LB_DNS_NAME,
        aws_tag=aws_tag,
    )

    cartography.intel.ontology.dnsrecords.sync(
        neo4j_session,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    owned = neo4j_session.run(
        """
        MATCH (:AWSDNSRecord)-[r:DNS_POINTS_TO]->(:AWSLoadBalancerV2 {id: $lb_dns_name})
        RETURN count(r) AS count, collect(DISTINCT r.lastupdated) AS lastupdated
        """,
        lb_dns_name=LB_DNS_NAME,
    ).single()
    assert owned["count"] == 1
    # The edge must be left alone entirely, not refreshed with the ontology run's tag: the
    # AWSDNSRecord exclusion is on the MERGE's match, not only on the cleanup's WHERE.
    assert owned["lastupdated"] == [aws_tag]

    # The cleanup must still delete stale edges it does own.
    stale_count = neo4j_session.run(
        """
        MATCH (:DNSRecord {id: 'generic-record-pointing-elsewhere'})
              -[r:DNS_POINTS_TO]->(:AWSLoadBalancerV2 {id: $lb_dns_name})
        RETURN count(r) AS count
        """,
        lb_dns_name=LB_DNS_NAME,
    ).single()["count"]
    assert stale_count == 0
