from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.guardduty_active_threat import (
    aws_guardduty_active_threat,
)


def _flagged_finding_ids(neo4j_session, findings: list[dict]) -> set[str]:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (a:AWSAccount {id: '111111111111', name: 'prod'})
        WITH a
        UNWIND $findings AS f
        CREATE (finding:AWSGuardDutyFinding {
            id: f.id,
            type: f.type,
            severity: f.severity,
            accountid: '111111111111',
            archived: false
        })
        MERGE (a)-[:RESOURCE]->(finding)
        """,
        findings=findings,
    )
    rows = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        aws_guardduty_active_threat.cypher_query,
    )
    return {row["finding_id"] for row in rows}


def test_runtime_reverse_shell_is_an_active_threat(neo4j_session) -> None:
    assert _flagged_finding_ids(
        neo4j_session,
        [
            {
                "id": "reverse-shell",
                "type": "Execution:Runtime/ReverseShell",
                "severity": 8.0,
            },
        ],
    ) == {"reverse-shell"}


def test_attack_sequence_is_an_active_threat(neo4j_session) -> None:
    assert _flagged_finding_ids(
        neo4j_session,
        [
            {
                "id": "attack-sequence",
                "type": "AttackSequence:EKS/CompromisedCluster",
                "severity": 9.0,
            },
        ],
    ) == {"attack-sequence"}


def test_low_severity_runtime_finding_is_not_an_active_threat(neo4j_session) -> None:
    assert (
        _flagged_finding_ids(
            neo4j_session,
            [
                {
                    "id": "suspicious-command",
                    "type": "Execution:Runtime/SuspiciousCommand",
                    "severity": 2.0,
                },
            ],
        )
        == set()
    )


def test_high_severity_discovery_and_policy_findings_are_not_active_threats(
    neo4j_session,
) -> None:
    assert (
        _flagged_finding_ids(
            neo4j_session,
            [
                {
                    "id": "discovery",
                    "type": "Discovery:IAMUser/AnomalousBehavior",
                    "severity": 8.0,
                },
                {
                    "id": "policy",
                    "type": "Policy:IAMUser/RootCredentialUsage",
                    "severity": 8.0,
                },
            ],
        )
        == set()
    )
