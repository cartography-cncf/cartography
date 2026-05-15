from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.eol_software import (
    _build_ec2_instance_amazon_linux_2_eol_query,
)
from cartography.rules.data.rules.eol_software import eol_software


def _reset_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _get_fact(fact_id: str):
    return next(fact for fact in eol_software.facts if fact.id == fact_id)


def test_eks_fact_returns_provider_lifecycle_finding(neo4j_session) -> None:
    _reset_graph(neo4j_session)
    neo4j_session.run(
        """
        CREATE (:EKSCluster {
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
            "asset_type": "EKSCluster",
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
        CREATE (cluster:EKSCluster {
            id: 'arn:aws:eks:us-east-1:123456789012:cluster/eks-1',
            arn: 'arn:aws:eks:us-east-1:123456789012:cluster/eks-1',
            name: 'eks-1',
            version: '1.28',
            region: 'us-east-1'
        })
        CREATE (worker:EC2Instance {
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
        CREATE (:EKSCluster {
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


def test_ec2_fact_flags_amazon_linux_2_after_eol(neo4j_session) -> None:
    _reset_graph(neo4j_session)
    neo4j_session.run(
        """
        CREATE (al2:EC2Instance {
            id: 'i-al2',
            instanceid: 'i-al2',
            region: 'us-east-1'
        })
        CREATE (al2023:EC2Instance {
            id: 'i-al2023',
            instanceid: 'i-al2023',
            region: 'us-east-1'
        })
        CREATE (al2_ssm:SSMInstanceInformation {
            id: 'i-al2',
            platform_name: 'Amazon Linux',
            platform_version: '2',
            region: 'us-east-1'
        })
        CREATE (al2023_ssm:SSMInstanceInformation {
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
            "asset_type": "EC2Instance",
            "software_name": "amazon-linux",
            "software_version": "2",
            "software_major": 2,
            "software_minor": None,
            "location": "us-east-1",
            "support_basis": "vendor",
            "support_status": "eol",
        }
    ]
