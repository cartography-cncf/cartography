import copy

import pytest

from cartography.analysis.aws.analysis import AWS_EC2_ASSET_EXPOSURE_JOBS
from cartography.analysis.kubernetes.analysis import K8S_COMPUTE_ASSET_EXPOSURE_JOBS
from cartography.analysis.kubernetes.analysis import K8S_LB_EXPOSURE_JOBS
from cartography.intel.aws.ec2.load_balancer_v2s import load_load_balancer_v2s
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.endpoint_slices import load_endpoint_slices
from cartography.intel.kubernetes.gateway_api import load_gateways
from cartography.intel.kubernetes.gateway_api import load_http_routes
from cartography.intel.kubernetes.ingress import load_ingresses
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.pods import load_containers
from cartography.intel.kubernetes.pods import load_pods
from cartography.intel.kubernetes.services import load_services
from cartography.util import run_typed_analysis_job
from tests.data.kubernetes.exposure import build_exposure_test_data
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_rels


def _seed_exposure_graph(
    neo4j_session,
    *,
    case: dict,
    include_duplicate_ingress: bool = False,
    include_ingress: bool = True,
    nlb_scheme: str = "internet-facing",
    mark_alb_exposed: bool = True,
):
    create_test_account(neo4j_session, case["aws_account_id"], case["update_tag"])
    load_kubernetes_cluster(neo4j_session, case["cluster"], case["update_tag"])
    load_namespaces(
        neo4j_session,
        case["namespaces"],
        update_tag=case["update_tag"],
        cluster_id=case["cluster_id"],
        cluster_name=case["cluster_name"],
    )
    load_pods(
        neo4j_session,
        case["pods"],
        update_tag=case["update_tag"],
        cluster_id=case["cluster_id"],
        cluster_name=case["cluster_name"],
    )
    load_containers(
        neo4j_session,
        case["containers"],
        update_tag=case["update_tag"],
        cluster_id=case["cluster_id"],
        cluster_name=case["cluster_name"],
        region=case["region"],
    )

    lb_data = copy.deepcopy(case["lb_data"])
    for lb in lb_data:
        if lb["DNSName"] == case["nlb_dns"]:
            lb["Scheme"] = nlb_scheme

    load_load_balancer_v2s(
        neo4j_session,
        lb_data,
        case["region"],
        case["aws_account_id"],
        case["update_tag"],
    )

    # Keep ingress-path tests deterministic: ALB exposure is modeled via aws_ec2_asset_exposure,
    # but scoped-job tests exercise only k8s jobs.
    if mark_alb_exposed:
        neo4j_session.run(
            "MATCH (lb:AWSLoadBalancerV2{id: $alb_id}) SET lb.exposed_internet = true",
            alb_id=case["alb_dns"],
        )

    load_services(
        neo4j_session,
        case["services"],
        update_tag=case["update_tag"],
        cluster_id=case["cluster_id"],
        cluster_name=case["cluster_name"],
    )
    load_endpoint_slices(
        neo4j_session,
        [
            {
                "uid": f"slice-{service['uid']}",
                "name": f"slice-{service['uid']}",
                "namespace": service["namespace"],
                "address_type": "IPv4",
                "managed_by": "endpointslice-controller.k8s.io",
                "service_qualified_name": service["qualified_name"],
                "endpoints": "[]",
                "ports": "[]",
                "port_numbers": [8080],
                "port_keys": ["TCP/8080"],
                "ready_pod_ids": service["pod_ids"],
                "creation_timestamp": None,
                "deletion_timestamp": None,
            }
            for service in case["services"]
        ],
        update_tag=case["update_tag"],
        cluster_id=case["cluster_id"],
        cluster_name=case["cluster_name"],
    )

    if include_ingress:
        ingresses = [case["ingress"]]
        if include_duplicate_ingress:
            ingresses.append(case["duplicate_ingress"])
        load_ingresses(
            neo4j_session,
            ingresses,
            update_tag=case["update_tag"],
            cluster_id=case["cluster_id"],
            cluster_name=case["cluster_name"],
        )


def _run_k8s_compute_analysis(neo4j_session, common_job_parameters):
    for job in K8S_COMPUTE_ASSET_EXPOSURE_JOBS:
        run_typed_analysis_job(job, neo4j_session, common_job_parameters)


def _run_k8s_lb_analysis(neo4j_session, common_job_parameters):
    for job in K8S_LB_EXPOSURE_JOBS:
        run_typed_analysis_job(job, neo4j_session, common_job_parameters)


def test_k8s_lb_expose_via_service(neo4j_session):
    case = build_exposure_test_data()
    _seed_exposure_graph(neo4j_session, case=case)

    common_job_parameters = {
        "UPDATE_TAG": case["update_tag"],
        "CLUSTER_ID": case["cluster_id"],
    }

    _run_k8s_compute_analysis(neo4j_session, common_job_parameters)
    _run_k8s_lb_analysis(neo4j_session, common_job_parameters)

    result = neo4j_session.run(
        "MATCH (lb:AWSLoadBalancerV2)-[:EXPOSE]->(pod:KubernetesPod) "
        "WHERE lb.id IN $lbs AND pod.id IN $pods "
        "RETURN lb.id AS lb_id, pod.id AS pod_id",
        lbs=[case["nlb_dns"], case["alb_dns"]],
        pods=[case["pod_lb_id"], case["pod_ing_id"]],
    )
    assert {(r["lb_id"], r["pod_id"]) for r in result} == {
        (case["nlb_dns"], case["pod_lb_id"]),
        (case["alb_dns"], case["pod_ing_id"]),
    }

    result = neo4j_session.run(
        "MATCH (lb:AWSLoadBalancerV2)-[:EXPOSE]->(c:KubernetesContainer) "
        "WHERE lb.id IN $lbs AND c.id IN $containers "
        "RETURN lb.id AS lb_id, c.id AS container_id",
        lbs=[case["nlb_dns"], case["alb_dns"]],
        containers=[case["cont_lb_id"], case["cont_ing_id"]],
    )
    assert {(r["lb_id"], r["container_id"]) for r in result} == {
        (case["nlb_dns"], case["cont_lb_id"]),
        (case["alb_dns"], case["cont_ing_id"]),
    }


def test_k8s_asset_exposure_properties(neo4j_session):
    case = build_exposure_test_data()
    _seed_exposure_graph(neo4j_session, case=case)

    common_job_parameters = {
        "UPDATE_TAG": case["update_tag"],
        "CLUSTER_ID": case["cluster_id"],
    }

    _run_k8s_compute_analysis(neo4j_session, common_job_parameters)

    nlb_ontology = neo4j_session.run(
        """
        MATCH (lb:AWSLoadBalancerV2 {id: $lb_id})
        RETURN lb._ont_source AS source,
               lb._ont_scheme AS scheme,
               lb._ont_lb_type AS lb_type,
               lb.exposed_internet AS exposed
        """,
        lb_id=case["nlb_dns"],
    ).single()
    assert nlb_ontology == {
        "source": "aws",
        "scheme": "internet_facing",
        "lb_type": "network",
        "exposed": None,
    }

    result = neo4j_session.run(
        "MATCH (svc:KubernetesService{id: $svc_id}) "
        "RETURN svc.exposed_internet AS exposed",
        svc_id=case["svc_lb_id"],
    )
    assert result.single()["exposed"] is True

    result = neo4j_session.run(
        "MATCH (svc:KubernetesService{id: $svc_id}) "
        "RETURN svc.exposed_internet AS exposed",
        svc_id=case["svc_ing_id"],
    )
    assert result.single()["exposed"] is True

    result = neo4j_session.run(
        "MATCH (pod:KubernetesPod) "
        "WHERE pod.id IN $pods AND pod.exposed_internet = true "
        "RETURN pod.id AS id ORDER BY id",
        pods=[case["pod_ing_id"], case["pod_lb_id"]],
    )
    assert [r["id"] for r in result] == sorted([case["pod_ing_id"], case["pod_lb_id"]])

    result = neo4j_session.run(
        "MATCH (c:KubernetesContainer) "
        "WHERE c.id IN $containers AND c.exposed_internet = true "
        "RETURN c.id AS id ORDER BY id",
        containers=[case["cont_ing_id"], case["cont_lb_id"]],
    )
    assert [r["id"] for r in result] == sorted(
        [case["cont_ing_id"], case["cont_lb_id"]]
    )

    result = neo4j_session.run(
        """
        MATCH (c:KubernetesContainer {id: $container_id})
        OPTIONAL MATCH (:LoadBalancer)-[exposure:EXPOSE]->(c)
        RETURN c.exposed_internet AS exposed, count(exposure) AS relationship_count
        """,
        container_id=case["cont_lb_mismatch_id"],
    )
    assert result.single() == {"exposed": None, "relationship_count": 0}


def test_stale_endpoint_slices_do_not_attribute_container_exposure(neo4j_session):
    case = build_exposure_test_data()
    _seed_exposure_graph(neo4j_session, case=case)
    common_job_parameters = {
        "UPDATE_TAG": case["update_tag"],
        "CLUSTER_ID": case["cluster_id"],
    }

    _run_k8s_compute_analysis(neo4j_session, common_job_parameters)
    _run_k8s_lb_analysis(neo4j_session, common_job_parameters)
    assert (
        neo4j_session.run(
            "MATCH (container:KubernetesContainer {id: $container_id}) "
            "RETURN container.exposed_internet AS exposed",
            container_id=case["cont_lb_id"],
        ).single()["exposed"]
        is True
    )

    next_job_parameters = {
        "UPDATE_TAG": case["update_tag"] + 1,
        "CLUSTER_ID": case["cluster_id"],
    }
    _run_k8s_compute_analysis(neo4j_session, next_job_parameters)
    _run_k8s_lb_analysis(neo4j_session, next_job_parameters)

    result = neo4j_session.run(
        """
        MATCH (pod:KubernetesPod {id: $pod_id})
        MATCH (container:KubernetesContainer {id: $container_id})
        OPTIONAL MATCH (:LoadBalancer)-[exposure:EXPOSE]->(container)
        RETURN pod.exposed_internet AS pod_exposed,
               container.exposed_internet AS container_exposed,
               count(exposure) AS relationship_count
        """,
        pod_id=case["pod_lb_id"],
        container_id=case["cont_lb_id"],
    ).single()
    assert result == {
        "pod_exposed": True,
        "container_exposed": None,
        "relationship_count": 0,
    }


def test_k8s_asset_exposure_type_deduplicates_on_multiple_paths(neo4j_session):
    case = build_exposure_test_data()
    _seed_exposure_graph(neo4j_session, case=case, include_duplicate_ingress=True)

    common_job_parameters = {
        "UPDATE_TAG": case["update_tag"],
        "CLUSTER_ID": case["cluster_id"],
    }

    _run_k8s_compute_analysis(neo4j_session, common_job_parameters)

    result = neo4j_session.run(
        "MATCH (svc:KubernetesService{id: $svc_id}) "
        "RETURN svc.exposed_internet_type AS exposure_types",
        svc_id=case["svc_ing_id"],
    )
    assert result.single()["exposure_types"] == ["lb"]

    result = neo4j_session.run(
        "MATCH (pod:KubernetesPod{id: $pod_id}) "
        "RETURN pod.exposed_internet_type AS exposure_types",
        pod_id=case["pod_ing_id"],
    )
    assert result.single()["exposure_types"] == ["lb"]

    result = neo4j_session.run(
        "MATCH (c:KubernetesContainer{id: $container_id}) "
        "RETURN c.exposed_internet_type AS exposure_types",
        container_id=case["cont_ing_id"],
    )
    assert result.single()["exposure_types"] == ["lb"]


def test_nlb_internet_exposure_propagates_to_kubernetes_compute(neo4j_session):
    case = build_exposure_test_data()
    _seed_exposure_graph(neo4j_session, case=case)

    common_job_parameters = {
        "UPDATE_TAG": case["update_tag"],
        "CLUSTER_ID": case["cluster_id"],
        "AWS_ID": case["aws_account_id"],
    }

    for job in AWS_EC2_ASSET_EXPOSURE_JOBS:
        run_typed_analysis_job(job, neo4j_session, common_job_parameters)
    _run_k8s_compute_analysis(neo4j_session, common_job_parameters)
    _run_k8s_lb_analysis(neo4j_session, common_job_parameters)

    result = neo4j_session.run(
        "MATCH (lb:AWSLoadBalancerV2{id: $lb_id}) "
        "RETURN lb.exposed_internet AS exposed",
        lb_id=case["nlb_dns"],
    )
    assert result.single()["exposed"] is True

    result = neo4j_session.run(
        "MATCH (lb:AWSLoadBalancerV2{id: $lb_id})-[:EXPOSE]->(pod:KubernetesPod{id: $pod_id}) "
        "RETURN count(*) AS rel_count",
        lb_id=case["nlb_dns"],
        pod_id=case["pod_lb_id"],
    )
    assert result.single()["rel_count"] == 1


def test_internal_nlb_does_not_propagate_exposure(neo4j_session):
    case = build_exposure_test_data()
    _seed_exposure_graph(
        neo4j_session,
        case=case,
        include_ingress=False,
        nlb_scheme="internal",
        mark_alb_exposed=False,
    )

    common_job_parameters = {
        "UPDATE_TAG": case["update_tag"],
        "CLUSTER_ID": case["cluster_id"],
    }

    _run_k8s_compute_analysis(neo4j_session, common_job_parameters)
    _run_k8s_lb_analysis(neo4j_session, common_job_parameters)

    result = neo4j_session.run(
        "MATCH (svc:KubernetesService{id: $svc_id}) "
        "RETURN svc.exposed_internet AS exposed, svc.exposed_internet_type AS exposure_types",
        svc_id=case["svc_lb_id"],
    )
    record = result.single()
    assert record["exposed"] is None
    assert record["exposure_types"] is None

    result = neo4j_session.run(
        "MATCH (pod:KubernetesPod{id: $pod_id}) "
        "RETURN pod.exposed_internet AS exposed, pod.exposed_internet_type AS exposure_types",
        pod_id=case["pod_lb_id"],
    )
    record = result.single()
    assert record["exposed"] is None
    assert record["exposure_types"] is None

    result = neo4j_session.run(
        "MATCH (c:KubernetesContainer{id: $container_id}) "
        "RETURN c.exposed_internet AS exposed, c.exposed_internet_type AS exposure_types",
        container_id=case["cont_lb_id"],
    )
    record = result.single()
    assert record["exposed"] is None
    assert record["exposure_types"] is None

    result = neo4j_session.run(
        "MATCH (lb:AWSLoadBalancerV2{id: $lb_id})-[:EXPOSE]->(pod:KubernetesPod{id: $pod_id}) "
        "RETURN count(*) AS rel_count",
        lb_id=case["nlb_dns"],
        pod_id=case["pod_lb_id"],
    )
    assert result.single()["rel_count"] == 0


@pytest.mark.parametrize(
    ("address_kind", "programmed", "accepted", "expected_exposed"),
    [
        ("ip", True, True, True),
        ("dns", True, True, True),
        ("ip", False, True, False),
        ("ip", True, False, False),
    ],
)
def test_gateway_status_propagates_only_current_accepted_exposure(
    neo4j_session,
    address_kind,
    programmed,
    accepted,
    expected_exposed,
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    case = build_exposure_test_data()
    _seed_exposure_graph(
        neo4j_session,
        case=case,
        include_ingress=False,
        mark_alb_exposed=False,
    )
    namespace = "default"
    gateway_name = "public-gateway"
    gateway_qualified_name = f"{namespace}/{gateway_name}"
    route_qualified_name = f"{namespace}/frontend-route"
    load_balancer_address = "8.8.8.8" if address_kind == "ip" else "gateway.example.net"

    if address_kind == "ip":
        neo4j_session.run(
            """
            MERGE (lb:GCPForwardingRule:LoadBalancer {id: $address})
            SET lb._ont_ip_address = $address,
                lb._ont_source = 'gcp',
                lb.exposed_internet = true
            """,
            address=load_balancer_address,
        )
    else:
        neo4j_session.run(
            """
            MERGE (lb:AzureLoadBalancer:LoadBalancer {id: $address})
            SET lb._ont_dns_name = $address,
                lb._ont_source = 'azure',
                lb.exposed_internet = true
            """,
            address=load_balancer_address,
        )
    load_http_routes(
        neo4j_session,
        [
            {
                "uid": "route-uid",
                "name": "frontend-route",
                "namespace": namespace,
                "qualified_name": route_qualified_name,
                "hostnames": ["app.example.com"],
                "backend_service_qualified_names": [
                    f"{namespace}/{case['services'][1]['name']}"
                ],
                "parent_gateway_qualified_names": [gateway_qualified_name],
                "accepted_parent_gateway_qualified_names": (
                    [gateway_qualified_name] if accepted else []
                ),
            }
        ],
        update_tag=case["update_tag"],
        cluster_id=case["cluster_id"],
        cluster_name=case["cluster_name"],
    )
    load_gateways(
        neo4j_session,
        [
            {
                "uid": "gateway-uid",
                "name": gateway_name,
                "namespace": namespace,
                "qualified_name": gateway_qualified_name,
                "gateway_class_name": "example",
                "programmed": programmed,
                "load_balancer_ip_addresses": (
                    [load_balancer_address] if address_kind == "ip" else []
                ),
                "load_balancer_dns_names": (
                    [load_balancer_address] if address_kind == "dns" else []
                ),
                "attached_route_qualified_names": [route_qualified_name],
            }
        ],
        update_tag=case["update_tag"],
        cluster_id=case["cluster_id"],
        cluster_name=case["cluster_name"],
    )

    assert check_rels(
        neo4j_session,
        "KubernetesGateway",
        "id",
        "LoadBalancer",
        "id",
        "USES_LOAD_BALANCER",
        rel_direction_right=True,
    ) == {("gateway-uid", load_balancer_address)}
    assert check_rels(
        neo4j_session,
        "KubernetesGateway",
        "id",
        "KubernetesHTTPRoute",
        "id",
        "ROUTES",
        rel_direction_right=True,
    ) == {("gateway-uid", "route-uid")}
    assert check_rels(
        neo4j_session,
        "KubernetesHTTPRoute",
        "id",
        "KubernetesService",
        "id",
        "TARGETS",
        rel_direction_right=True,
    ) == {("route-uid", case["svc_ing_id"])}

    common_job_parameters = {
        "UPDATE_TAG": case["update_tag"],
        "CLUSTER_ID": case["cluster_id"],
    }
    _run_k8s_compute_analysis(neo4j_session, common_job_parameters)
    _run_k8s_lb_analysis(neo4j_session, common_job_parameters)

    result = neo4j_session.run(
        """
        MATCH (lb:LoadBalancer {id: $address})
        MATCH (pod:KubernetesPod {id: $pod_id})
        MATCH (container:KubernetesContainer {id: $container_id})
        OPTIONAL MATCH (lb)-[pod_exposure:EXPOSE]->(pod)
        OPTIONAL MATCH (lb)-[container_exposure:EXPOSE]->(container)
        RETURN pod.exposed_internet AS pod_exposed,
               container.exposed_internet AS container_exposed,
               pod_exposure IS NOT NULL AS pod_relationship,
               container_exposure IS NOT NULL AS container_relationship
        """,
        address=load_balancer_address,
        pod_id=case["pod_ing_id"],
        container_id=case["cont_ing_id"],
    ).single()
    expected_property = True if expected_exposed else None
    assert result["pod_exposed"] is expected_property
    assert result["container_exposed"] is expected_property
    assert result["pod_relationship"] is expected_exposed
    assert result["container_relationship"] is expected_exposed
