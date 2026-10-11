"""Nodes written before AWS intel moved to the node-schema data model have no
_module_name and no sub-resource edge, so generated cleanup never reaches them and an
upgraded graph keeps them forever. Most of their labels survive as extra labels on the
current nodes, which is why the job keys on the exact label set rather than the label.
"""

from cartography.util import run_analysis_job

COMMON_JOB_PARAMETERS = {"UPDATE_TAG": 123456789}
STALE_TAG = 1700000000


def _ids(neo4j_session):
    return {row["id"] for row in neo4j_session.run("MATCH (n) RETURN n.id AS id")}


def test_deletes_only_unstamped_legacy_label_sets(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (principal:AWSPrincipal:AWSRole {
            id: 'live-role', _module_name: 'cartography:aws', lastupdated: $tag
        })
        CREATE (legacy_policy:AWSPolicy {id: 'legacy-policy', lastupdated: $stale})
        CREATE (live_policy:AWSManagedPolicy:AWSPolicy {
            id: 'live-policy', _module_name: 'cartography:aws', lastupdated: $tag
        })
        CREATE (principal)-[:POLICY]->(legacy_policy)
        CREATE (principal)-[:POLICY]->(live_policy)

        CREATE (:AWSPolicyStatement {id: 'legacy-statement', lastupdated: $stale})
        CREATE (:AWSPolicyStatement {
            id: 'live-statement', _module_name: 'cartography:aws', lastupdated: $stale
        })

        CREATE (:IpPermissionInbound:IpRule {id: 'legacy-inbound', lastupdated: $stale})
        CREATE (:IpPermissionEgress:IpRule {id: 'legacy-egress', lastupdated: $stale})
        CREATE (:AzureNetworkSecurityRule:IpPermissionInbound:IpRule {
            id: 'azure-rule', _module_name: 'cartography:azure', lastupdated: $stale
        })
        CREATE (:ELBV2Listener:Endpoint {id: 'legacy-listener', lastupdated: $stale})

        // Carries the legacy label as an extra label next to its current primary one.
        CREATE (:AWSEC2Subnet:EC2Subnet {id: 'current-subnet', lastupdated: $stale})
        CREATE (:EC2Subnet {id: 'legacy-subnet', lastupdated: $stale})

        // Still under an account, so the label migration and scoped cleanup own it.
        CREATE (account:AWSAccount {
            id: '123456789012', _module_name: 'cartography:aws', lastupdated: $tag
        })
        CREATE (account)-[:RESOURCE]->(:KMSAlias {id: 'parented-alias', lastupdated: $stale})

        // Elasticsearch still writes DNS records outside load(), so they stay unstamped.
        CREATE (:AWSDNSRecord:DNSRecord {id: 'es-dns-record', lastupdated: $stale})

        CREATE (:KMSAlias {id: 'refreshed-alias', lastupdated: $tag})

        // Out-of-scope account written before load() stamped _module_name, with
        // the root principal that came with it.
        CREATE (stub:AWSAccount {id: '999999999999', foreign: true, lastupdated: $stale})
        CREATE (stub)-[:RESOURCE]->(:AWSPrincipal {id: 'stub-root', lastupdated: $stale})
        // Also owned by a live account, so it outlives the stub.
        CREATE (shared:AWSPrincipal {id: 'shared-principal', lastupdated: $stale})
        CREATE (stub)-[:RESOURCE]->(shared)
        CREATE (:AWSAccount {id: '333333333333', inscope: true, _module_name: 'cartography:aws', lastupdated: $tag})-[:RESOURCE]->(shared)
        // Still in scope: the removed-account purge, not this job, decides about it.
        CREATE (:AWSAccount {id: '111111111111', inscope: true, lastupdated: $stale})
        // Unstamped, but something current still hangs off it.
        CREATE (referenced:AWSAccount {id: '222222222222', lastupdated: $stale})
        CREATE (referenced)-[:RESOURCE]->(:AWSRootPrincipal {
            id: 'live-root', _module_name: 'cartography:aws', lastupdated: $tag
        })
        """,
        tag=COMMON_JOB_PARAMETERS["UPDATE_TAG"],
        stale=STALE_TAG,
    )

    run_analysis_job(
        "aws_legacy_node_cleanup.json",
        neo4j_session,
        COMMON_JOB_PARAMETERS,
    )

    assert _ids(neo4j_session) == {
        "live-role",
        "live-policy",
        "live-statement",
        "azure-rule",
        "current-subnet",
        "es-dns-record",
        "refreshed-alias",
        "123456789012",
        "parented-alias",
        "111111111111",
        "222222222222",
        "live-root",
        "333333333333",
        "shared-principal",
    }
    assert neo4j_session.run(
        "MATCH (:AWSRole {id: 'live-role'})-[:POLICY]->(p) RETURN collect(p.id) AS ids"
    ).single()["ids"] == ["live-policy"]
