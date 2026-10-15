"""Kubernetes pods that no internet path modelled in the graph reaches."""

import json
from unittest.mock import patch

import pytest

from cartography.analysis.kubernetes.analysis import K8S_COMPUTE_ASSET_EXPOSURE_JOBS
from cartography.analysis.kubernetes.analysis import K8S_LB_EXPOSURE_JOBS
from cartography.analysis.kubernetes.analysis import K8S_NO_MODELED_INTERNET_PATH
from cartography.analysis.kubernetes.analysis import K8S_UNMODELED_INTERNET_PATHS
from cartography.intel.aws import _check_unmodeled_internet_paths
from cartography.intel.aws import AWS_UNMODELED_INTERNET_PATHS_DEPS
from cartography.intel.aws import cloudfront
from cartography.intel.aws.ec2 import load_balancer_v2s as elbv2
from cartography.intel.aws.ec2.instances import load_ec2_instance_data
from cartography.intel.aws.ec2.instances import transform_ec2_instances
from cartography.intel.aws.ec2.network_interfaces import load_network_data
from cartography.intel.aws.ec2.network_interfaces import (
    transform_network_interface_data,
)
from cartography.intel.aws.ec2.subnets import load_subnets
from cartography.intel.kubernetes import gateway_api
from cartography.intel.kubernetes import ingress
from cartography.intel.kubernetes import services
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.nodes import load_nodes
from cartography.intel.kubernetes.pods import load_containers
from cartography.intel.kubernetes.pods import load_pods
from cartography.util import run_typed_analysis_job
from tests.data.aws.cloudfront import CLOUDFRONT_DISTRIBUTIONS_VPC_ORIGIN
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.cartography.intel.aws.common import make_load_balancer_v2
from tests.integration.util import check_nodes

ACCOUNT = "123456789012"
REGION = "us-east-1"
VPC = "vpc-0example"
SUBNET = "subnet-0example"
CLUSTER_NAME = "example"
CLUSTER_ID = f"arn:aws:eks:{REGION}:{ACCOUNT}:cluster/{CLUSTER_NAME}"
NODE_ID = f"{CLUSTER_NAME}/node-1"
NODE_INSTANCE = "i-0example0node00001"
NODE_ENI = "eni-0example0node0001"
# With the VPC CNI, pod IPs are secondary IPs on the node's interface.
POD_IP = "10.0.5.20"
INTERNAL_NLB = "internal-nlb.example.invalid"
PUBLIC_NLB = "public-nlb.example.invalid"
INTERNAL_ALB = "internal-alb.example.invalid"
PUBLIC_ALB = "public-alb.example.invalid"
CHAINED_ALB = "internal-chained.example.invalid"
EDGE_NLB = "public-edge.example.invalid"
POD_IP_ALB = "public-pod-ip.example.invalid"
MISSING_LB = "missing-lb.example.invalid"


def _arn(dns):
    return f"arn:aws:elasticloadbalancing:{REGION}:{ACCOUNT}:loadbalancer/{dns}"


LOAD_BALANCERS = [
    make_load_balancer_v2(INTERNAL_NLB, "internal", "network"),
    make_load_balancer_v2(PUBLIC_NLB, "internet-facing", "network"),
    make_load_balancer_v2(INTERNAL_ALB, "internal", "application"),
    make_load_balancer_v2(PUBLIC_ALB, "internet-facing", "application"),
    make_load_balancer_v2(CHAINED_ALB, "internal", "application"),
    # An internet-facing NLB forwarding to the internal ALB of an Ingress.
    make_load_balancer_v2(
        EDGE_NLB, "internet-facing", "network", [("alb", [_arn(CHAINED_ALB)])]
    ),
]
# An IP target group registered outside any Service or Ingress, as a
# TargetGroupBinding does, that sends internet traffic to a pod IP.
POD_IP_LOAD_BALANCER = make_load_balancer_v2(
    POD_IP_ALB, "internet-facing", "application", [("ip", [POD_IP])]
)
# The static IP pattern for an ALB: an internet-facing NLB whose IP target group
# lists the private IP of an internal ALB's own interface.
ALB_INTERFACE_IP = "10.0.5.200"
ALB_INTERFACE = {
    "NetworkInterfaceId": "eni-0example0alb00001",
    "Description": "ELB app/internal-alb/50dc6c495c0c9188",
    "InterfaceType": "interface",
    "MacAddress": "02:00:00:00:00:03",
    "RequesterId": "amazon-elb",
    "RequesterManaged": True,
    "SourceDestCheck": True,
    "Status": "in-use",
    "SubnetId": SUBNET,
    "PrivateIpAddress": ALB_INTERFACE_IP,
    "PrivateIpAddresses": [{"PrivateIpAddress": ALB_INTERFACE_IP, "Primary": True}],
    "Groups": [],
}
STATIC_IP_LOAD_BALANCER = make_load_balancer_v2(
    "static-ip.example.invalid",
    "internet-facing",
    "network",
    [("ip", [ALB_INTERFACE_IP])],
)


def _pod(name, *, host_network=False, host_ports=()):
    return {
        "uid": f"pod-{name}",
        "name": name,
        "status_phase": "Running",
        "creation_timestamp": 1767225600,
        "deletion_timestamp": None,
        "namespace": "default",
        "node": "node-1",
        "labels": json.dumps({"app": name}),
        "host_network": host_network,
        "host_ports": list(host_ports),
        "containers": [],
        "secret_volume_ids": [],
        "secret_env_ids": [],
    }


def _container(name):
    return {
        "uid": f"pod-{name}/app",
        "name": "app",
        "image": "registry.example.com/app:1.0.0",
        "namespace": "default",
        "pod_id": f"pod-{name}",
        "status_state": "running",
    }


def _service(name, service_type, *, pods, lb_dns=None, selector=True):
    service = {
        "uid": f"svc-{name}",
        "name": name,
        "creation_timestamp": 1767225600,
        "deletion_timestamp": None,
        "namespace": "default",
        "type": service_type,
        "selector": json.dumps({"app": name} if selector else None),
        "cluster_ip": "10.100.0.10",
        "load_balancer_ip": None,
        "pod_ids": [f"pod-{pod}" for pod in pods],
    }
    if lb_dns:
        service["load_balancer_ingress"] = json.dumps([{"hostname": lb_dns}])
        service["load_balancer_dns_names"] = [lb_dns]
    return service


def _ingress(name, *, service, lb_dns, ingress_class="alb"):
    return {
        "uid": f"ing-{name}",
        "name": name,
        "namespace": "default",
        "creation_timestamp": 1767225600,
        "deletion_timestamp": None,
        "annotations": "{}",
        "ingress_class_name": ingress_class,
        "rules": "[]",
        "default_backend": "{}",
        "target_services": [service],
        "ingress_group_name": None,
        "load_balancer_dns_names": [lb_dns],
    }


CLEAR = {"clusterip", "ingress-internal"}
PODS = [
    _pod("clusterip"),
    _pod("internal-nlb"),
    _pod("public-nlb"),
    _pod("nodeport"),
    _pod("host-network", host_network=True),
    _pod("host-port", host_ports=[8080]),
    _pod("ingress-internal"),
    _pod("ingress-public"),
    _pod("ingress-chained"),
    _pod("ingress-controller-backend"),
]
CONTAINERS = [_container(pod["name"]) for pod in PODS]
SERVICES = [
    _service("clusterip", "ClusterIP", pods=["clusterip", "host-network", "host-port"]),
    # A LoadBalancer Service opens a node port on every node, even behind an internal
    # load balancer.
    _service(
        "internal-nlb", "LoadBalancer", pods=["internal-nlb"], lb_dns=INTERNAL_NLB
    ),
    _service("public-nlb", "LoadBalancer", pods=["public-nlb"], lb_dns=PUBLIC_NLB),
    _service("nodeport", "NodePort", pods=["nodeport"]),
    _service("ingress-internal", "ClusterIP", pods=["ingress-internal"]),
    _service("ingress-public", "ClusterIP", pods=["ingress-public"]),
    _service("ingress-chained", "ClusterIP", pods=["ingress-chained"]),
    _service(
        "ingress-controller-backend",
        "ClusterIP",
        pods=["ingress-controller-backend"],
    ),
]
INGRESSES = [
    _ingress("internal", service="ingress-internal", lb_dns=INTERNAL_ALB),
    _ingress("public", service="ingress-public", lb_dns=PUBLIC_ALB),
    _ingress("chained", service="ingress-chained", lb_dns=CHAINED_ALB),
    # An in-cluster controller such as ingress-nginx publishes its LoadBalancer
    # Service's load balancer on the Ingress, and routes what reaches its node
    # port to the Ingress's backends.
    _ingress(
        "controller",
        service="ingress-controller-backend",
        lb_dns=INTERNAL_NLB,
        ingress_class="nginx",
    ),
]
GATEWAY = {
    "metadata": {"uid": "gw-edge", "name": "edge", "namespace": "default"},
    "spec": {"gatewayClassName": "example"},
}
HTTP_ROUTE = {
    "metadata": {"uid": "route-web", "name": "web", "namespace": "default"},
    "spec": {
        "parentRefs": [{"name": "edge"}],
        "rules": [{"backendRefs": [{"name": "clusterip"}]}],
    },
}


def _load_node_instance(session, tag, *, ipv6=False, pod_ip_public=False):
    """The node's EC2 instance and its interface, which holds a pod IP."""
    load_subnets(session, [{"SubnetId": SUBNET, "VpcId": VPC}], REGION, ACCOUNT, tag)
    interface = {
        "NetworkInterfaceId": NODE_ENI,
        "Description": "",
        "InterfaceType": "interface",
        "MacAddress": "02:00:00:00:00:02",
        "RequesterManaged": False,
        "SourceDestCheck": True,
        "Status": "in-use",
        "SubnetId": SUBNET,
        "Attachment": {"InstanceId": NODE_INSTANCE, "DeviceIndex": 0},
        "PrivateIpAddress": "10.0.5.10",
        "PrivateIpAddresses": [
            {"PrivateIpAddress": "10.0.5.10", "Primary": True},
            {"PrivateIpAddress": POD_IP, "Primary": False},
        ],
        "Groups": [],
        "Ipv6Addresses": (
            [{"Ipv6Address": "2001:db8::5:20", "IsPrimaryIpv6": True}] if ipv6 else []
        ),
    }
    if pod_ip_public:
        interface["PrivateIpAddresses"][1]["Association"] = {"PublicIp": "203.0.113.20"}
    instances = transform_ec2_instances(
        [
            {
                "ReservationId": "r-0example",
                "OwnerId": ACCOUNT,
                "Instances": [
                    {
                        "InstanceId": NODE_INSTANCE,
                        "State": {"Name": "running"},
                        "SubnetId": SUBNET,
                        "SecurityGroups": [],
                        "NetworkInterfaces": [interface],
                    }
                ],
            }
        ],
        REGION,
        ACCOUNT,
    )
    load_ec2_instance_data(session, REGION, ACCOUNT, tag, *instances)
    network = transform_network_interface_data([interface], REGION)
    load_network_data(session, REGION, ACCOUNT, tag, **network._asdict())


def _sync(
    session,
    tag,
    *,
    pods=PODS,
    containers=CONTAINERS,
    service_list=SERVICES,
    ingresses=INGRESSES,
    gateway_api_objects=False,
    node_instance=True,
    node_ipv6=False,
    pod_ip_public=False,
    pod_ip_load_balancer=False,
    static_ip_load_balancer=False,
    vpc_origin=False,
    aws_check=True,
):
    """
    Sync the load balancers' AWS account and run its check of unmodeled internet
    paths, then load one cluster with the real loaders and clean up what this run did
    not see.
    """
    params = {"UPDATE_TAG": tag, "CLUSTER_ID": CLUSTER_ID}
    aws_params = {"UPDATE_TAG": tag, "AWS_ID": ACCOUNT}
    create_test_account(session, ACCOUNT, tag)
    if node_instance:
        _load_node_instance(session, tag, ipv6=node_ipv6, pod_ip_public=pod_ip_public)
    load_balancers = (
        LOAD_BALANCERS
        + ([POD_IP_LOAD_BALANCER] if pod_ip_load_balancer else [])
        + ([STATIC_IP_LOAD_BALANCER] if static_ip_load_balancer else [])
    )
    if static_ip_load_balancer:
        network = transform_network_interface_data([ALB_INTERFACE], REGION)
        load_network_data(session, REGION, ACCOUNT, tag, **network._asdict())
    elbv2.load_load_balancer_v2s(session, load_balancers, REGION, ACCOUNT, tag)
    with patch.object(elbv2, "get_loadbalancer_v2_data", return_value=load_balancers):
        elbv2.sync_load_balancer_v2_expose(
            session, None, [REGION], ACCOUNT, tag, aws_params
        )
    cloudfront.load_cloudfront_distributions(
        session,
        cloudfront.transform_cloudfront_distributions(
            CLOUDFRONT_DISTRIBUTIONS_VPC_ORIGIN if vpc_origin else []
        ),
        ACCOUNT,
        tag,
    )
    cloudfront.cleanup_cloudfront_distributions(session, aws_params)
    if aws_check:
        _check_unmodeled_internet_paths(
            session, AWS_UNMODELED_INTERNET_PATHS_DEPS, aws_params
        )

    load_kubernetes_cluster(
        session,
        [{"id": CLUSTER_ID, "name": CLUSTER_NAME, "external_id": CLUSTER_ID}],
        tag,
    )
    load_namespaces(
        session,
        [{"uid": "ns-default", "name": "default", "status_phase": "Active"}],
        update_tag=tag,
        cluster_id=CLUSTER_ID,
        cluster_name=CLUSTER_NAME,
    )
    load_nodes(
        session,
        [{"id": NODE_ID, "name": "node-1", "instance_id": NODE_INSTANCE}],
        update_tag=tag,
        cluster_id=CLUSTER_ID,
        cluster_name=CLUSTER_NAME,
    )
    kwargs = {"update_tag": tag, "cluster_id": CLUSTER_ID, "cluster_name": CLUSTER_NAME}
    load_pods(session, pods, **kwargs)
    load_containers(session, containers, region=REGION, **kwargs)
    services.load_services(session, service_list, **kwargs)
    services.cleanup(session, params)
    gateways = gateway_api.transform_gateways([GATEWAY] if gateway_api_objects else [])
    routes = gateway_api.transform_http_routes(
        [HTTP_ROUTE] if gateway_api_objects else []
    )
    gateway_api.load_gateways(session, gateways, **kwargs)
    gateway_api.load_http_routes(session, routes, **kwargs)
    gateway_api.cleanup(session, params)
    ingress.load_ingresses(session, ingresses, **kwargs)
    ingress.cleanup(session, params)


def _analyze(session, tag):
    """Run the cluster's analysis jobs in the order the Kubernetes sync runs them."""
    params = {"UPDATE_TAG": tag, "CLUSTER_ID": CLUSTER_ID, "CHECK_INPUTS_SYNCED": True}
    for job in (
        *K8S_COMPUTE_ASSET_EXPOSURE_JOBS,
        *K8S_LB_EXPOSURE_JOBS,
        K8S_UNMODELED_INTERNET_PATHS,
        K8S_NO_MODELED_INTERNET_PATH,
    ):
        run_typed_analysis_job(job, session, params)


def _results(session, label):
    return {
        (node_id, clear, checked_at)
        for node_id, clear, checked_at in check_nodes(
            session,
            label,
            ["id", "no_modeled_internet_path", "no_modeled_internet_path_checked_at"],
        )
        if clear is not None or checked_at is not None
    }


def _cluster_check(session):
    return (
        session.run(
            "MATCH (c:KubernetesCluster {id: $id}) "
            "RETURN c.unmodeled_internet_paths AS paths, "
            "c.unmodeled_internet_path_count AS count, "
            "c.unmodeled_internet_paths_checked_at AS checked_at",
            id=CLUSTER_ID,
        )
        .single()
        .data()
    )


@pytest.fixture
def neo4j_session_empty(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    return neo4j_session


def test_only_pods_behind_private_entry_points_have_no_modeled_internet_path(
    neo4j_session_empty,
):
    session = neo4j_session_empty
    _sync(session, 1)

    _analyze(session, 1)

    assert _results(session, "KubernetesPod") == {
        (f"pod-{name}", True, 1) for name in CLEAR
    }
    assert _results(session, "KubernetesContainer") == {
        (f"pod-{name}/app", True, 1) for name in CLEAR
    }
    assert _cluster_check(session) == {"paths": None, "count": 0, "checked_at": 1}


def test_result_is_dropped_when_a_later_run_finds_exposure(neo4j_session_empty):
    session = neo4j_session_empty
    _sync(session, 1)
    _analyze(session, 1)

    reexposed = [
        (
            _service("clusterip", "NodePort", pods=["clusterip"])
            if svc["name"] == "clusterip"
            else svc
        )
        for svc in SERVICES
    ]
    _sync(session, 2, service_list=reexposed)
    _analyze(session, 2)

    assert _results(session, "KubernetesPod") == {
        (f"pod-{name}", True, 2) for name in CLEAR - {"clusterip"}
    }
    assert _results(session, "KubernetesContainer") == {
        (f"pod-{name}/app", True, 2) for name in CLEAR - {"clusterip"}
    }


@pytest.mark.parametrize(
    "entry_point,paths",
    [
        (
            {
                "ingresses": INGRESSES
                + [_ingress("unresolved", service="clusterip", lb_dns=MISSING_LB)]
            },
            ["ing-unresolved"],
        ),
        # A second status address, such as one ingress-nginx publishes with
        # --publish-status-address, may be an internet entry point.
        (
            {
                "ingresses": INGRESSES
                + [
                    {
                        **_ingress("partial", service="clusterip", lb_dns=INTERNAL_ALB),
                        "load_balancer_dns_names": [INTERNAL_ALB, MISSING_LB],
                    }
                ]
            },
            ["ing-partial"],
        ),
        (
            {
                "ingresses": INGRESSES
                + [
                    {
                        **_ingress("partial", service="clusterip", lb_dns=INTERNAL_ALB),
                        "load_balancer_ips": ["203.0.113.10"],
                    }
                ]
            },
            ["ing-partial"],
        ),
        (
            {
                "service_list": SERVICES
                + [_service("unresolved", "LoadBalancer", pods=[], lb_dns=MISSING_LB)]
            },
            ["svc-unresolved"],
        ),
        (
            {
                "service_list": SERVICES
                + [_service("manual", "NodePort", pods=[], selector=False)]
            },
            ["svc-manual"],
        ),
        # A Service whose endpoints are managed by hand, or an ExternalName
        # Service, which ignores any selector it has, is not linked to the pods it
        # reaches.
        (
            {
                "service_list": SERVICES
                + [_service("manual", "ClusterIP", pods=[], selector=False)],
                "ingresses": INGRESSES
                + [_ingress("manual", service="manual", lb_dns=PUBLIC_ALB)],
            },
            ["svc-manual"],
        ),
        (
            {
                "service_list": SERVICES
                + [_service("bridge", "ExternalName", pods=[])],
                "ingresses": INGRESSES
                + [_ingress("bridge", service="bridge", lb_dns=PUBLIC_ALB)],
            },
            ["svc-bridge"],
        ),
        ({"gateway_api_objects": True}, ["gw-edge", "route-web"]),
        ({"pod_ip_load_balancer": True}, [POD_IP_ALB]),
        ({"node_instance": False}, [NODE_ID]),
        ({"node_ipv6": True}, [NODE_ID]),
        ({"pod_ip_public": True}, [NODE_ID]),
    ],
    ids=[
        "unresolved_ingress",
        "ingress_with_an_unresolved_hostname",
        "ingress_with_an_ip_address",
        "unresolved_load_balancer_service",
        "node_port_service_without_selector",
        "ingress_to_service_without_selector",
        "ingress_to_external_name_service",
        "gateway_api",
        "load_balancer_ip_target_on_a_node",
        "node_instance_not_in_graph",
        "ipv6_on_a_node_interface",
        "public_ip_on_a_pod_ip",
    ],
)
def test_cluster_with_an_unmodeled_path_gets_no_result_until_it_goes(
    neo4j_session_empty, entry_point, paths
):
    session = neo4j_session_empty
    _sync(session, 1, **entry_point)
    _analyze(session, 1)

    assert _results(session, "KubernetesPod") == set()
    assert _cluster_check(session) == {
        "paths": paths,
        "count": len(paths),
        "checked_at": 1,
    }

    _sync(session, 2)
    _analyze(session, 2)

    assert _results(session, "KubernetesPod") == {
        (f"pod-{name}", True, 2) for name in CLEAR
    }
    assert _cluster_check(session) == {"paths": None, "count": 0, "checked_at": 2}


@pytest.mark.parametrize(
    "runs",
    [
        [{"vpc_origin": True}],
        [{"aws_check": False}],
        [{}, {"aws_check": False}],
        [{"static_ip_load_balancer": True}],
    ],
    ids=[
        "unmodeled_path",
        "not_checked",
        "checked_before_the_load_balancer_sync",
        "load_balancer_interface_target",
    ],
)
def test_internal_load_balancer_needs_a_clear_aws_account(neo4j_session_empty, runs):
    session = neo4j_session_empty
    # A CloudFront VPC origin, or a load balancer that targets the interface of one
    # in the account, can put the internet in front of any internal load balancer in
    # the account, and an unchecked account may have either.
    for tag, run in enumerate(runs, start=1):
        _sync(session, tag, **run)
        _analyze(session, tag)

    assert _results(session, "KubernetesPod") == {("pod-clusterip", True, len(runs))}


# A list call that failed leaves the previous Services, Ingresses, Nodes or Gateways
# in place, so the run cannot vouch for the cluster.
@pytest.mark.parametrize(
    "cluster_check",
    [None, {"CHECK_INPUTS_SYNCED": False}],
    ids=["not_run", "inputs_not_synced"],
)
def test_cluster_not_checked_since_the_pod_sync_gets_no_result(
    neo4j_session_empty, cluster_check
):
    session = neo4j_session_empty
    _sync(session, 1)
    _analyze(session, 1)

    _sync(session, 2)
    params = {"UPDATE_TAG": 2, "CLUSTER_ID": CLUSTER_ID}
    if cluster_check is not None:
        run_typed_analysis_job(
            K8S_UNMODELED_INTERNET_PATHS, session, {**params, **cluster_check}
        )
    run_typed_analysis_job(K8S_NO_MODELED_INTERNET_PATH, session, params)

    assert _results(session, "KubernetesPod") == set()


@pytest.mark.parametrize(
    "label,node_id",
    [("KubernetesPod", "pod-clusterip"), ("KubernetesContainer", "pod-clusterip/app")],
)
def test_result_is_never_written_on_a_runtime_marked_exposed(
    neo4j_session_empty, label, node_id
):
    session = neo4j_session_empty
    _sync(session, 1)
    # A future exposure rule may mark a runtime through a path this job does not
    # model. Run the jobs alone so the existing rules do not clear the mark.
    session.run(
        f"MATCH (n:{label} {{id: $id}}) SET n.exposed_internet = true", id=node_id
    )

    for job in (K8S_UNMODELED_INTERNET_PATHS, K8S_NO_MODELED_INTERNET_PATH):
        run_typed_analysis_job(
            job,
            session,
            {"UPDATE_TAG": 1, "CLUSTER_ID": CLUSTER_ID, "CHECK_INPUTS_SYNCED": True},
        )

    assert ("pod-clusterip", True, 1) not in _results(session, "KubernetesPod")
