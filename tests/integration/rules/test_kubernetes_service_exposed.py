from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.kubernetes_service_exposed import (
    _kubernetes_service_exposed_direct_load_balancer,
)
from cartography.rules.data.rules.kubernetes_service_exposed import (
    _kubernetes_service_exposed_via_ingress,
)


def _reset_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _seed_cluster(neo4j_session) -> None:
    """Both routes into a cluster, each with a negative counterpart.

    - direct: LoadBalancer service behind two internet-facing ALBs. Two edges on
      purpose: the fact must still report the service once.
    - direct-nlb: LoadBalancer service behind an internet-facing NLB that the AWS
      asset-exposure job never flags, because NLBs bypass security groups.
    - direct-internal: LoadBalancer service behind an internal ALB -> not exposed.
    - ingress-backend: ClusterIP service published by an Ingress on an
      internet-facing ALB.
    - ingress-internal-backend: ClusterIP service published by an Ingress on an
      internal ALB -> not exposed.
    - both: LoadBalancer service exposed directly *and* through an Ingress, so it
      must appear in both facts with its own exposure_type.
    - isolated: ClusterIP service with no entry point at all.
    """
    neo4j_session.run(
        """
        CREATE (cluster:KubernetesCluster {id: 'cluster-1', name: 'my-cluster'})

        CREATE (public_alb:AWSLoadBalancerV2 {id: 'alb-public',
            dnsname: 'public-alb.us-east-1.elb.amazonaws.com',
            scheme: 'internet-facing', type: 'application', exposed_internet: true})
        CREATE (public_alb_2:AWSLoadBalancerV2 {id: 'alb-public-2',
            dnsname: 'public-alb-2.us-east-1.elb.amazonaws.com',
            scheme: 'internet-facing', type: 'application', exposed_internet: true})
        CREATE (public_nlb:AWSLoadBalancerV2 {id: 'nlb-public',
            dnsname: 'public-nlb.us-east-1.elb.amazonaws.com',
            scheme: 'internet-facing', type: 'network'})
        CREATE (internal_alb:AWSLoadBalancerV2 {id: 'alb-internal',
            dnsname: 'internal-alb.us-east-1.elb.amazonaws.com',
            scheme: 'internal', type: 'application', exposed_internet: false})

        CREATE (direct:KubernetesService {id: 'svc-direct', name: 'direct',
            qualified_name: 'default/direct', namespace: 'default',
            type: 'LoadBalancer'})
        CREATE (direct_nlb:KubernetesService {id: 'svc-direct-nlb',
            name: 'direct-nlb', qualified_name: 'default/direct-nlb',
            namespace: 'default', type: 'LoadBalancer'})
        CREATE (direct_internal:KubernetesService {id: 'svc-direct-internal',
            name: 'direct-internal',
            qualified_name: 'default/direct-internal',
            namespace: 'default', type: 'LoadBalancer'})
        CREATE (ingress_backend:KubernetesService {id: 'svc-ingress-backend',
            name: 'ingress-backend', qualified_name: 'apps/ingress-backend',
            namespace: 'apps', type: 'ClusterIP'})
        CREATE (ingress_internal_backend:KubernetesService {
            id: 'svc-ingress-internal-backend',
            name: 'ingress-internal-backend',
            qualified_name: 'apps/ingress-internal-backend',
            namespace: 'apps', type: 'ClusterIP'})
        CREATE (both:KubernetesService {id: 'svc-both', name: 'both',
            qualified_name: 'apps/both', namespace: 'apps',
            type: 'LoadBalancer'})
        CREATE (isolated:KubernetesService {id: 'svc-isolated',
            name: 'isolated', qualified_name: 'default/isolated',
            namespace: 'default', type: 'ClusterIP'})

        CREATE (direct)-[:USES_LOAD_BALANCER]->(public_alb)
        CREATE (direct)-[:USES_LOAD_BALANCER]->(public_alb_2)
        CREATE (direct_nlb)-[:USES_LOAD_BALANCER]->(public_nlb)
        CREATE (direct_internal)-[:USES_LOAD_BALANCER]->(internal_alb)
        CREATE (both)-[:USES_LOAD_BALANCER]->(public_alb)

        CREATE (public_ingress:KubernetesIngress {id: 'ing-public',
            name: 'public', namespace: 'apps'})
        CREATE (internal_ingress:KubernetesIngress {id: 'ing-internal',
            name: 'internal', namespace: 'apps'})
        CREATE (public_ingress)-[:USES_LOAD_BALANCER]->(public_alb)
        CREATE (internal_ingress)-[:USES_LOAD_BALANCER]->(internal_alb)
        CREATE (public_ingress)-[:TARGETS]->(ingress_backend)
        CREATE (public_ingress)-[:TARGETS]->(both)
        CREATE (internal_ingress)-[:TARGETS]->(ingress_internal_backend)

        MERGE (cluster)-[:RESOURCE]->(direct)
        MERGE (cluster)-[:RESOURCE]->(direct_nlb)
        MERGE (cluster)-[:RESOURCE]->(direct_internal)
        MERGE (cluster)-[:RESOURCE]->(ingress_backend)
        MERGE (cluster)-[:RESOURCE]->(ingress_internal_backend)
        MERGE (cluster)-[:RESOURCE]->(both)
        MERGE (cluster)-[:RESOURCE]->(isolated)
        MERGE (cluster)-[:RESOURCE]->(public_ingress)
        MERGE (cluster)-[:RESOURCE]->(internal_ingress)
        """
    )


def test_direct_load_balancer_exposure(neo4j_session) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    _seed_cluster(neo4j_session)

    # Act
    findings = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        _kubernetes_service_exposed_direct_load_balancer.cypher_query,
    )

    # Assert
    # The internal load balancer is excluded; the NLB is included even though the
    # AWS job left exposed_internet unset. `svc-direct` has two internet-facing
    # load balancers but yields one row, not two.
    assert [
        (f["id"], f["name"], f["namespace"], f["service_type"], f["exposure_type"])
        for f in sorted(findings, key=lambda f: f["id"])
    ] == [
        ("svc-both", "apps/both", "apps", "LoadBalancer", "direct_load_balancer"),
        (
            "svc-direct",
            "default/direct",
            "default",
            "LoadBalancer",
            "direct_load_balancer",
        ),
        (
            "svc-direct-nlb",
            "default/direct-nlb",
            "default",
            "LoadBalancer",
            "direct_load_balancer",
        ),
    ]
    assert {f["cluster_name"] for f in findings} == {"my-cluster"}


def test_ingress_exposure(neo4j_session) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    _seed_cluster(neo4j_session)

    # Act
    findings = neo4j_session.execute_read(
        read_list_of_dicts_tx, _kubernetes_service_exposed_via_ingress.cypher_query
    )

    # Assert
    # A ClusterIP backend counts: the controller, not the service, terminates the
    # internet traffic. The backend of the internal-only ingress does not.
    assert [
        (f["id"], f["name"], f["service_type"], f["exposure_type"])
        for f in sorted(findings, key=lambda f: f["id"])
    ] == [
        ("svc-both", "apps/both", "LoadBalancer", "ingress_load_balancer"),
        (
            "svc-ingress-backend",
            "apps/ingress-backend",
            "ClusterIP",
            "ingress_load_balancer",
        ),
    ]


def test_count_queries_cover_the_eligible_population(neo4j_session) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    _seed_cluster(neo4j_session)

    # Act
    direct_count = neo4j_session.run(
        _kubernetes_service_exposed_direct_load_balancer.cypher_count_query
    ).single()["count"]
    ingress_count = neo4j_session.run(
        _kubernetes_service_exposed_via_ingress.cypher_count_query
    ).single()["count"]

    # Assert
    # Every LoadBalancer service could be directly exposed: direct, direct-nlb,
    # direct-internal, both.
    assert direct_count == 4
    # Every ingress-targeted service could be exposed that way: ingress-backend,
    # ingress-internal-backend, both.
    assert ingress_count == 3


def test_visual_queries_run(neo4j_session) -> None:
    """The visual queries must stay executable and agree with the row queries."""
    # Arrange
    _reset_graph(neo4j_session)
    _seed_cluster(neo4j_session)

    for fact in (
        _kubernetes_service_exposed_direct_load_balancer,
        _kubernetes_service_exposed_via_ingress,
    ):
        # Act
        visual_services = {
            record["svc"]["id"]
            for record in neo4j_session.run(fact.cypher_visual_query)
        }
        rows = neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_query)

        # Assert
        assert visual_services == {row["id"] for row in rows}, fact.id
