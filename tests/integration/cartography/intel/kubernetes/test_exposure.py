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
from tests.data.kubernetes.exposure import build_exposure_test_data
from tests.integration.cartography.intel.aws.common import create_test_account


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


def test_k8s_lb_expose_via_service(neo4j_session):
    case = build_exposure_test_data()
    _seed_exposure_graph(neo4j_session, case=case)

    common_job_parameters = {
        "UPDATE_TAG": case["update_tag"],
        "CLUSTER_ID": case["cluster_id"],
    }

    run_scoped_analysis_job(
        "k8s_compute_asset_exposure.json", neo4j_session, common_job_parameters
    )
    run_scoped_analysis_job(
        "k8s_lb_exposure.json", neo4j_session, common_job_parameters
    )

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

    run_scoped_analysis_job(
        "k8s_compute_asset_exposure.json", neo4j_session, common_job_parameters
    )

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

    run_scoped_analysis_job(
        "k8s_compute_asset_exposure.json", neo4j_session, common_job_parameters
    )

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

    run_scoped_analysis_job(
        "k8s_compute_asset_exposure.json", neo4j_session, common_job_parameters
    )
    run_scoped_analysis_job(
        "k8s_lb_exposure.json", neo4j_session, common_job_parameters
    )

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
