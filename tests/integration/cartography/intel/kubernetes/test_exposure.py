import copy

from cartography.intel.aws.ec2.load_balancer_v2s import load_load_balancer_v2s
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.ingress import load_ingresses
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.pods import load_containers
from cartography.intel.kubernetes.pods import load_pods
from cartography.intel.kubernetes.services import load_services
from cartography.util import run_analysis_job
from cartography.util import run_scoped_analysis_job
from tests.data.kubernetes.exposure import TEST_AWS_ACCOUNT_ID
from tests.data.kubernetes.exposure import TEST_CLUSTER
from tests.data.kubernetes.exposure import TEST_CLUSTER_ID
from tests.data.kubernetes.exposure import TEST_CLUSTER_NAME
from tests.data.kubernetes.exposure import TEST_CONTAINERS
from tests.data.kubernetes.exposure import TEST_DUPLICATE_INGRESS
from tests.data.kubernetes.exposure import TEST_INGRESS
from tests.data.kubernetes.exposure import TEST_LB_DATA
from tests.data.kubernetes.exposure import TEST_NAMESPACES
from tests.data.kubernetes.exposure import TEST_PODS
from tests.data.kubernetes.exposure import TEST_REGION
from tests.data.kubernetes.exposure import TEST_SERVICES
from tests.data.kubernetes.exposure import TEST_UPDATE_TAG
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_rels


def _seed_exposure_graph(neo4j_session, *, include_duplicate_ingress: bool = False):
    create_test_account(neo4j_session, TEST_AWS_ACCOUNT_ID, TEST_UPDATE_TAG)
    load_kubernetes_cluster(neo4j_session, TEST_CLUSTER, TEST_UPDATE_TAG)
    load_namespaces(
        neo4j_session,
        TEST_NAMESPACES,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=TEST_CLUSTER_ID,
        cluster_name=TEST_CLUSTER_NAME,
    )
    load_pods(
        neo4j_session,
        TEST_PODS,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=TEST_CLUSTER_ID,
        cluster_name=TEST_CLUSTER_NAME,
    )
    load_containers(
        neo4j_session,
        TEST_CONTAINERS,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=TEST_CLUSTER_ID,
        cluster_name=TEST_CLUSTER_NAME,
        region=TEST_REGION,
    )
    load_load_balancer_v2s(
        neo4j_session,
        copy.deepcopy(TEST_LB_DATA),
        TEST_REGION,
        TEST_AWS_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    # Keep ingress-path tests deterministic: ALB exposure is modeled via aws_ec2_asset_exposure,
    # but these scoped-job tests exercise only k8s jobs.
    neo4j_session.run(
        "MATCH (lb:AWSLoadBalancerV2{id: 'alb-dns.elb.amazonaws.com'}) "
        "SET lb.exposed_internet = true"
    )
    load_services(
        neo4j_session,
        TEST_SERVICES,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=TEST_CLUSTER_ID,
        cluster_name=TEST_CLUSTER_NAME,
    )

    ingresses = [TEST_INGRESS]
    if include_duplicate_ingress:
        ingresses.append(TEST_DUPLICATE_INGRESS)
    load_ingresses(
        neo4j_session,
        ingresses,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=TEST_CLUSTER_ID,
        cluster_name=TEST_CLUSTER_NAME,
    )


def test_k8s_lb_expose_via_service(neo4j_session):
    """
    Test that the k8s_lb_exposure analysis job creates EXPOSE rels
    from an internet-facing NLB to Pods and Containers via Service type=LoadBalancer.
    """
    # Arrange
    _seed_exposure_graph(neo4j_session)
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
    _seed_exposure_graph(neo4j_session)
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


def test_k8s_asset_exposure_type_deduplicates_on_multiple_paths(neo4j_session):
    _seed_exposure_graph(neo4j_session, include_duplicate_ingress=True)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    run_scoped_analysis_job(
        "k8s_compute_asset_exposure.json", neo4j_session, common_job_parameters
    )

    result = neo4j_session.run(
        "MATCH (svc:KubernetesService{id: 'svc-clusterip-uid'}) "
        "RETURN svc.exposed_internet_type AS exposure_types",
    )
    assert result.single()["exposure_types"] == ["lb"]

    result = neo4j_session.run(
        "MATCH (pod:KubernetesPod{id: 'pod-ing-uid'}) "
        "RETURN pod.exposed_internet_type AS exposure_types",
    )
    assert result.single()["exposure_types"] == ["lb"]

    result = neo4j_session.run(
        "MATCH (c:KubernetesContainer{id: 'cont-ing-uid'}) "
        "RETURN c.exposed_internet_type AS exposure_types",
    )
    assert result.single()["exposure_types"] == ["lb"]


def test_nlb_internet_exposure_propagates_to_kubernetes_compute(neo4j_session):
    _seed_exposure_graph(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
        "AWS_ID": TEST_AWS_ACCOUNT_ID,
    }

    run_analysis_job(
        "aws_ec2_asset_exposure.json", neo4j_session, common_job_parameters
    )
    run_scoped_analysis_job(
        "k8s_compute_asset_exposure.json", neo4j_session, common_job_parameters
    )
    run_scoped_analysis_job(
        "k8s_lb_exposure.json", neo4j_session, common_job_parameters
    )

    result = neo4j_session.run(
        "MATCH (lb:AWSLoadBalancerV2{id: 'nlb-dns.elb.amazonaws.com'}) "
        "RETURN lb.exposed_internet AS exposed",
    )
    assert result.single()["exposed"] is True

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
