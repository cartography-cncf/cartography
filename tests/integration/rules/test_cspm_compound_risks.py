from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.github_actions_privileged_pull_request import (
    github_actions_privileged_pull_request,
)
from cartography.rules.data.rules.internet_exposed_database_without_backups import (
    internet_exposed_database_without_backups,
)
from cartography.rules.data.rules.privileged_kubernetes_workload_cloud_identity import (
    privileged_kubernetes_workload_cloud_identity,
)
from cartography.rules.data.rules.public_object_storage_without_recovery import (
    public_object_storage_without_recovery,
)
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Rule


def _reset_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _get_fact(rule: Rule, fact_id: str) -> Fact:
    return next(fact for fact in rule.facts if fact.id == fact_id)


def _run_query(neo4j_session, fact: Fact) -> list[dict]:
    return neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_query)


def _run_count_query(neo4j_session, fact: Fact) -> int:
    rows = neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_count_query)
    return rows[0]["count"]


def test_public_s3_without_versioning_matches_json_serialized_public_principal(
    neo4j_session,
) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    fact = _get_fact(
        public_object_storage_without_recovery,
        "aws_public_s3_without_versioning",
    )
    neo4j_session.run(
        """
        CREATE (account:AWSAccount {id: 'aws-account-1', name: 'test-account'})
        CREATE (public_bucket:S3Bucket {
            id: 'bucket-public-policy',
            name: 'bucket-public-policy',
            versioning_status: 'Suspended',
            anonymous_access: false,
            region: 'us-east-1'
        })
        CREATE (versioned_bucket:S3Bucket {
            id: 'bucket-versioned',
            name: 'bucket-versioned',
            versioning_status: 'Enabled',
            anonymous_access: true,
            region: 'us-east-1'
        })
        CREATE (stmt:S3PolicyStatement {
            id: 'bucket-public-policy/policy_statement/1/public',
            effect: 'Allow',
            principal: '"*"'
        })
        CREATE (account)-[:RESOURCE]->(public_bucket)
        CREATE (account)-[:RESOURCE]->(versioned_bucket)
        CREATE (public_bucket)-[:POLICY_STATEMENT]->(stmt)
        """
    )

    # Act
    findings = _run_query(neo4j_session, fact)

    # Assert
    assert findings == [
        {
            "id": "bucket-public-policy",
            "name": "bucket-public-policy",
            "account": "test-account",
            "account_id": "aws-account-1",
            "region": "us-east-1",
            "provider": "aws",
            "recovery_gap": "versioning_disabled",
            "recovery_status": "Suspended",
        }
    ]
    assert _run_count_query(neo4j_session, fact) == 2


def test_public_azure_blob_without_retention_keeps_account_fields_consistent(
    neo4j_session,
) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    fact = _get_fact(
        public_object_storage_without_recovery,
        "azure_public_blob_without_retention",
    )
    neo4j_session.run(
        """
        CREATE (subscription:AzureSubscription {id: 'sub-1'})
        CREATE (account:AzureStorageAccount {
            id: 'storage-account-1',
            name: 'storage-account-1',
            location: 'eastus'
        })
        CREATE (service:AzureStorageBlobService {id: 'blob-service-1'})
        CREATE (container:AzureStorageBlobContainer {
            id: 'container-1',
            name: 'container-1',
            public_access: 'Container',
            remaining_retention_days: 0,
            has_immutability_policy: false,
            has_legal_hold: false
        })
        CREATE (subscription)-[:RESOURCE]->(container)
        CREATE (subscription)-[:RESOURCE]->(account)
        CREATE (account)-[:USES]->(service)
        CREATE (service)-[:CONTAINS]->(container)
        """
    )

    # Act
    findings = _run_query(neo4j_session, fact)

    # Assert
    assert findings == [
        {
            "id": "container-1",
            "name": "container-1",
            "account": "sub-1",
            "account_id": "sub-1",
            "region": "eastus",
            "storage_account": "storage-account-1",
            "provider": "azure",
            "recovery_gap": "no_retention_or_immutability",
            "recovery_status": "0",
        }
    ]
    assert _run_count_query(neo4j_session, fact) == 1


def test_internet_exposed_rds_without_backups_requires_backup_disabled(
    neo4j_session,
) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    fact = _get_fact(
        internet_exposed_database_without_backups,
        "aws_public_rds_without_backups",
    )
    neo4j_session.run(
        """
        CREATE (account:AWSAccount {id: 'aws-account-1', name: 'test-account'})
        CREATE (rds_without_backups:RDSInstance {
            id: 'rds-no-backups',
            db_instance_identifier: 'rds-no-backups',
            publicly_accessible: true,
            endpoint_port: 5432,
            endpoint_address: 'rds-no-backups.example.test',
            backup_retention_period: 0,
            deletion_protection: false,
            engine: 'postgres',
            region: 'us-east-1'
        })
        CREATE (rds_with_backups:RDSInstance {
            id: 'rds-with-backups',
            db_instance_identifier: 'rds-with-backups',
            publicly_accessible: true,
            endpoint_port: 5432,
            endpoint_address: 'rds-with-backups.example.test',
            backup_retention_period: 7,
            deletion_protection: true,
            engine: 'postgres',
            region: 'us-east-1'
        })
        CREATE (sg:EC2SecurityGroup {id: 'sg-public'})
        CREATE (rule:AWSIpPermissionInbound {
            id: 'rule-public-postgres',
            protocol: 'tcp',
            fromport: 5432,
            toport: 5432
        })
        CREATE (range:AWSIpRange {id: '0.0.0.0/0', range: '0.0.0.0/0'})
        CREATE (account)-[:RESOURCE]->(rds_without_backups)
        CREATE (account)-[:RESOURCE]->(rds_with_backups)
        CREATE (rds_without_backups)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg)
        CREATE (rds_with_backups)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg)
        CREATE (rule)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg)
        CREATE (range)-[:MEMBER_OF_IP_RULE]->(rule)
        """
    )

    # Act
    findings = _run_query(neo4j_session, fact)

    # Assert
    assert [finding["id"] for finding in findings] == ["rds-no-backups"]
    assert _run_count_query(neo4j_session, fact) == 2


def test_internet_exposed_cloudsql_without_backups_uses_null_retention(
    neo4j_session,
) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    fact = _get_fact(
        internet_exposed_database_without_backups,
        "gcp_public_cloudsql_without_backups",
    )
    neo4j_session.run(
        """
        CREATE (project:GCPProject {id: 'project-1'})
        CREATE (sql:GCPCloudSQLInstance {
            id: 'sql-1',
            name: 'sql-1',
            database_version: 'POSTGRES_15',
            connection_name: 'project-1:us-central1:sql-1',
            region: 'us-central1',
            backup_enabled: false
        })
        CREATE (network:GCPCloudSQLAuthorizedNetwork {
            id: 'network-1',
            value: '0.0.0.0/0'
        })
        CREATE (project)-[:RESOURCE]->(sql)
        CREATE (sql)-[:AUTHORIZED_NETWORK]->(network)
        """
    )

    # Act
    findings = _run_query(neo4j_session, fact)

    # Assert
    assert findings[0]["backup_retention_days"] is None
    assert _run_count_query(neo4j_session, fact) == 1


def test_privileged_kubernetes_workload_cloud_identity_ignores_system_namespace(
    neo4j_session,
) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    fact = _get_fact(
        privileged_kubernetes_workload_cloud_identity,
        "k8s_privileged_workloads_with_aws_identity",
    )
    neo4j_session.run(
        """
        CREATE (cluster:KubernetesCluster {id: 'cluster-1', name: 'cluster-1'})
        CREATE (role:AWSRole {
            id: 'role-1',
            arn: 'arn:aws:iam::aws-account-1:role/test-role'
        })
        CREATE (sa:KubernetesServiceAccount {
            id: 'sa-default',
            name: 'workload',
            namespace: 'default'
        })
        CREATE (system_sa:KubernetesServiceAccount {
            id: 'sa-system',
            name: 'system-workload',
            namespace: 'kube-system'
        })
        CREATE (pod:KubernetesPod {
            id: 'pod-default',
            name: 'pod-default',
            namespace: 'default',
            host_network: true
        })
        CREATE (system_pod:KubernetesPod {
            id: 'pod-system',
            name: 'pod-system',
            namespace: 'kube-system',
            host_network: true
        })
        CREATE (cluster)-[:RESOURCE]->(pod)
        CREATE (cluster)-[:RESOURCE]->(system_pod)
        CREATE (pod)-[:USES_SERVICE_ACCOUNT]->(sa)
        CREATE (system_pod)-[:USES_SERVICE_ACCOUNT]->(system_sa)
        CREATE (sa)-[:ASSUMES_ROLE]->(role)
        CREATE (system_sa)-[:ASSUMES_ROLE]->(role)
        """
    )

    # Act
    findings = _run_query(neo4j_session, fact)

    # Assert
    assert [finding["pod_id"] for finding in findings] == ["pod-default"]
    assert _run_count_query(neo4j_session, fact) == 1


def test_github_actions_pr_target_write_token_counts_public_workflows(
    neo4j_session,
) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    fact = _get_fact(
        github_actions_privileged_pull_request,
        "github_public_pull_request_target_write_token",
    )
    neo4j_session.run(
        """
        CREATE (repo:GitHubRepository {
            id: 'repo-public',
            fullname: 'org/repo-public',
            defaultbranch: 'main',
            private: false,
            archived: false
        })
        CREATE (private_repo:GitHubRepository {
            id: 'repo-private',
            fullname: 'org/repo-private',
            defaultbranch: 'main',
            private: true,
            archived: false
        })
        CREATE (pr_target:GitHubWorkflow {
            id: 'workflow-pr-target',
            name: 'pr-target',
            path: '.github/workflows/pr-target.yml',
            trigger_events: ['pull_request_target'],
            permissions_contents: 'write'
        })
        CREATE (push_workflow:GitHubWorkflow {
            id: 'workflow-push',
            name: 'push',
            path: '.github/workflows/push.yml',
            trigger_events: ['push'],
            permissions_contents: 'write'
        })
        CREATE (private_workflow:GitHubWorkflow {
            id: 'workflow-private',
            name: 'private',
            path: '.github/workflows/private.yml',
            trigger_events: ['pull_request_target'],
            permissions_contents: 'write'
        })
        CREATE (repo)-[:HAS_WORKFLOW]->(pr_target)
        CREATE (repo)-[:HAS_WORKFLOW]->(push_workflow)
        CREATE (private_repo)-[:HAS_WORKFLOW]->(private_workflow)
        """
    )

    # Act
    findings = _run_query(neo4j_session, fact)

    # Assert
    assert [finding["workflow_id"] for finding in findings] == ["workflow-pr-target"]
    assert _run_count_query(neo4j_session, fact) == 2
