import copy
import datetime

from cartography.intel.aws.ec2.load_balancer_v2s import load_load_balancer_v2s
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.ingress import load_ingresses
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.pods import load_containers
from cartography.intel.kubernetes.pods import load_pods
from cartography.intel.kubernetes.services import load_services
from cartography.util import run_analysis_job
from cartography.util import run_scoped_analysis_job
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_rels

TEST_CLUSTER_ID = "arn:aws:eks:us-east-1:000000000000:cluster/test-cluster"
TEST_CLUSTER_NAME = "test-cluster"
TEST_AWS_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


TEST_CLUSTER = [
    {
        "id": TEST_CLUSTER_ID,
        "name": TEST_CLUSTER_NAME,
        "creation_timestamp": 1234567890,
        "external_id": TEST_CLUSTER_ID,
        "git_version": "v1.30.0",
        "version_major": 1,
        "version_minor": 30,
        "go_version": "go1.16.5",
        "compiler": "gc",
        "platform": "linux/amd64",
    },
]

TEST_NAMESPACES = [
    {
        "uid": "default-ns-uid",
        "name": "default",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "status_phase": "Active",
    },
]

TEST_PODS = [
    {
        "uid": "pod-lb-uid",
        "name": "pod-lb",
        "status_phase": "running",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": "default",
        "node": "node-1",
        "labels": '{"app": "lb-app"}',
        "containers": [],
        "secret_volume_ids": [],
        "secret_env_ids": [],
    },
    {
        "uid": "pod-ing-uid",
        "name": "pod-ing",
        "status_phase": "running",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": "default",
        "node": "node-1",
        "labels": '{"app": "ing-app"}',
        "containers": [],
        "secret_volume_ids": [],
        "secret_env_ids": [],
    },
]

TEST_CONTAINERS = [
    {
        "uid": "cont-lb-uid",
        "name": "web",
        "image": "example/web:latest",
        "namespace": "default",
        "pod_id": "pod-lb-uid",
        "image_pull_policy": "Always",
        "status_image_id": "img-1",
        "status_image_sha": "sha256:1",
        "status_ready": True,
        "status_started": True,
        "status_state": "running",
        "memory_request": "128Mi",
        "cpu_request": "100m",
        "memory_limit": "256Mi",
        "cpu_limit": "500m",
    },
    {
        "uid": "cont-ing-uid",
        "name": "api",
        "image": "example/api:latest",
        "namespace": "default",
        "pod_id": "pod-ing-uid",
        "image_pull_policy": "Always",
        "status_image_id": "img-2",
        "status_image_sha": "sha256:2",
        "status_ready": True,
        "status_started": True,
        "status_state": "running",
        "memory_request": "128Mi",
        "cpu_request": "100m",
        "memory_limit": "256Mi",
        "cpu_limit": "500m",
    },
]

TEST_SERVICES = [
    {
        "uid": "svc-lb-uid",
        "name": "my-lb-svc",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": "default",
        "type": "LoadBalancer",
        "selector": '{"app":"lb-app"}',
        "cluster_ip": "10.0.0.10",
        "pod_ids": ["pod-lb-uid"],
        "load_balancer_ip": None,
        "load_balancer_ingress": '[{"hostname":"nlb-dns.elb.amazonaws.com"}]',
        "load_balancer_dns_names": ["nlb-dns.elb.amazonaws.com"],
    },
    {
        "uid": "svc-clusterip-uid",
        "name": "my-clusterip-svc",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": "default",
        "type": "ClusterIP",
        "selector": '{"app":"ing-app"}',
        "cluster_ip": "10.0.0.20",
        "pod_ids": ["pod-ing-uid"],
        "load_balancer_ip": None,
    },
]

TEST_INGRESS = {
    "uid": "ing-uid",
    "name": "my-ingress",
    "namespace": "default",
    "creation_timestamp": 1633581666,
    "deletion_timestamp": None,
    "annotations": "{}",
    "ingress_class_name": "alb",
    "rules": "[]",
    "default_backend": "{}",
    "target_services": ["my-clusterip-svc"],
    "ingress_group_name": None,
    "load_balancer_dns_names": ["alb-dns.elb.amazonaws.com"],
}

TEST_DUPLICATE_INGRESS = {
    "uid": "ing-uid-2",
    "name": "my-ingress-2",
    "namespace": "default",
    "creation_timestamp": 1633581666,
    "deletion_timestamp": None,
    "annotations": "{}",
    "ingress_class_name": "alb",
    "rules": "[]",
    "default_backend": "{}",
    "target_services": ["my-clusterip-svc"],
    "ingress_group_name": None,
    "load_balancer_dns_names": ["alb-dns.elb.amazonaws.com"],
}

TEST_LB_DATA = [
    {
        "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:loadbalancer/net/test-nlb/1234567890",
        "DNSName": "nlb-dns.elb.amazonaws.com",
        "CanonicalHostedZoneId": "Z26RNL4JYFTOTI",
        "CreatedTime": datetime.datetime(2021, 1, 1, 12, 0, 0),
        "LoadBalancerName": "test-nlb",
        "Scheme": "internet-facing",
        "VpcId": "vpc-12345678",
        "State": {"Code": "active"},
        "Type": "network",
        "AvailabilityZones": [
            {
                "ZoneName": "us-east-1a",
                "SubnetId": "subnet-11111111",
            },
        ],
        "Listeners": [
            {
                "ListenerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/net/test-nlb/1234567890/abcdef",
                "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:loadbalancer/net/test-nlb/1234567890",
                "Port": 80,
                "Protocol": "TCP",
            },
        ],
        "TargetGroups": [],
    },
    {
        "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:loadbalancer/app/test-alb/1234567890",
        "DNSName": "alb-dns.elb.amazonaws.com",
        "CanonicalHostedZoneId": "Z35SXDOTRQ7X7K",
        "CreatedTime": datetime.datetime(2021, 1, 1, 12, 0, 0),
        "LoadBalancerName": "test-alb",
        "Scheme": "internet-facing",
        "VpcId": "vpc-12345678",
        "State": {"Code": "active"},
        "Type": "application",
        "AvailabilityZones": [
            {
                "ZoneName": "us-east-1a",
                "SubnetId": "subnet-22222222",
            },
        ],
        "SecurityGroups": ["sg-12345678"],
        "Listeners": [
            {
                "ListenerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/test-alb/1234567890/abcdef",
                "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:loadbalancer/app/test-alb/1234567890",
                "Port": 80,
                "Protocol": "HTTP",
            },
        ],
        "TargetGroups": [],
    },
]


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
