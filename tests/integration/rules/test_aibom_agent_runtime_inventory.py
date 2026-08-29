"""
End-to-end coverage for aibom_agent_runtime_inventory: seeds agents across runtime
states and tenants, runs the real ontology job that materializes HAS_RUNTIME_IMAGE, and
asserts the rule reports one row per running agent and workload. The rule reports the
workload rather than its context, so the last test walks from a reported workload to the
tenant and exposure a consumer would read off the graph.
"""

from cartography.analysis.ontology.analysis import WORKLOAD_HAS_RUNTIME_IMAGE
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.nist_ai_rmf import (
    _aibom_nist_ai_agent_runtime_inventory,
)
from cartography.util import run_typed_analysis_job

TEST_UPDATE_TAG = 123456789


def _seed(neo4j_session) -> None:
    """Three agents: one exposed in prod, one internal in prod, one not running at all.

    The prod pair sits under a tenant and a cluster; the staging agent under a
    different tenant and no cluster, which is the serverless shape.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (prod:Tenant:AWSAccount {id: 'account-prod'})
        SET prod._ont_name = 'example-prod', prod.lastupdated = $tag
        MERGE (staging:Tenant:AWSAccount {id: 'account-staging'})
        SET staging._ont_name = 'example-staging', staging.lastupdated = $tag
        MERGE (cluster:ComputeCluster:AWSECSCluster {id: 'cluster-prod'})
        SET cluster._ont_name = 'prod-cluster', cluster.lastupdated = $tag
        """,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        UNWIND [
            {key: 'exposed',  exposure: true,  tenant: 'account-prod',    clustered: true},
            {key: 'internal', exposure: false, tenant: 'account-prod',    clustered: true},
            {key: 'staging',  exposure: false, tenant: 'account-staging', clustered: false}
        ] AS spec
        MATCH (tenant:Tenant {id: spec.tenant})
        MERGE (svc:ComputeService:AWSECSService {id: 'svc-' + spec.key})
        SET svc._ont_name = 'workload-' + spec.key,
            svc._ont_region = 'us-east-1',
            svc._ont_source = 'aws',
            svc.lastupdated = $tag
        MERGE (container:Container:AWSECSContainer {id: 'container-' + spec.key})
        SET container._ont_state = 'running',
            container.exposed_internet = spec.exposure,
            container.lastupdated = $tag
        MERGE (img:Image:AWSECRImage {id: 'sha256:' + spec.key})
        SET img._ont_digest = 'sha256:' + spec.key, img.lastupdated = $tag
        MERGE (container)-[wp:WORKLOAD_PARENT]->(svc) SET wp.lastupdated = $tag
        MERGE (container)-[ri:RESOLVED_IMAGE]->(img) SET ri.lastupdated = $tag
        MERGE (tenant)-[res:RESOURCE]->(svc) SET res.lastupdated = $tag
        WITH spec, svc
        MATCH (cluster:ComputeCluster {id: 'cluster-prod'})
        WHERE spec.clustered
        MERGE (svc)-[cp:WORKLOAD_PARENT]->(cluster) SET cp.lastupdated = $tag
        """,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        // The offline agent's image was scanned but nothing is running it.
        MERGE (img:Image:AWSECRImage {id: 'sha256:offline'})
        SET img._ont_digest = 'sha256:offline', img.lastupdated = $tag
        """,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        UNWIND ['exposed', 'internal', 'staging', 'offline'] AS key
        MATCH (img:Image {id: 'sha256:' + key})
        MERGE (source:AIBOMSource {id: 'aibom-' + key})
        SET source.image_uri = 'registry.example.com/' + key + ':latest',
            source.lastupdated = $tag
        MERGE (agent:AIBOMComponent:AIAgent {id: 'agent-' + key})
        SET agent.name = 'agent-' + key,
            agent.logical_id = 'logical-' + key,
            agent.framework = 'examplechain',
            agent.lastupdated = $tag
        MERGE (tool:AIBOMComponent:AITool {id: 'tool-' + key})
        SET tool.name = 'tool-' + key, tool.lastupdated = $tag
        MERGE (source)-[si:SCANNED_IMAGE]->(img) SET si.lastupdated = $tag
        MERGE (source)-[hc:HAS_COMPONENT]->(agent) SET hc.lastupdated = $tag
        MERGE (agent)-[di:DETECTED_IN]->(img) SET di.lastupdated = $tag
        MERGE (agent)-[ut:USES_TOOL]->(tool) SET ut.lastupdated = $tag
        """,
        tag=TEST_UPDATE_TAG,
    )
    run_typed_analysis_job(
        WORKLOAD_HAS_RUNTIME_IMAGE, neo4j_session, {"UPDATE_TAG": TEST_UPDATE_TAG}
    )


def _findings(neo4j_session):
    return neo4j_session.execute_read(
        read_list_of_dicts_tx, _aibom_nist_ai_agent_runtime_inventory.cypher_query
    )


def test_reports_only_agents_that_are_running(neo4j_session) -> None:
    _seed(neo4j_session)

    findings = _findings(neo4j_session)

    # The scanned-but-not-running agent is the whole point of the runtime narrowing:
    # it is in the AIBOM inventory and must not be in this one.
    assert {f["agent_component_id"] for f in findings} == {
        "agent-exposed",
        "agent-internal",
        "agent-staging",
    }


def test_reports_one_row_per_agent_and_workload(neo4j_session) -> None:
    _seed(neo4j_session)

    findings = _findings(neo4j_session)
    by_agent = {f["agent_component_id"]: f for f in findings}

    assert len(findings) == len(by_agent)
    exposed = by_agent["agent-exposed"]
    assert exposed["agent_name"] == "agent-exposed"
    assert exposed["workload_name"] == "workload-exposed"
    assert exposed["workload_id"] == "svc-exposed"
    assert exposed["ontology_source"] == "aws"
    assert exposed["image_uri"] == "registry.example.com/exposed:latest"


def test_reported_workload_anchors_tenant_and_exposure(neo4j_session) -> None:
    """The rule deliberately stops at the workload. This is the walk a consumer makes
    from a reported workload_id to answer "is this one in production, and is it
    reachable", so a change that broke that anchor would fail here."""
    _seed(neo4j_session)

    by_agent = {f["agent_component_id"]: f for f in _findings(neo4j_session)}

    context = neo4j_session.run(
        """
        UNWIND $workload_ids AS workload_id
        MATCH (svc:ComputeService {id: workload_id})
        OPTIONAL MATCH (tenant:Tenant)-[:RESOURCE]->(svc)
        OPTIONAL MATCH (svc)-[:WORKLOAD_PARENT]->(cluster:ComputeCluster)
        OPTIONAL MATCH (svc)-[hri:HAS_RUNTIME_IMAGE]->(:Image)
        RETURN
            workload_id,
            tenant._ont_name AS tenant_name,
            cluster._ont_name AS cluster_name,
            hri.exposed_internet AS internet_exposed
        """,
        workload_ids=[f["workload_id"] for f in by_agent.values()],
    )
    by_workload = {r["workload_id"]: r for r in context}

    assert by_workload[by_agent["agent-exposed"]["workload_id"]] == {
        "workload_id": "svc-exposed",
        "tenant_name": "example-prod",
        "cluster_name": "prod-cluster",
        "internet_exposed": True,
    }
    assert by_workload[by_agent["agent-internal"]["workload_id"]] == {
        "workload_id": "svc-internal",
        "tenant_name": "example-prod",
        "cluster_name": "prod-cluster",
        "internet_exposed": False,
    }
    # Serverless: a tenant but no cluster.
    staging = by_workload[by_agent["agent-staging"]["workload_id"]]
    assert staging["tenant_name"] == "example-staging"
    assert staging["cluster_name"] is None
