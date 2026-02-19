from cartography.util import run_scoped_analysis_job
from tests.integration.util import check_rels

TEST_CLUSTER_ID = "arn:aws:eks:us-east-1:000000000000:cluster/test-cluster"
TEST_UPDATE_TAG = 123456789


def _create_prereq_nodes(neo4j_session):
    """
    Create the full graph needed for both exposure paths:

    Path 1 (Service type=LoadBalancer):
      KubernetesCluster -[:RESOURCE]-> KubernetesService -[:USES_LOAD_BALANCER]-> AWSLoadBalancerV2(exposed_internet=true)
      KubernetesService -[:TARGETS]-> KubernetesPod -[:CONTAINS]-> KubernetesContainer

    Path 2 (Ingress):
      KubernetesCluster -[:RESOURCE]-> KubernetesIngress -[:USES_LOAD_BALANCER]-> AWSLoadBalancerV2(exposed_internet=true)
      KubernetesIngress -[:TARGETS]-> KubernetesService -[:TARGETS]-> KubernetesPod -[:CONTAINS]-> KubernetesContainer
    """
    # Cluster
    neo4j_session.run(
        "MERGE (c:KubernetesCluster{id: $id}) SET c.lastupdated = $tag",
        id=TEST_CLUSTER_ID,
        tag=TEST_UPDATE_TAG,
    )

    # --- Path 1: Service type=LoadBalancer -> NLB ---

    # Internet-facing NLB
    neo4j_session.run(
        "MERGE (lb:AWSLoadBalancerV2{id: 'nlb-dns.elb.amazonaws.com', dnsname: 'nlb-dns.elb.amazonaws.com'}) "
        "SET lb.lastupdated = $tag, lb.scheme = 'internet-facing', lb.exposed_internet = true",
        tag=TEST_UPDATE_TAG,
    )

    # LoadBalancer-type Service
    neo4j_session.run(
        "MERGE (svc:KubernetesService{id: 'svc-lb-uid', name: 'my-lb-svc', namespace: 'default'}) "
        "SET svc.lastupdated = $tag, svc.type = 'LoadBalancer'",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MATCH (c:KubernetesCluster{id: $cid}), (svc:KubernetesService{id: 'svc-lb-uid'}) "
        "MERGE (c)-[:RESOURCE]->(svc)",
        cid=TEST_CLUSTER_ID,
    )
    neo4j_session.run(
        "MATCH (svc:KubernetesService{id: 'svc-lb-uid'}), (lb:AWSLoadBalancerV2{id: 'nlb-dns.elb.amazonaws.com'}) "
        "MERGE (svc)-[:USES_LOAD_BALANCER]->(lb)",
    )

    # Pod targeted by LB service
    neo4j_session.run(
        "MERGE (pod:KubernetesPod{id: 'pod-lb-uid', namespace: 'default'}) "
        "SET pod.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MATCH (c:KubernetesCluster{id: $cid}), (pod:KubernetesPod{id: 'pod-lb-uid'}) "
        "MERGE (c)-[:RESOURCE]->(pod)",
        cid=TEST_CLUSTER_ID,
    )
    neo4j_session.run(
        "MATCH (svc:KubernetesService{id: 'svc-lb-uid'}), (pod:KubernetesPod{id: 'pod-lb-uid'}) "
        "MERGE (svc)-[:TARGETS]->(pod)",
    )

    # Container in LB pod
    neo4j_session.run(
        "MERGE (cont:KubernetesContainer{id: 'cont-lb-uid', name: 'web'}) "
        "SET cont.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MATCH (c:KubernetesCluster{id: $cid}), (cont:KubernetesContainer{id: 'cont-lb-uid'}) "
        "MERGE (c)-[:RESOURCE]->(cont)",
        cid=TEST_CLUSTER_ID,
    )
    neo4j_session.run(
        "MATCH (pod:KubernetesPod{id: 'pod-lb-uid'}), (cont:KubernetesContainer{id: 'cont-lb-uid'}) "
        "MERGE (pod)-[:CONTAINS]->(cont)",
    )

    # --- Path 2: Ingress -> ALB ---

    # Internet-facing ALB
    neo4j_session.run(
        "MERGE (lb:AWSLoadBalancerV2{id: 'alb-dns.elb.amazonaws.com', dnsname: 'alb-dns.elb.amazonaws.com'}) "
        "SET lb.lastupdated = $tag, lb.scheme = 'internet-facing', lb.exposed_internet = true",
        tag=TEST_UPDATE_TAG,
    )

    # Ingress
    neo4j_session.run(
        "MERGE (ing:KubernetesIngress{id: 'ing-uid', name: 'my-ingress', namespace: 'default'}) "
        "SET ing.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MATCH (c:KubernetesCluster{id: $cid}), (ing:KubernetesIngress{id: 'ing-uid'}) "
        "MERGE (c)-[:RESOURCE]->(ing)",
        cid=TEST_CLUSTER_ID,
    )
    neo4j_session.run(
        "MATCH (ing:KubernetesIngress{id: 'ing-uid'}), (lb:AWSLoadBalancerV2{id: 'alb-dns.elb.amazonaws.com'}) "
        "MERGE (ing)-[:USES_LOAD_BALANCER]->(lb)",
    )

    # ClusterIP Service behind Ingress
    neo4j_session.run(
        "MERGE (svc:KubernetesService{id: 'svc-clusterip-uid', name: 'my-clusterip-svc', namespace: 'default'}) "
        "SET svc.lastupdated = $tag, svc.type = 'ClusterIP'",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MATCH (c:KubernetesCluster{id: $cid}), (svc:KubernetesService{id: 'svc-clusterip-uid'}) "
        "MERGE (c)-[:RESOURCE]->(svc)",
        cid=TEST_CLUSTER_ID,
    )
    neo4j_session.run(
        "MATCH (ing:KubernetesIngress{id: 'ing-uid'}), (svc:KubernetesService{id: 'svc-clusterip-uid'}) "
        "MERGE (ing)-[:TARGETS]->(svc)",
    )

    # Pod targeted by ClusterIP service
    neo4j_session.run(
        "MERGE (pod:KubernetesPod{id: 'pod-ing-uid', namespace: 'default'}) "
        "SET pod.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MATCH (c:KubernetesCluster{id: $cid}), (pod:KubernetesPod{id: 'pod-ing-uid'}) "
        "MERGE (c)-[:RESOURCE]->(pod)",
        cid=TEST_CLUSTER_ID,
    )
    neo4j_session.run(
        "MATCH (svc:KubernetesService{id: 'svc-clusterip-uid'}), (pod:KubernetesPod{id: 'pod-ing-uid'}) "
        "MERGE (svc)-[:TARGETS]->(pod)",
    )

    # Container in Ingress pod
    neo4j_session.run(
        "MERGE (cont:KubernetesContainer{id: 'cont-ing-uid', name: 'api'}) "
        "SET cont.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MATCH (c:KubernetesCluster{id: $cid}), (cont:KubernetesContainer{id: 'cont-ing-uid'}) "
        "MERGE (c)-[:RESOURCE]->(cont)",
        cid=TEST_CLUSTER_ID,
    )
    neo4j_session.run(
        "MATCH (pod:KubernetesPod{id: 'pod-ing-uid'}), (cont:KubernetesContainer{id: 'cont-ing-uid'}) "
        "MERGE (pod)-[:CONTAINS]->(cont)",
    )


def test_k8s_lb_expose_via_service(neo4j_session):
    """
    Test that the k8s_lb_exposure analysis job creates EXPOSE rels
    from an internet-facing NLB to Pods and Containers via Service type=LoadBalancer.
    """
    # Arrange
    _create_prereq_nodes(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Act
    run_scoped_analysis_job(
        "k8s_compute_asset_exposure.json", neo4j_session, common_job_parameters
    )
    run_scoped_analysis_job(
        "k8s_lb_exposure.json", neo4j_session, common_job_parameters
    )

    # Assert: NLB -> Pod via Service path
    assert check_rels(
        neo4j_session,
        "AWSLoadBalancerV2",
        "id",
        "KubernetesPod",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {
        ("nlb-dns.elb.amazonaws.com", "pod-lb-uid"),
        ("alb-dns.elb.amazonaws.com", "pod-ing-uid"),
    }

    # Assert: NLB -> Container via Service path
    assert check_rels(
        neo4j_session,
        "AWSLoadBalancerV2",
        "id",
        "KubernetesContainer",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {
        ("nlb-dns.elb.amazonaws.com", "cont-lb-uid"),
        ("alb-dns.elb.amazonaws.com", "cont-ing-uid"),
    }


def test_k8s_asset_exposure_properties(neo4j_session):
    """
    Test that the k8s_compute_asset_exposure analysis job sets exposed_internet
    on Services, Pods, and Containers.
    """
    # Arrange
    _create_prereq_nodes(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Act
    run_scoped_analysis_job(
        "k8s_compute_asset_exposure.json", neo4j_session, common_job_parameters
    )

    # Assert: LB-backed service is exposed
    result = neo4j_session.run(
        "MATCH (svc:KubernetesService{id: 'svc-lb-uid'}) RETURN svc.exposed_internet AS exposed",
    )
    assert result.single()["exposed"] is True

    # Assert: Ingress-backed service is exposed
    result = neo4j_session.run(
        "MATCH (svc:KubernetesService{id: 'svc-clusterip-uid'}) RETURN svc.exposed_internet AS exposed",
    )
    assert result.single()["exposed"] is True

    # Assert: Both pods are exposed
    result = neo4j_session.run(
        "MATCH (pod:KubernetesPod) WHERE pod.exposed_internet = true RETURN pod.id AS id ORDER BY id",
    )
    assert [r["id"] for r in result] == ["pod-ing-uid", "pod-lb-uid"]

    # Assert: Both containers are exposed
    result = neo4j_session.run(
        "MATCH (c:KubernetesContainer) WHERE c.exposed_internet = true RETURN c.id AS id ORDER BY id",
    )
    assert [r["id"] for r in result] == ["cont-ing-uid", "cont-lb-uid"]
