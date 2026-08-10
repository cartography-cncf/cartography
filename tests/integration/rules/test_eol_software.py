from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.eol_software import (
    _build_ec2_instance_amazon_linux_2_eol_query,
)
from cartography.rules.data.rules.eol_software import (
    _build_kubernetes_ingress_nginx_eol_query,
)
from cartography.rules.data.rules.eol_software import eol_software


def _reset_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _get_fact(fact_id: str):
    return next(fact for fact in eol_software.facts if fact.id == fact_id)


def _seed_ingress_nginx_controller_graph(neo4j_session) -> None:
    result = neo4j_session.run(
        """
        CREATE (cluster:KubernetesCluster {
            id: 'cluster-1',
            name: 'cluster-1'
        })
        CREATE (pod_1:KubernetesPod {
            id: 'pod-controller-1',
            name: 'ingress-nginx-controller-abcde',
            namespace: 'ingress-nginx',
            cluster_name: 'cluster-1',
            labels: '{"app.kubernetes.io/name":"ingress-nginx","app.kubernetes.io/component":"controller","app.kubernetes.io/instance":"ingress-nginx","app.kubernetes.io/version":"1.12.0","helm.sh/chart":"ingress-nginx-4.12.0"}'
        })
        CREATE (pod_2:KubernetesPod {
            id: 'pod-controller-2',
            name: 'ingress-nginx-controller-fghij',
            namespace: 'ingress-nginx',
            cluster_name: 'cluster-1',
            labels: '{"app.kubernetes.io/name":"ingress-nginx","app.kubernetes.io/component":"controller","app.kubernetes.io/instance":"ingress-nginx","app.kubernetes.io/version":"1.12.0","helm.sh/chart":"ingress-nginx-4.12.0"}'
        })
        CREATE (container_1:KubernetesContainer {
            id: 'container-controller-1',
            name: 'controller',
            namespace: 'ingress-nginx',
            cluster_name: 'cluster-1',
            image: 'registry.k8s.io/ingress-nginx/controller:v1.12.0@sha256:abc'
        })
        CREATE (container_2:KubernetesContainer {
            id: 'container-controller-2',
            name: 'controller',
            namespace: 'ingress-nginx',
            cluster_name: 'cluster-1',
            image: 'registry.k8s.io/ingress-nginx/controller:v1.12.0@sha256:def'
        })
        CREATE (cluster)-[:RESOURCE]->(pod_1)
        CREATE (cluster)-[:RESOURCE]->(pod_2)
        CREATE (container_1)-[:WORKLOAD_PARENT]->(pod_1)
        CREATE (pod_1)-[:CONTAINS]->(container_1)
        CREATE (pod_2)-[:CONTAINS]->(container_2)
        """
    )
    result.consume()


def test_eks_fact_returns_provider_lifecycle_finding(neo4j_session) -> None:
    _reset_graph(neo4j_session)
    neo4j_session.run(
        """
        CREATE (:AWSEKSCluster {
            id: 'eks-1',
            name: 'eks-1',
            version: '1.28',
            region: 'us-east-1'
        })
        """
    )

    findings = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        _get_fact("eks_cluster_kubernetes_version_eol").cypher_query,
    )

    assert findings == [
        {
            "asset_id": "eks-1",
            "asset_name": "eks-1",
            "asset_type": "AWSEKSCluster",
            "software_name": "kubernetes",
            "software_version": "1.28",
            "software_major": 1,
            "software_minor": 28,
            "location": "us-east-1",
            "support_basis": "provider",
            "support_status": "eol",
        }
    ]


def test_eks_visual_query_returns_account_and_worker_context(neo4j_session) -> None:
    _reset_graph(neo4j_session)
    result = neo4j_session.run(
        """
        CREATE (account:AWSAccount {id: '123456789012', name: 'prod'})
        CREATE (cluster:AWSEKSCluster {
            id: 'arn:aws:eks:us-east-1:123456789012:cluster/eks-1',
            arn: 'arn:aws:eks:us-east-1:123456789012:cluster/eks-1',
            name: 'eks-1',
            version: '1.28',
            region: 'us-east-1'
        })
        CREATE (worker:AWSEC2Instance {
            id: 'i-eks-worker',
            instanceid: 'i-eks-worker'
        })
        CREATE (account)-[:RESOURCE]->(cluster)
        CREATE (worker)-[:MEMBER_OF_EKS_CLUSTER]->(cluster)
        """
    )
    result.consume()

    record = neo4j_session.run(
        _get_fact("eks_cluster_kubernetes_version_eol").cypher_visual_query,
    ).single()

    assert record is not None
    assert record["cluster"]["name"] == "eks-1"
    assert record["account_path"] is not None
    assert record["worker_path"] is not None


def test_kubernetes_fact_dedupes_eks_overlap(neo4j_session) -> None:
    _reset_graph(neo4j_session)
    neo4j_session.run(
        """
        CREATE (:AWSEKSCluster {
            id: 'shared-cluster',
            name: 'shared-cluster',
            endpoint: 'https://shared.example'
        })
        CREATE (:KubernetesCluster {
            id: 'kube-deduped',
            name: 'kube-deduped',
            version: '1.32.0',
            version_minor: 32,
            external_id: 'shared-cluster',
            api_server_url: 'https://shared.example'
        })
        CREATE (:KubernetesCluster {
            id: 'kube-unmanaged',
            name: 'kube-unmanaged',
            version: '1.32.0',
            version_minor: 32
        })
        """
    )

    findings = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        _get_fact("kubernetes_cluster_kubernetes_version_eol").cypher_query,
    )

    assert findings == [
        {
            "asset_id": "kube-unmanaged",
            "asset_name": "kube-unmanaged",
            "asset_type": "KubernetesCluster",
            "software_name": "kubernetes",
            "software_version": "1.32.0",
            "software_major": 1,
            "software_minor": 32,
            "location": None,
            "support_basis": "upstream",
            "support_status": "eol",
        }
    ]


def test_kubernetes_visual_query_returns_workload_context(neo4j_session) -> None:
    _reset_graph(neo4j_session)
    result = neo4j_session.run(
        """
        CREATE (cluster:KubernetesCluster {
            id: 'kube-1',
            name: 'kube-1',
            version: '1.32.0',
            version_minor: 32
        })
        CREATE (service:KubernetesService {
            id: 'svc-1',
            name: 'frontend',
            namespace: 'default',
            cluster_name: 'kube-1'
        })
        CREATE (pod:KubernetesPod {
            id: 'pod-1',
            name: 'frontend-abc',
            namespace: 'default',
            cluster_name: 'kube-1'
        })
        CREATE (cluster)-[:RESOURCE]->(service)
        CREATE (service)-[:TARGETS]->(pod)
        """
    )
    result.consume()

    record = neo4j_session.run(
        _get_fact("kubernetes_cluster_kubernetes_version_eol").cypher_visual_query,
    ).single()

    assert record is not None
    assert record["cluster"]["name"] == "kube-1"
    assert record["workload_path"] is not None
    assert record["resource_path"] is not None


def test_ingress_nginx_fact_collapses_controller_replicas(neo4j_session) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    _seed_ingress_nginx_controller_graph(neo4j_session)

    # Act
    findings = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        _build_kubernetes_ingress_nginx_eol_query(),
    )

    # Assert
    assert findings == [
        {
            "cluster_id": "cluster-1",
            "asset_id": "cluster-1/namespaces/ingress-nginx/ingress-controllers/ingress-nginx/1.12.0",
            "asset_name": "cluster-1/ingress-nginx/ingress-nginx",
            "asset_type": "KubernetesIngressController",
            "software_name": "ingress-nginx",
            "software_version": "1.12.0",
            "software_major": 1,
            "software_minor": 12,
            "location": None,
            "support_basis": "upstream",
            "support_status": "eol",
        }
    ]


def test_ingress_nginx_fact_ignores_non_controller_images(neo4j_session) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    result = neo4j_session.run(
        """
        CREATE (cluster:KubernetesCluster {
            id: 'cluster-1',
            name: 'cluster-1'
        })
        CREATE (admission_pod:KubernetesPod {
            id: 'pod-admission',
            name: 'ingress-nginx-admission-create',
            namespace: 'ingress-nginx',
            cluster_name: 'cluster-1',
            labels: '{"app.kubernetes.io/name":"ingress-nginx","app.kubernetes.io/component":"admission-webhook","app.kubernetes.io/instance":"ingress-nginx"}'
        })
        CREATE (nginx_pod:KubernetesPod {
            id: 'pod-nginx',
            name: 'nginx',
            namespace: 'default',
            cluster_name: 'cluster-1',
            labels: '{"app.kubernetes.io/name":"nginx","app.kubernetes.io/component":"server"}'
        })
        CREATE (admission_container:KubernetesContainer {
            id: 'container-admission',
            name: 'create',
            namespace: 'ingress-nginx',
            cluster_name: 'cluster-1',
            image: 'registry.k8s.io/ingress-nginx/kube-webhook-certgen:v1.5.2'
        })
        CREATE (nginx_container:KubernetesContainer {
            id: 'container-nginx',
            name: 'nginx',
            namespace: 'default',
            cluster_name: 'cluster-1',
            image: 'docker.io/library/nginx:1.25'
        })
        CREATE (cluster)-[:RESOURCE]->(admission_pod)
        CREATE (cluster)-[:RESOURCE]->(nginx_pod)
        CREATE (admission_container)-[:WORKLOAD_PARENT]->(admission_pod)
        CREATE (nginx_container)-[:WORKLOAD_PARENT]->(nginx_pod)
        """
    )
    result.consume()

    # Act
    findings = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        _build_kubernetes_ingress_nginx_eol_query(),
    )

    # Assert
    assert findings == []


def test_ingress_nginx_visual_query_returns_controller_context(
    neo4j_session,
) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    _seed_ingress_nginx_controller_graph(neo4j_session)

    # Act
    records = list(
        neo4j_session.run(
            _get_fact("kubernetes_ingress_nginx_controller_eol").cypher_visual_query,
        )
    )

    # Assert
    assert records
    assert len(records) == 2
    record = records[0]
    assert record["cluster"]["name"] == "cluster-1"
    assert record["pod"]["namespace"] == "ingress-nginx"
    assert record["container"]["image"].startswith(
        "registry.k8s.io/ingress-nginx/controller:v1.12.0",
    )
    assert record["resource_path"] is not None
    assert record["controller_path"] is not None


def test_ec2_fact_flags_amazon_linux_2_after_eol(neo4j_session) -> None:
    _reset_graph(neo4j_session)
    neo4j_session.run(
        """
        CREATE (al2:AWSEC2Instance {
            id: 'i-al2',
            instanceid: 'i-al2',
            region: 'us-east-1'
        })
        CREATE (al2023:AWSEC2Instance {
            id: 'i-al2023',
            instanceid: 'i-al2023',
            region: 'us-east-1'
        })
        CREATE (al2_ssm:AWSSSMInstanceInformation {
            id: 'i-al2',
            platform_name: 'Amazon Linux',
            platform_version: '2',
            region: 'us-east-1'
        })
        CREATE (al2023_ssm:AWSSSMInstanceInformation {
            id: 'i-al2023',
            platform_name: 'Amazon Linux',
            platform_version: '2023',
            region: 'us-east-1'
        })
        CREATE (al2)-[:HAS_INFORMATION]->(al2_ssm)
        CREATE (al2023)-[:HAS_INFORMATION]->(al2023_ssm)
        """
    )

    findings = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        _build_ec2_instance_amazon_linux_2_eol_query("date('2026-07-01')"),
    )

    assert findings == [
        {
            "asset_id": "i-al2",
            "asset_name": "i-al2",
            "asset_type": "AWSEC2Instance",
            "software_name": "amazon-linux",
            "software_version": "2",
            "software_major": 2,
            "software_minor": None,
            "location": "us-east-1",
            "support_basis": "vendor",
            "support_status": "eol",
        }
    ]
