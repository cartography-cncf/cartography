from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.github_actions_privileged_pull_request import (
    github_actions_privileged_pull_request,
)
from cartography.rules.data.rules.internet_exposed_database_without_backups import (
    internet_exposed_database_without_backups,
)
from cartography.rules.data.rules.privileged_kubernetes_workload_cloud_identity import (
    privileged_kubernetes_workload_cloud_identity,
)
from cartography.rules.data.rules.public_database_snapshot import (
    public_database_snapshot,
)
from cartography.rules.data.rules.public_object_storage_without_recovery import (
    public_object_storage_without_recovery,
)
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module

NEW_CSPM_RULES = [
    public_database_snapshot,
    public_object_storage_without_recovery,
    internet_exposed_database_without_backups,
    privileged_kubernetes_workload_cloud_identity,
    github_actions_privileged_pull_request,
]


def test_new_cspm_rules_are_registered() -> None:
    for rule in NEW_CSPM_RULES:
        assert RULES[rule.id] is rule


def test_new_cspm_rules_are_experimental() -> None:
    for rule in NEW_CSPM_RULES:
        assert all(fact.maturity == Maturity.EXPERIMENTAL for fact in rule.facts)


def test_public_database_snapshot_shape() -> None:
    assert public_database_snapshot.id == "public_database_snapshot"
    assert {fact.module for fact in public_database_snapshot.facts} == {Module.AWS}
    assert public_database_snapshot.facts[0].asset_id_field == "snapshot_id"
    assert "RDSSnapshot" in public_database_snapshot.facts[0].cypher_query
    assert "ispublic" in public_database_snapshot.facts[0].cypher_query


def test_public_object_storage_without_recovery_modules() -> None:
    assert public_object_storage_without_recovery.id == (
        "public_object_storage_without_recovery"
    )
    assert {fact.module for fact in public_object_storage_without_recovery.facts} == {
        Module.AWS,
        Module.AZURE,
        Module.GCP,
    }
    for fact in public_object_storage_without_recovery.facts:
        assert fact.asset_id_field == "id"


def test_internet_exposed_database_without_backups_modules() -> None:
    assert internet_exposed_database_without_backups.id == (
        "internet_exposed_database_without_backups"
    )
    assert {
        fact.module for fact in internet_exposed_database_without_backups.facts
    } == {
        Module.AWS,
        Module.GCP,
    }
    assert all(
        fact.asset_id_field == "id"
        for fact in internet_exposed_database_without_backups.facts
    )


def test_privileged_kubernetes_workload_cloud_identity_shape() -> None:
    assert privileged_kubernetes_workload_cloud_identity.id == (
        "privileged_kubernetes_workload_cloud_identity"
    )
    assert {
        fact.module for fact in privileged_kubernetes_workload_cloud_identity.facts
    } == {Module.KUBERNETES}
    query_text = "\n".join(
        fact.cypher_query
        for fact in privileged_kubernetes_workload_cloud_identity.facts
    )
    assert "ASSUMES_ROLE" in query_text
    assert "WORKLOAD_IDENTITY_BINDING" in query_text
    assert "allow_privilege_escalation" in query_text
    assert "kube-system" in query_text


def test_github_actions_privileged_pull_request_shape() -> None:
    fact = github_actions_privileged_pull_request.facts[0]

    assert github_actions_privileged_pull_request.id == (
        "github_actions_privileged_pull_request"
    )
    assert {fact.module for fact in github_actions_privileged_pull_request.facts} == {
        Module.GITHUB
    }
    assert fact.asset_id_field == "workflow_id"
    assert "pull_request_target" in fact.cypher_query
    assert "permissions_contents = 'write'" in fact.cypher_query
    assert "coalesce(repo.private, false) = false" in fact.cypher_query
