import cartography.intel.ontology.dnsrecords
from cartography.analysis.ontology.analysis import DNS_RECORD_LINKING_JOBS
from cartography.analysis.ontology.analysis import DNS_RECORD_TARGETS
from cartography.analysis.ontology.analysis import DNS_RECORD_TO_KUBERNETES_INGRESS
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
LB_DNS_NAME = "mylb-1234567890.us-east-1.elb.amazonaws.com"


def test_sync_links_canonical_dns_name_to_kubernetes_ingress(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (:DNSRecord {id: 'dns', _ont_name: 'app.example.com'})
        CREATE (:KubernetesIngress {
            id: 'ingress',
            host_names: [' App.Example.COM. '],
            host_names_normalized: ['app.example.com']
        })
        """
    )

    cartography.intel.ontology.dnsrecords.sync(
        neo4j_session,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    assert check_rels(
        neo4j_session,
        "KubernetesIngress",
        "id",
        "DNSRecord",
        "id",
        "MATCHES_HOSTNAME",
    ) == {("ingress", "dns")}
    # DEPRECATED: the legacy edge is kept for existing queries until v1.0.0.
    assert check_rels(
        neo4j_session,
        "DNSRecord",
        "id",
        "KubernetesIngress",
        "id",
        "DNS_POINTS_TO",
    ) == {("dns", "ingress")}


def test_sync_links_dns_name_to_ingress_created_before_hostname_normalization(
    neo4j_session,
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (:DNSRecord {id: 'dns', _ont_name: 'app.example.com'})
        CREATE (:KubernetesIngress {
            id: 'ingress',
            host_names: [' App.Example.COM. ']
        })
        """
    )

    cartography.intel.ontology.dnsrecords.sync(
        neo4j_session,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    assert check_rels(
        neo4j_session,
        "KubernetesIngress",
        "id",
        "DNSRecord",
        "id",
        "MATCHES_HOSTNAME",
    ) == {("ingress", "dns")}
    # DEPRECATED: the legacy edge is kept for existing queries until v1.0.0.
    assert check_rels(
        neo4j_session,
        "DNSRecord",
        "id",
        "KubernetesIngress",
        "id",
        "DNS_POINTS_TO",
    ) == {("dns", "ingress")}


def test_sync_skips_ingress_without_host_names(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (:DNSRecord {id: 'dns', _ont_name: 'app.example.com'})
        CREATE (:KubernetesIngress {id: 'ingress'})
        """
    )

    cartography.intel.ontology.dnsrecords.sync(
        neo4j_session,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    assert (
        check_rels(
            neo4j_session,
            "DNSRecord",
            "id",
            "KubernetesIngress",
            "id",
            "DNS_POINTS_TO",
        )
        == set()
    )


def test_sync_skips_ingress_host_without_dns_record(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (:DNSRecord {id: 'dns', _ont_name: 'other.example.com'})
        CREATE (:KubernetesIngress {
            id: 'ingress', host_names_normalized: ['app.example.com']
        })
        """
    )

    # Act
    cartography.intel.ontology.dnsrecords.sync(
        neo4j_session,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    assert (
        neo4j_session.run(
            "MATCH (:KubernetesIngress)-[r]-(:DNSRecord) RETURN count(r) AS count"
        ).single()["count"]
        == 0
    )


def test_sync_resolves_shared_hostname_to_record_target_not_ingress_lb(
    neo4j_session,
):
    """
    A record aliases an internet-facing ALB, while an Ingress declaring the same host
    uses a separate internal ALB. The record resolves only to the ALB it targets; the
    Ingress is correlated by hostname and keeps its own load balancer.
    """
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (public_lb:AWSLoadBalancerV2:LoadBalancer {
            id: 'public-alb-1.us-east-1.elb.amazonaws.com',
            dnsname: 'public-alb-1.us-east-1.elb.amazonaws.com',
            scheme: 'internet-facing'
        })
        CREATE (internal_lb:AWSLoadBalancerV2:LoadBalancer {
            id: 'internal-k8s-alb-2.us-east-1.elb.amazonaws.com',
            dnsname: 'internal-k8s-alb-2.us-east-1.elb.amazonaws.com',
            scheme: 'internal'
        })
        CREATE (:CloudflareDNSRecord:DNSRecord {
            id: 'dns',
            _ont_name: 'app.example.com',
            _ont_type: 'CNAME',
            _ont_value: 'public-alb-1.us-east-1.elb.amazonaws.com'
        })
        CREATE (ing:KubernetesIngress {
            id: 'ingress', host_names_normalized: ['app.example.com']
        })
        CREATE (ing)-[:USES_LOAD_BALANCER]->(internal_lb)
        """
    )

    # Act
    cartography.intel.ontology.dnsrecords.sync(
        neo4j_session,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "DNSRecord",
        "id",
        "AWSLoadBalancerV2",
        "id",
        "DNS_POINTS_TO",
    ) == {("dns", "public-alb-1.us-east-1.elb.amazonaws.com")}
    assert check_rels(
        neo4j_session,
        "KubernetesIngress",
        "id",
        "AWSLoadBalancerV2",
        "id",
        "USES_LOAD_BALANCER",
    ) == {("ingress", "internal-k8s-alb-2.us-east-1.elb.amazonaws.com")}
    assert check_rels(
        neo4j_session,
        "KubernetesIngress",
        "id",
        "DNSRecord",
        "id",
        "MATCHES_HOSTNAME",
    ) == {("ingress", "dns")}


def test_sync_removes_stale_ingress_hostname_matches(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (:DNSRecord {id: 'dns', _ont_name: 'app.example.com'})
        CREATE (:KubernetesIngress {
            id: 'ingress', host_names_normalized: ['app.example.com']
        })
        """
    )
    cartography.intel.ontology.dnsrecords.sync(
        neo4j_session,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )
    neo4j_session.run(
        "MATCH (ing:KubernetesIngress {id: 'ingress'}) "
        "SET ing.host_names_normalized = ['moved.example.com']"
    )

    # Act
    cartography.intel.ontology.dnsrecords.sync(
        neo4j_session,
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1},
    )

    # Assert
    assert (
        neo4j_session.run(
            "MATCH (:KubernetesIngress)-[r]-(:DNSRecord) RETURN count(r) AS count"
        ).single()["count"]
        == 0
    )


def test_kubernetes_ingress_match_seeks_dns_record_index(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        UNWIND range(1, 100) AS i
        CREATE (:DNSRecord {id: 'dns-' + i, _ont_name: 'app-' + i + '.example.com'})
        """
    )
    neo4j_session.run(
        """
        CREATE (:KubernetesIngress {
            id: 'ingress', host_names_normalized: ['app-1.example.com']
        })
        """
    )
    _create_dns_record_index_with_fresh_sample(
        neo4j_session, "dns_record_ont_name", "_ont_name"
    )
    match = DNS_RECORD_TO_KUBERNETES_INGRESS.statements[0].match

    plan = neo4j_session.run(f"EXPLAIN {match} RETURN dns, ing").consume().plan

    assert "NodeIndexSeek" in _operator_names(plan)


def _create_dns_record_index_with_fresh_sample(
    neo4j_session, index_name: str, prop: str
) -> None:
    """Ensure the DNSRecord index on `prop` exists and its sample matches the graph.

    Plans depend on index statistics. An earlier test module's load() may already have
    created an equivalent unnamed index, which makes the named CREATE a no-op, and Neo4j
    resamples an index only in the background. A stale sample taken on an empty label
    estimates zero rows for both a seek and a scan, and the planner may then pick either.
    """
    neo4j_session.run(
        f"CREATE INDEX {index_name} IF NOT EXISTS FOR (n:DNSRecord) ON (n.{prop})"
    ).consume()
    neo4j_session.run("CALL db.awaitIndexes()").consume()
    existing_name = neo4j_session.run(
        "SHOW RANGE INDEXES YIELD name, labelsOrTypes, properties "
        "WHERE labelsOrTypes = ['DNSRecord'] AND properties = [$prop] RETURN name",
        prop=prop,
    ).single(strict=True)["name"]
    neo4j_session.run("CALL db.resampleIndex($name)", name=existing_name).consume()


def _operator_names(plan) -> set[str]:
    names = {plan["operatorType"].split("@")[0]}
    for child in plan.get("children", []):
        names |= _operator_names(child)
    return names


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
    service_domain_links = check_rels(
        neo4j_session,
        "DNSRecord",
        "id",
        "RailwayServiceDomain",
        "id",
        "DNS_POINTS_TO",
    )
    assert service_domain_links == {("custom-domain-record", "service-domain")}
    assert ("stale-record", "service-domain") not in service_domain_links

    custom_domain_links = check_rels(
        neo4j_session,
        "DNSRecord",
        "id",
        "RailwayCustomDomain",
        "id",
        "DNS_POINTS_TO",
    )
    assert custom_domain_links == {("custom-domain-record", "custom-domain")}
    assert ("stale-record", "custom-domain") not in custom_domain_links
    assert ("pending-domain-record", "unverified-domain") not in custom_domain_links

    assert check_rels(
        neo4j_session,
        "RailwayServiceDomain",
        "id",
        "RailwayServiceInstance",
        "id",
        "EXPOSE",
    ) == {("service-domain", "service-instance")}
    assert check_rels(
        neo4j_session,
        "RailwayCustomDomain",
        "id",
        "RailwayServiceInstance",
        "id",
        "EXPOSE",
    ) == {("custom-domain", "service-instance")}


SERVICE_ENDPOINT_LABELS = (
    "ModalSandboxTunnel",
    "ModalFunction",
    "GCPCloudRunService",
    "NetlifySite",
    "ScalewayServerlessContainer",
    "ScalewayServerlessFunction",
)


def _dns_points_to(neo4j_session, target_label: str) -> set[tuple]:
    return check_rels(
        neo4j_session,
        "DNSRecord",
        "id",
        target_label,
        "id",
        "DNS_POINTS_TO",
    )


def test_sync_links_dns_records_to_service_endpoints(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (:ModalSandboxTunnel {
            id: 'tunnel',
            host_normalized: 'tls.modal.example.com',
            unencrypted_host_normalized: 'clear.modal.example.com'
        })
        CREATE (:ModalSandboxTunnel {id: 'tunnel-without-hosts'})
        CREATE (:ModalFunction {
            id: 'modal-function', web_hostname: 'function.modal.example.com'
        })
        CREATE (:GCPCloudRunService {
            id: 'cloud-run', uri_hostname: 'service.run.example.com'
        })
        CREATE (:NetlifySite {
            id: 'netlify',
            default_domain_normalized: 'site.netlify.example.com',
            custom_domain_normalized: 'www.example.com',
            domain_aliases_normalized: ['alias.example.com']
        })
        CREATE (stale_site:NetlifySite {
            id: 'stale-site',
            default_domain_normalized: 'other.netlify.example.com'
        })
        CREATE (:ScalewayServerlessContainer {
            id: 'container', domain_name_normalized: 'container.functions.example.com'
        })
        CREATE (:ScalewayServerlessFunction {
            id: 'scw-function', domain_name_normalized: 'function.functions.example.com'
        })
        CREATE (stale_record:DNSRecord {
            id: 'stale-record', _ont_target_hostname: 'gone.example.com'
        })
        CREATE (stale_record)-[:DNS_POINTS_TO {lastupdated: $stale_tag}]->(stale_site)
        CREATE (:GCPRecordSet:DNSRecord {
            id: 'gcp-function',
            _ont_target_hostnames: ['function.modal.example.com']
        })
        CREATE (:GCPRecordSet:DNSRecord {
            id: 'gcp-alias',
            _ont_target_hostnames: ['alias.example.com']
        })
        WITH 1 AS ignored
        UNWIND [
            ['tls', 'tls.modal.example.com'],
            ['clear', 'clear.modal.example.com'],
            ['modal-function', 'function.modal.example.com'],
            ['cloud-run', 'service.run.example.com'],
            ['netlify-default', 'site.netlify.example.com'],
            ['netlify-custom', 'www.example.com'],
            ['netlify-alias', 'alias.example.com'],
            ['scw-container', 'container.functions.example.com'],
            ['scw-function', 'function.functions.example.com']
        ] AS pair
        CREATE (:DNSRecord {id: pair[0], _ont_target_hostname: pair[1]})
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
    assert _dns_points_to(neo4j_session, "ModalSandboxTunnel") == {
        ("tls", "tunnel"),
        ("clear", "tunnel"),
    }
    assert _dns_points_to(neo4j_session, "ModalFunction") == {
        ("modal-function", "modal-function"),
        ("gcp-function", "modal-function"),
    }
    assert _dns_points_to(neo4j_session, "GCPCloudRunService") == {
        ("cloud-run", "cloud-run"),
    }
    assert _dns_points_to(neo4j_session, "NetlifySite") == {
        ("netlify-default", "netlify"),
        ("netlify-custom", "netlify"),
        ("netlify-alias", "netlify"),
        ("gcp-alias", "netlify"),
    }
    assert _dns_points_to(neo4j_session, "ScalewayServerlessContainer") == {
        ("scw-container", "container"),
    }
    assert _dns_points_to(neo4j_session, "ScalewayServerlessFunction") == {
        ("scw-function", "scw-function"),
    }


def test_service_endpoint_matches_seek_dns_record_index(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        UNWIND range(1, 100) AS i
        CREATE (:DNSRecord {
            id: 'dns-' + i, _ont_target_hostname: 'host-' + i + '.example.com'
        })
        """
    )
    neo4j_session.run(
        """
        CREATE (:GCPRecordSet:DNSRecord {
            id: 'gcp', _ont_target_hostnames: ['host-1.example.com']
        })
        """
    )
    for target in DNS_RECORD_TARGETS:
        if target.label not in SERVICE_ENDPOINT_LABELS:
            continue
        hostnames = {prop: f"{prop}.example.com" for prop in target.properties}
        hostnames |= {prop: [f"{prop}.example.com"] for prop in target.list_properties}
        neo4j_session.run(
            f"CREATE (target:{target.label} {{id: $id}}) SET target += $hostnames",
            id=target.label,
            hostnames=hostnames,
        )
    _create_dns_record_index_with_fresh_sample(
        neo4j_session, "dns_record_ont_target_hostname", "_ont_target_hostname"
    )
    matches = [
        statement.match
        for job in DNS_RECORD_LINKING_JOBS
        for statement in job.statements
        if any(
            effect.target_label in SERVICE_ENDPOINT_LABELS
            for effect in statement.effects
        )
        and "(dns:DNSRecord {_ont_target_hostname:" in statement.match
    ]

    # Act
    plans = {
        match: neo4j_session.run(f"EXPLAIN {match} RETURN dns, target").consume().plan
        for match in matches
    }

    # Assert
    # One match per scalar hostname property, plus one for Netlify aliases.
    assert len(plans) == 9
    for match, plan in plans.items():
        assert "NodeIndexSeek" in _operator_names(plan), match
