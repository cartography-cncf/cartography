from cartography.intel.sysdig import sync
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_DIGEST = "sha256:" + "a" * 64


class FakeSysdigClient:
    def get_schema(self):
        return {
            "entities": [
                {"name": "Vulnerability"},
                {"name": "RiskFinding"},
                {"name": "PostureFinding"},
                {"name": "RuntimeEvent"},
                {"name": "KubeWorkload"},
            ],
        }

    def query(self, query, parameters=None):
        if "Vulnerability" in query:
            return [
                {
                    "resource": {
                        "id": "resource-1",
                        "name": "prod-pod",
                        "type": "KubernetesResource",
                        "cluster": "prod",
                        "namespace": "default",
                        "imageDigest": TEST_DIGEST,
                    },
                    "vulnerability": {
                        "cveId": "CVE-2026-0001",
                        "title": "openssl vuln",
                        "severity": "high",
                        "status": "active",
                        "packageName": "openssl",
                        "packageVersion": "3.0.0",
                        "packageType": "apk",
                    },
                    "package": {
                        "name": "openssl",
                        "version": "3.0.0",
                        "type": "apk",
                    },
                }
            ]
        if "RiskFinding" in query:
            return [
                {
                    "resource": {"id": "resource-1", "name": "prod-pod"},
                    "finding": {
                        "id": "risk-1",
                        "title": "Public workload with exploitable CVE",
                        "severity": "critical",
                        "status": "open",
                    },
                }
            ]
        if "PostureFinding" in query:
            return [
                {
                    "resource": {"id": "resource-1", "name": "prod-pod"},
                    "finding": {
                        "id": "posture-1",
                        "title": "Privileged container",
                        "severity": "high",
                        "status": "open",
                    },
                }
            ]
        if "RuntimeEvent" in query:
            return [
                {
                    "resource": {"id": "resource-1", "name": "prod-pod"},
                    "event": {
                        "id": "event-1",
                        "ruleName": "Terminal shell in container",
                        "policyId": "policy-1",
                        "severity": "high",
                        "source": "syscall",
                        "engine": "falco",
                        "timestamp": "2026-04-25T00:00:00Z",
                    },
                },
                {
                    "resource": {"id": "resource-1", "name": "prod-pod"},
                    "event": {
                        "id": "event-2",
                        "ruleName": "Terminal shell in container",
                        "policyId": "policy-1",
                        "severity": "high",
                        "source": "syscall",
                        "engine": "falco",
                        "timestamp": "2026-04-25T01:00:00Z",
                    },
                },
            ]
        return []


def test_sysdig_sync_loads_findings_and_relationships(neo4j_session):
    neo4j_session.run("MATCH (n:SysdigTenant) DETACH DELETE n")
    neo4j_session.run("MATCH (n:SysdigResource) DETACH DELETE n")
    neo4j_session.run("MATCH (n:SysdigImage) DETACH DELETE n")
    neo4j_session.run("MATCH (n:SysdigPackage) DETACH DELETE n")
    neo4j_session.run("MATCH (n:SysdigVulnerabilityFinding) DETACH DELETE n")
    neo4j_session.run("MATCH (n:SysdigSecurityFinding) DETACH DELETE n")
    neo4j_session.run("MATCH (n:SysdigRiskFinding) DETACH DELETE n")
    neo4j_session.run("MATCH (n:SysdigRuntimeEventSummary) DETACH DELETE n")

    sync(
        neo4j_session,
        FakeSysdigClient(),
        "https://api.us1.sysdig.com",
        "api.us1.sysdig.com",
        TEST_UPDATE_TAG,
        24,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    assert check_nodes(neo4j_session, "SysdigTenant", ["id"]) == {
        ("api.us1.sysdig.com",),
    }
    assert check_nodes(neo4j_session, "SysdigResource", ["id", "name"]) == {
        ("resource-1", "prod-pod"),
    }
    assert check_nodes(neo4j_session, "SysdigImage", ["id", "digest"]) == {
        (TEST_DIGEST, TEST_DIGEST),
    }
    assert check_nodes(
        neo4j_session, "SysdigPackage", ["normalized_id", "name", "version"]
    ) == {
        ("apk|openssl|3.0.0", "openssl", "3.0.0"),
    }
    assert check_nodes(
        neo4j_session, "SysdigRuntimeEventSummary", ["rule_name", "event_count"]
    ) == {
        ("Terminal shell in container", 2),
    }

    finding_rows = neo4j_session.run(
        """
        MATCH (f:SysdigVulnerabilityFinding)
        RETURN f.cve_id AS cve_id, f.severity AS severity
        """
    )
    assert {(row["cve_id"], row["severity"]) for row in finding_rows} == {
        ("CVE-2026-0001", "high"),
    }

    assert check_rels(
        neo4j_session,
        "SysdigVulnerabilityFinding",
        "cve_id",
        "SysdigPackage",
        "normalized_id",
        "AFFECTS",
    ) == {
        ("CVE-2026-0001", "apk|openssl|3.0.0"),
    }
    assert check_rels(
        neo4j_session,
        "SysdigPackage",
        "normalized_id",
        "SysdigImage",
        "digest",
        "DEPLOYED",
    ) == {
        ("apk|openssl|3.0.0", TEST_DIGEST),
    }


def test_sysdig_cleanup_does_not_delete_unrelated_nodes(neo4j_session):
    neo4j_session.run(
        "MERGE (:AWSAccount {id: '123456789012', lastupdated: 1, name: 'prod'})"
    )
    neo4j_session.run(
        """
        MERGE (t:SysdigTenant {id: 'api.us1.sysdig.com', lastupdated: 1})
        MERGE (r:SysdigResource {id: 'stale-resource', lastupdated: 1})
        MERGE (r)-[:RESOURCE {lastupdated: 1}]->(t)
        """
    )

    sync(
        neo4j_session,
        FakeSysdigClient(),
        "https://api.us1.sysdig.com",
        "api.us1.sysdig.com",
        TEST_UPDATE_TAG,
        24,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    assert check_nodes(neo4j_session, "AWSAccount", ["id"]) == {("123456789012",)}
    assert ("stale-resource",) not in check_nodes(
        neo4j_session, "SysdigResource", ["id"]
    )
