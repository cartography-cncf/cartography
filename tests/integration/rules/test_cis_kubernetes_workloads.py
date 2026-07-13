from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_secrets_used_as_environment_variables,
)


def _reset_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _get_fact(fact_id: str):
    return next(
        fact
        for fact in kubernetes_secrets_used_as_environment_variables.facts
        if fact.id == fact_id
    )


def test_secrets_in_env_fact_matches_env_and_dual_use_mount_methods(
    neo4j_session,
) -> None:
    """The canonical USES_SECRET edge carries the injection method on
    `mount_method`. A secret used both as a volume and via env has
    `mount_method = "volume,env"`, so the fact must match membership of `env`
    rather than an exact `= "env"`, otherwise dual-use pods slip through. A
    volume-only pod must NOT be flagged.
    """
    _reset_graph(neo4j_session)
    neo4j_session.run(
        """
        CREATE (c:KubernetesCluster {id: 'cluster-1', name: 'cluster-1'})
        CREATE (env_pod:KubernetesPod {id: 'pod-env', name: 'pod-env', namespace: 'default'})
        CREATE (both_pod:KubernetesPod {id: 'pod-both', name: 'pod-both', namespace: 'default'})
        CREATE (vol_pod:KubernetesPod {id: 'pod-vol', name: 'pod-vol', namespace: 'default'})
        CREATE (s_env:KubernetesSecret {id: 'cluster-1/default/s-env', name: 's-env'})
        CREATE (s_both:KubernetesSecret {id: 'cluster-1/default/s-both', name: 's-both'})
        CREATE (s_vol:KubernetesSecret {id: 'cluster-1/default/s-vol', name: 's-vol'})
        MERGE (c)-[:RESOURCE]->(env_pod)
        MERGE (c)-[:RESOURCE]->(both_pod)
        MERGE (c)-[:RESOURCE]->(vol_pod)
        MERGE (env_pod)-[:USES_SECRET {mount_method: 'env'}]->(s_env)
        MERGE (both_pod)-[:USES_SECRET {mount_method: 'volume,env'}]->(s_both)
        MERGE (vol_pod)-[:USES_SECRET {mount_method: 'volume'}]->(s_vol)
        """
    )

    findings = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        _get_fact("k8s_secrets_in_env_vars").cypher_query,
    )

    # Findings are grouped per (cluster, namespace): all three pods live in the
    # `default` namespace, so the env and dual-use pods collapse into a single
    # row, while the volume-only pod is excluded entirely.
    assert len(findings) == 1
    row = findings[0]
    assert row["cluster_name"] == "cluster-1"
    assert row["namespace"] == "default"
    assert sorted(row["pod_names"]) == ["pod-both", "pod-env"]
    assert sorted(row["secret_names"]) == ["s-both", "s-env"]
