from cartography.util import run_analysis_job
from cartography.util import run_scoped_analysis_job
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "cluster-1"


def _create_nlb_backed_service_graph(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    neo4j_session.run(
        "MERGE (cluster:KubernetesCluster{id: $id}) SET cluster.lastupdated = $tag",
        id=TEST_CLUSTER_ID,
        tag=TEST_UPDATE_TAG,
    )

    neo4j_session.run(
        "MERGE (lb:AWSLoadBalancerV2:LoadBalancerV2{id: 'nlb-public'}) "
        "SET lb.scheme = 'internet-facing', lb.type = 'network', lb.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (listener:ELBV2Listener{id: 'listener-80'}) "
        "SET listener.port = 80, listener.protocol = 'TCP', listener.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MATCH (lb:LoadBalancerV2{id: 'nlb-public'}), (listener:ELBV2Listener{id: 'listener-80'}) "
        "MERGE (lb)-[:HAS_LISTENER]->(listener)",
    )

    neo4j_session.run(
        "MERGE (svc:KubernetesService{id: 'svc-uid', name: 'svc', namespace: 'default'}) "
        "SET svc.lastupdated = $tag, svc.type = 'LoadBalancer'",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MATCH (cluster:KubernetesCluster{id: $cid}), (svc:KubernetesService{id: 'svc-uid'}) "
        "MERGE (cluster)-[:RESOURCE]->(svc)",
        cid=TEST_CLUSTER_ID,
    )
    neo4j_session.run(
        "MATCH (svc:KubernetesService{id: 'svc-uid'}), (lb:AWSLoadBalancerV2{id: 'nlb-public'}) "
        "MERGE (svc)-[:USES_LOAD_BALANCER]->(lb)",
    )

    neo4j_session.run(
        "MERGE (pod:KubernetesPod{id: 'pod-uid', name: 'pod', namespace: 'default'}) "
        "SET pod.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MATCH (cluster:KubernetesCluster{id: $cid}), (pod:KubernetesPod{id: 'pod-uid'}) "
        "MERGE (cluster)-[:RESOURCE]->(pod)",
        cid=TEST_CLUSTER_ID,
    )
    neo4j_session.run(
        "MATCH (svc:KubernetesService{id: 'svc-uid'}), (pod:KubernetesPod{id: 'pod-uid'}) "
        "MERGE (svc)-[:TARGETS]->(pod)",
    )

    neo4j_session.run(
        "MERGE (c:KubernetesContainer{id: 'container-uid', name: 'container', namespace: 'default'}) "
        "SET c.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MATCH (pod:KubernetesPod{id: 'pod-uid'}), (c:KubernetesContainer{id: 'container-uid'}) "
        "MERGE (pod)-[:CONTAINS]->(c)",
    )


def test_nlb_internet_exposure_propagates_to_kubernetes_compute(neo4j_session):
    _create_nlb_backed_service_graph(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    run_analysis_job(
        "aws_ec2_asset_exposure.json", neo4j_session, common_job_parameters
    )
    run_scoped_analysis_job(
        "k8s_compute_asset_exposure.json",
        neo4j_session,
        common_job_parameters,
    )
    run_scoped_analysis_job(
        "k8s_lb_exposure.json",
        neo4j_session,
        common_job_parameters,
    )

    result = neo4j_session.run(
        "MATCH (lb:AWSLoadBalancerV2{id: 'nlb-public'}) "
        "RETURN lb.exposed_internet AS exposed",
    )
    assert result.single()["exposed"] is True

    result = neo4j_session.run(
        "MATCH (svc:KubernetesService{id: 'svc-uid'}) "
        "RETURN svc.exposed_internet AS exposed, svc.exposed_internet_type AS exposure_types",
    )
    record = result.single()
    assert record["exposed"] is True
    assert record["exposure_types"] == ["lb"]

    result = neo4j_session.run(
        "MATCH (pod:KubernetesPod{id: 'pod-uid'}) "
        "RETURN pod.exposed_internet AS exposed, pod.exposed_internet_type AS exposure_types",
    )
    record = result.single()
    assert record["exposed"] is True
    assert record["exposure_types"] == ["lb"]

    result = neo4j_session.run(
        "MATCH (c:KubernetesContainer{id: 'container-uid'}) "
        "RETURN c.exposed_internet AS exposed, c.exposed_internet_type AS exposure_types",
    )
    record = result.single()
    assert record["exposed"] is True
    assert record["exposure_types"] == ["lb"]

    assert check_rels(
        neo4j_session,
        "AWSLoadBalancerV2",
        "id",
        "KubernetesPod",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {("nlb-public", "pod-uid")}

    assert check_rels(
        neo4j_session,
        "AWSLoadBalancerV2",
        "id",
        "KubernetesContainer",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {("nlb-public", "container-uid")}
