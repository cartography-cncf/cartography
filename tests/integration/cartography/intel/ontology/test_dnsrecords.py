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


def test_sync_links_dns_records_to_railway_domains(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (service_domain:RailwayServiceDomain {
            id: 'service-domain',
            domain_normalized: 'web-production.up.railway.app'
        })
        CREATE (custom_domain:RailwayCustomDomain {
            id: 'custom-domain',
            domain_normalized: 'app.example.com',
            verified: true
        })
        CREATE (unverified_domain:RailwayCustomDomain {
            id: 'unverified-domain',
            domain_normalized: 'pending.example.com',
            verified: false
        })
        CREATE (instance:RailwayServiceInstance {id: 'service-instance'})
        CREATE (service_domain)-[:EXPOSE]->(instance)
        CREATE (custom_domain)-[:EXPOSE]->(instance)
        CREATE (:CloudflareDNSRecord:DNSRecord {
            id: 'custom-domain-record',
            _ont_name: 'app.example.com',
            _ont_type: 'CNAME',
            _ont_target_hostname: 'web-production.up.railway.app'
        })
        CREATE (:CloudflareDNSRecord:DNSRecord {
            id: 'pending-domain-record',
            _ont_name: 'pending.example.com',
            _ont_type: 'CNAME',
            _ont_target_hostname: 'pending.up.railway.app'
        })
        CREATE (:CloudflareDNSRecord:DNSRecord {
            id: 'unrelated-text-record',
            _ont_name: 'app.example.com',
            _ont_type: 'TXT',
            _ont_value: 'verification-token'
        })
        CREATE (stale:CloudflareDNSRecord:DNSRecord {
            id: 'stale-record',
            _ont_name: 'old.example.com',
            _ont_target_hostname: 'old.up.railway.app'
        })
        CREATE (stale)-[:DNS_POINTS_TO {lastupdated: $stale_tag}]->(service_domain)
        CREATE (stale)-[:DNS_POINTS_TO {lastupdated: $stale_tag}]->(custom_domain)
        """,
        stale_tag=TEST_UPDATE_TAG - 1,
    )

    # Act
    cartography.intel.ontology.dnsrecords.sync(
        neo4j_session,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    paths = {
        (record_id, domain_label, instance_id)
        for record_id, domain_label, instance_id in neo4j_session.run(
            """
            MATCH (dns:DNSRecord)-[:DNS_POINTS_TO]->(domain)-[:EXPOSE]->(instance)
            WHERE domain:RailwayServiceDomain
               OR domain:RailwayCustomDomain
            RETURN dns.id AS record_id, labels(domain)[0] AS domain_label,
                   instance.id AS instance_id
            """
        ).values()
    }
    assert paths == {
        ("custom-domain-record", "RailwayServiceDomain", "service-instance"),
        ("custom-domain-record", "RailwayCustomDomain", "service-instance"),
    }

    stale_relationship_count = neo4j_session.run(
        """
        MATCH (:DNSRecord {id: 'stale-record'})-[r:DNS_POINTS_TO]->(domain)
        WHERE domain:RailwayServiceDomain
           OR domain:RailwayCustomDomain
        RETURN count(r) AS count
        """
    ).single()["count"]
    assert stale_relationship_count == 0

    unverified_relationship_count = neo4j_session.run(
        """
        MATCH (:DNSRecord {id: 'pending-domain-record'})
              -[r:DNS_POINTS_TO]->(:RailwayCustomDomain {id: 'unverified-domain'})
        RETURN count(r) AS count
        """
    ).single()["count"]
    assert unverified_relationship_count == 0


def test_sync_links_dns_records_to_public_service_endpoints(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (:ModalSandboxTunnel {
            id: 'tunnel', host_normalized: 'tls.modal.test',
            unencrypted_host_normalized: 'clear.modal.test'
        })
        CREATE (:ModalFunction {
            id: 'modal-function', web_hostname: 'function.modal.test'
        })
        CREATE (:GCPCloudRunService {
            id: 'cloud-run', uri_hostname: 'service.run.test'
        })
        CREATE (:NetlifySite {
            id: 'netlify', default_domain_normalized: 'site.netlify.test',
            custom_domain_normalized: 'www.example.test',
            domain_aliases_normalized: ['alias.example.test']
        })
        CREATE (:ScalewayServerlessContainer {
            id: 'container', domain_name_normalized: 'container.functions.test'
        })
        CREATE (:ScalewayServerlessFunction {
            id: 'scw-function', domain_name_normalized: 'function.functions.test'
        })
        CREATE (:ModalSandboxTunnel {id: 'null-tunnel'})
        CREATE (:AWSEC2Instance {id: 'private-instance', publicdnsname: ''})
        CREATE (stale_record:DNSRecord {
            id: 'stale-service-record', _ont_target_hostname: 'gone.example.test'
        })
        CREATE (stale_target:NetlifySite {
            id: 'stale-site', default_domain_normalized: 'different.example.test'
        })
        CREATE (stale_record)-[:DNS_POINTS_TO {lastupdated: $stale_tag}]->(stale_target)
        CREATE (:DNSRecord {id: 'empty-record', _ont_target_hostname: ''})
        CREATE (:GCPRecordSet:DNSRecord {
            id: 'gcp-modal-function',
            _ont_target_hostnames: ['function.modal.test']
        })
        WITH 1 AS ignored
        UNWIND [
            ['tls', 'tls.modal.test'],
            ['clear', 'clear.modal.test'],
            ['modal-function', 'function.modal.test'],
            ['cloud-run', 'service.run.test'],
            ['netlify-default', 'site.netlify.test'],
            ['netlify-custom', 'www.example.test'],
            ['netlify-alias', 'alias.example.test'],
            ['scw-container', 'container.functions.test'],
            ['scw-function', 'function.functions.test']
        ] AS pair
        CREATE (:DNSRecord {id: pair[0], _ont_target_hostname: pair[1]})
        """,
        stale_tag=TEST_UPDATE_TAG - 1,
    )

    cartography.intel.ontology.dnsrecords.sync(
        neo4j_session,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    paths = {
        (record_id, target_label, target_id)
        for record_id, target_label, target_id in neo4j_session.run(
            """
            MATCH (dns:DNSRecord)-[:DNS_POINTS_TO]->(target)
            WHERE target:ModalSandboxTunnel
               OR target:ModalFunction
               OR target:GCPCloudRunService
               OR target:NetlifySite
               OR target:ScalewayServerlessContainer
               OR target:ScalewayServerlessFunction
            RETURN dns.id, labels(target)[0], target.id
            """
        ).values()
    }
    assert paths == {
        ("tls", "ModalSandboxTunnel", "tunnel"),
        ("clear", "ModalSandboxTunnel", "tunnel"),
        ("modal-function", "ModalFunction", "modal-function"),
        ("gcp-modal-function", "ModalFunction", "modal-function"),
        ("cloud-run", "GCPCloudRunService", "cloud-run"),
        ("netlify-default", "NetlifySite", "netlify"),
        ("netlify-custom", "NetlifySite", "netlify"),
        ("netlify-alias", "NetlifySite", "netlify"),
        ("scw-container", "ScalewayServerlessContainer", "container"),
        ("scw-function", "ScalewayServerlessFunction", "scw-function"),
    }

    assert (
        neo4j_session.run(
            """
            MATCH (:DNSRecord {id: 'stale-service-record'})
                  -[r:DNS_POINTS_TO]->(:NetlifySite {id: 'stale-site'})
            RETURN count(r) AS count
            """
        ).single()["count"]
        == 0
    )
    assert (
        neo4j_session.run(
            """
            MATCH (:DNSRecord {id: 'empty-record'})-[r:DNS_POINTS_TO]->()
            RETURN count(r) AS count
            """
        ).single()["count"]
        == 0
    )
