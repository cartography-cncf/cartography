import copy
from unittest.mock import MagicMock

from kubernetes.client import V1Node
from kubernetes.client import V1NodeSpec
from kubernetes.client import V1ObjectMeta

import cartography.intel.azure.application_gateways as application_gateways
import cartography.intel.azure.load_balancers as load_balancers
import cartography.intel.azure.network as network
from cartography.analysis.aws.analysis import AWS_EC2_ASSET_EXPOSURE_JOBS
from cartography.analysis.azure.analysis import AZURE_COMPUTE_ASSET_EXPOSURE_LB
from cartography.analysis.kubernetes.analysis import K8S_AKS_LOAD_BALANCER
from cartography.analysis.kubernetes.analysis import K8S_COMPUTE_ASSET_EXPOSURE_JOBS
from cartography.analysis.kubernetes.analysis import K8S_LB_EXPOSURE_JOBS
from cartography.intel.aws.ec2.load_balancer_v2s import load_load_balancer_v2s
from cartography.intel.gcp.backendservice import load_gcp_backend_services
from cartography.intel.gcp.backendservice import transform_gcp_backend_services
from cartography.intel.gcp.network_endpoint_group import (
    load_gcp_network_endpoint_groups,
)
from cartography.intel.gcp.network_endpoint_group import (
    transform_gcp_network_endpoint_groups,
)
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.ingress import load_ingresses
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.nodes import load_nodes
from cartography.intel.kubernetes.nodes import transform_nodes
from cartography.intel.kubernetes.pods import load_containers
from cartography.intel.kubernetes.pods import load_pods
from cartography.intel.kubernetes.services import load_services
from cartography.intel.kubernetes.target_group_bindings import (
    sync_target_group_bindings,
)
from cartography.util import run_typed_analysis_job
from tests.data.kubernetes.exposure import build_aks_exposure_test_data
from tests.data.kubernetes.exposure import build_exposure_test_data
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
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
            "MATCH (lb:AWSLoadBalancerV2{id: $alb_id}) "
            "SET lb.exposed_internet = true",
            alb_id=case["alb_dns"],
        )

    load_services(
        neo4j_session,
        case["services"],
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


def _k8s_client_listing(cluster_name, items):
    client = MagicMock()
    client.name = cluster_name
    client.custom.list_cluster_custom_object.return_value = {
        "items": items,
        "metadata": {},
    }
    return client


def test_sync_target_group_bindings_links_target_group_to_service_in_same_cluster(
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    case = build_exposure_test_data()
    _seed_exposure_graph(neo4j_session, case=case, include_ingress=False)
    load_kubernetes_cluster(neo4j_session, case["other_cluster"], case["update_tag"])
    load_services(
        neo4j_session,
        case["other_cluster_services"],
        update_tag=case["update_tag"],
        cluster_id=case["other_cluster_id"],
        cluster_name=case["other_cluster_name"],
    )

    # Act
    sync_target_group_bindings(
        neo4j_session,
        _k8s_client_listing(case["cluster_name"], case["target_group_bindings"]),
        case["update_tag"],
        {"UPDATE_TAG": case["update_tag"], "CLUSTER_ID": case["cluster_id"]},
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSELBV2TargetGroup",
        "id",
        "KubernetesService",
        "id",
        "TARGETS",
    ) == {(case["alb_tg_arn"], case["svc_ing_id"])}
    result = neo4j_session.run(
        "MATCH (:AWSELBV2TargetGroup)-[r:TARGETS]->(:KubernetesService) "
        "RETURN r.binding_name AS binding_name, r.target_type AS target_type, "
        "r.service_port AS service_port",
    )
    assert [r.data() for r in result] == [
        {
            "binding_name": case["binding_name"],
            "target_type": "ip",
            "service_port": "80",
        },
    ]


def test_target_group_binding_on_exposed_alb_exposes_service_pods_and_containers(
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    case = build_exposure_test_data()
    _seed_exposure_graph(neo4j_session, case=case, include_ingress=False)
    common_job_parameters = {
        "UPDATE_TAG": case["update_tag"],
        "CLUSTER_ID": case["cluster_id"],
    }
    sync_target_group_bindings(
        neo4j_session,
        _k8s_client_listing(case["cluster_name"], case["target_group_bindings"]),
        case["update_tag"],
        common_job_parameters,
    )

    # Act
    _run_k8s_compute_analysis(neo4j_session, common_job_parameters)
    _run_k8s_lb_analysis(neo4j_session, common_job_parameters)

    # Assert
    assert check_nodes(
        neo4j_session, "KubernetesService", ["id", "exposed_internet"]
    ) == {(case["svc_lb_id"], True), (case["svc_ing_id"], True)}
    assert check_rels(
        neo4j_session,
        "AWSLoadBalancerV2",
        "id",
        "KubernetesPod",
        "id",
        "EXPOSE",
    ) == {
        (case["nlb_dns"], case["pod_lb_id"]),
        (case["alb_dns"], case["pod_ing_id"]),
    }
    assert check_rels(
        neo4j_session,
        "AWSLoadBalancerV2",
        "id",
        "KubernetesContainer",
        "id",
        "EXPOSE",
    ) == {
        (case["nlb_dns"], case["cont_lb_id"]),
        (case["alb_dns"], case["cont_ing_id"]),
    }


def test_target_group_binding_on_unexposed_alb_does_not_expose_service(
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    case = build_exposure_test_data()
    _seed_exposure_graph(
        neo4j_session, case=case, include_ingress=False, mark_alb_exposed=False
    )
    common_job_parameters = {
        "UPDATE_TAG": case["update_tag"],
        "CLUSTER_ID": case["cluster_id"],
    }
    sync_target_group_bindings(
        neo4j_session,
        _k8s_client_listing(case["cluster_name"], case["target_group_bindings"]),
        case["update_tag"],
        common_job_parameters,
    )

    # Act
    _run_k8s_compute_analysis(neo4j_session, common_job_parameters)
    _run_k8s_lb_analysis(neo4j_session, common_job_parameters)

    # Assert
    assert check_nodes(
        neo4j_session, "KubernetesService", ["id", "exposed_internet"]
    ) == {(case["svc_lb_id"], True), (case["svc_ing_id"], None)}
    assert check_rels(
        neo4j_session,
        "AWSLoadBalancerV2",
        "id",
        "KubernetesPod",
        "id",
        "EXPOSE",
    ) == {(case["nlb_dns"], case["pod_lb_id"])}


def test_target_group_binding_cleanup_removes_deleted_bindings(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    case = build_exposure_test_data()
    _seed_exposure_graph(neo4j_session, case=case, include_ingress=False)

    # Act
    sync_target_group_bindings(
        neo4j_session,
        _k8s_client_listing(case["cluster_name"], case["target_group_bindings"]),
        case["update_tag"],
        {"UPDATE_TAG": case["update_tag"], "CLUSTER_ID": case["cluster_id"]},
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSELBV2TargetGroup",
        "id",
        "KubernetesService",
        "id",
        "TARGETS",
    ) == {(case["alb_tg_arn"], case["svc_ing_id"])}

    # Act
    sync_target_group_bindings(
        neo4j_session,
        _k8s_client_listing(case["cluster_name"], []),
        case["update_tag"] + 1,
        {"UPDATE_TAG": case["update_tag"] + 1, "CLUSTER_ID": case["cluster_id"]},
    )

    # Assert
    assert (
        check_rels(
            neo4j_session,
            "AWSELBV2TargetGroup",
            "id",
            "KubernetesService",
            "id",
            "TARGETS",
        )
        == set()
    )


def test_k8s_lb_expose_via_gke_neg(neo4j_session):
    case = build_exposure_test_data()
    project_id = case["gcp_project_id"]
    neo4j_session.run("MERGE (:GCPProject {id: $id})", id=project_id)
    load_gcp_network_endpoint_groups(
        neo4j_session,
        transform_gcp_network_endpoint_groups(case["gcp_negs"], project_id),
        case["update_tag"],
        project_id,
    )
    load_gcp_backend_services(
        neo4j_session,
        transform_gcp_backend_services(case["gcp_backend_services"], project_id),
        case["update_tag"],
        project_id,
    )
    _seed_exposure_graph(neo4j_session, case=case, include_ingress=False)
    common_job_parameters = {
        "UPDATE_TAG": case["update_tag"],
        "CLUSTER_ID": case["cluster_id"],
    }

    _run_k8s_compute_analysis(neo4j_session, common_job_parameters)
    _run_k8s_lb_analysis(neo4j_session, common_job_parameters)

    result = neo4j_session.run(
        "MATCH (svc:KubernetesService{id: $svc}) RETURN svc.exposed_internet AS exposed",
        svc=case["svc_ing_id"],
    )
    assert result.single()["exposed"] is True
    # The internal backend service's NEG targets the other service; it exposes nothing.
    result = neo4j_session.run(
        "MATCH (bs:GCPBackendService{project_id: $project})-[:EXPOSE]->(n) "
        "WHERE n:KubernetesPod OR n:KubernetesContainer "
        "RETURN bs.id AS bs_id, n.id AS id",
        project=project_id,
    )
    assert {(r["bs_id"], r["id"]) for r in result} == {
        (case["ext_bs_id"], case["pod_ing_id"]),
        (case["ext_bs_id"], case["cont_ing_id"]),
    }


def test_k8s_asset_exposure_properties(neo4j_session):
    case = build_exposure_test_data()
    _seed_exposure_graph(neo4j_session, case=case)

    common_job_parameters = {
        "UPDATE_TAG": case["update_tag"],
        "CLUSTER_ID": case["cluster_id"],
    }

    _run_k8s_compute_analysis(neo4j_session, common_job_parameters)

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


def _seed_aks_azure_graph(neo4j_session, case: dict) -> None:
    tag = case["update_tag"]
    for sub in (case["subscription_id"], case["other_subscription_id"]):
        neo4j_session.run(
            "MERGE (s:AzureSubscription{id: $sub}) SET s.lastupdated = $tag",
            sub=sub,
            tag=tag,
        )
        network.load_public_ip_addresses(
            neo4j_session,
            network.transform_public_ip_addresses(case["public_ips"][sub]),
            sub,
            tag,
        )
        lbs = case["load_balancers"][sub]
        load_balancers.load_load_balancers(
            neo4j_session, load_balancers.transform_load_balancers(lbs), sub, tag
        )
        for lb in lbs:
            load_balancers.load_frontend_ips(
                neo4j_session,
                load_balancers.transform_frontend_ips(lb),
                lb["id"],
                sub,
                tag,
            )
    appgw = case["application_gateway"]
    application_gateways.load_application_gateways(
        neo4j_session,
        application_gateways.transform_application_gateways([appgw]),
        case["subscription_id"],
        tag,
    )
    application_gateways.load_frontend_ips(
        neo4j_session,
        application_gateways.transform_frontend_ips(appgw),
        appgw["id"],
        case["subscription_id"],
        tag,
    )
    load_nodes(
        neo4j_session,
        transform_nodes(
            [
                V1Node(
                    metadata=V1ObjectMeta(name="aks-nodepool1-vmss000000"),
                    spec=V1NodeSpec(provider_id=case["node_provider_id"]),
                ),
            ],
            case["cluster_name"],
        ),
        tag,
        case["cluster_id"],
        case["cluster_name"],
    )


def test_aks_load_balancers_link_and_propagate_exposure(neo4j_session):
    case = build_aks_exposure_test_data()
    _seed_exposure_graph(neo4j_session, case=case, mark_alb_exposed=False)
    _seed_aks_azure_graph(neo4j_session, case)
    common_job_parameters = {
        "UPDATE_TAG": case["update_tag"],
        "CLUSTER_ID": case["cluster_id"],
    }

    run_typed_analysis_job(
        AZURE_COMPUTE_ASSET_EXPOSURE_LB, neo4j_session, common_job_parameters
    )
    run_typed_analysis_job(K8S_AKS_LOAD_BALANCER, neo4j_session, common_job_parameters)
    _run_k8s_compute_analysis(neo4j_session, common_job_parameters)
    _run_k8s_lb_analysis(neo4j_session, common_job_parameters)

    # Decoys reuse the public address in another subscription and the private
    # address outside the node resource group; neither may link.
    result = neo4j_session.run(
        "MATCH (k:KubernetesCluster{id: $cluster_id})-[:RESOURCE]->(src)"
        "-[:USES_LOAD_BALANCER]->(lb) "
        "WHERE lb:AzureLoadBalancer OR lb:AzureApplicationGateway "
        "RETURN src.id AS src, lb.id AS lb",
        cluster_id=case["cluster_id"],
    )
    assert {(r["src"], r["lb"]) for r in result} == {
        (case["svc_lb_id"], case["public_lb_id"]),
        (case["svc_internal_id"], case["internal_lb_id"]),
        (case["ingress"]["uid"], case["appgw_id"]),
    }

    result = neo4j_session.run(
        "MATCH (lb:LoadBalancer)-[:EXPOSE]->(pod:KubernetesPod) "
        "WHERE pod.id IN $pods RETURN lb.id AS lb, pod.id AS pod",
        pods=[case["pod_lb_id"], case["pod_ing_id"]],
    )
    assert {(r["lb"], r["pod"]) for r in result} == {
        (case["public_lb_id"], case["pod_lb_id"]),
        (case["appgw_id"], case["pod_ing_id"]),
    }

    result = neo4j_session.run(
        "MATCH (svc:KubernetesService{id: $svc_id}) "
        "RETURN svc.exposed_internet AS exposed",
        svc_id=case["svc_internal_id"],
    )
    assert result.single()["exposed"] is None
