from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.guardduty_active_threat import (
    aws_guardduty_active_threat,
)


def test_guardduty_active_threat_includes_runtime_and_attack_sequence_findings(
    neo4j_session,
) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (a:AWSAccount {id: '111111111111', name: 'prod'})
        WITH a
        UNWIND [
            {id: 'reverse-shell', type: 'Execution:Runtime/ReverseShell', severity: 8.0},
            {id: 'attack-sequence', type: 'AttackSequence:EKS/CompromisedCluster', severity: 9.0},
            {id: 'priv-esc', type: 'PrivilegeEscalation:Runtime/ContainerMountsHostDirectory', severity: 7.0},
            {id: 'persistence', type: 'Persistence:IAMUser/AnomalousBehavior', severity: 8.0},
            {id: 'credential-access', type: 'CredentialAccess:IAMUser/AnomalousBehavior', severity: 8.0},
            {id: 'defense-evasion', type: 'DefenseEvasion:Runtime/ProcessInjection.Proc', severity: 8.0},
            {id: 'impact', type: 'Impact:IAMUser/AnomalousBehavior', severity: 8.0},
            {id: 'low-severity-execution', type: 'Execution:Runtime/SuspiciousCommand', severity: 2.0},
            {id: 'discovery', type: 'Discovery:IAMUser/AnomalousBehavior', severity: 8.0},
            {id: 'policy', type: 'Policy:IAMUser/RootCredentialUsage', severity: 8.0}
        ] AS f
        CREATE (finding:AWSGuardDutyFinding {
            id: f.id,
            type: f.type,
            severity: f.severity,
            accountid: '111111111111',
            archived: false
        })
        MERGE (a)-[:RESOURCE]->(finding)
        """
    )

    findings = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        aws_guardduty_active_threat.cypher_query,
    )
    visual_rows = list(
        neo4j_session.run(aws_guardduty_active_threat.cypher_visual_query)
    )

    assert {row["finding_id"] for row in findings} == {
        "reverse-shell",
        "attack-sequence",
        "priv-esc",
        "persistence",
        "credential-access",
        "defense-evasion",
        "impact",
    }
    assert len(visual_rows) == 7
