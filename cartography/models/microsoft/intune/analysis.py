from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisScope
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import RelationshipEffect

ENTRA_SCOPE = AnalysisScope("EntraTenant", "TENANT_ID")

INTUNE_COMPLIANCE_POLICY_DEVICE = AnalysisJob(
    name="Intune compliance policy to device resolution",
    short_name="intune_compliance_policy_device",
    scope=ENTRA_SCOPE,
    effect=RelationshipEffect(
        "IntuneCompliancePolicy",
        "APPLIES_TO",
        "IntuneManagedDevice",
    ),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            "MATCH (:EntraTenant {id: $TENANT_ID})-[:RESOURCE]->(policy:IntuneCompliancePolicy)-[:ASSIGNED_TO]->(g:EntraGroup)<-[:MEMBER_OF]-(u:EntraUser)-[:ENROLLED_TO]->(device:IntuneManagedDevice) WHERE policy.lastupdated = $UPDATE_TAG AND device.lastupdated = $UPDATE_TAG MERGE (policy)-[r:APPLIES_TO]->(device) ON CREATE SET r.firstseen = $UPDATE_TAG SET r.lastupdated = $UPDATE_TAG RETURN COUNT(*) AS TotalCompleted",
        ),
        AnalysisStatement(
            "MATCH (policy:IntuneCompliancePolicy)<-[:RESOURCE]-(t:EntraTenant {id: $TENANT_ID})-[:RESOURCE]->(device:IntuneManagedDevice) WHERE policy.applies_to_all_users = true AND policy.lastupdated = $UPDATE_TAG AND device.lastupdated = $UPDATE_TAG MATCH (u:EntraUser)-[:ENROLLED_TO]->(device) MERGE (policy)-[r:APPLIES_TO]->(device) ON CREATE SET r.firstseen = $UPDATE_TAG SET r.lastupdated = $UPDATE_TAG RETURN COUNT(*) AS TotalCompleted",
        ),
        AnalysisStatement(
            "MATCH (policy:IntuneCompliancePolicy)<-[:RESOURCE]-(t:EntraTenant {id: $TENANT_ID})-[:RESOURCE]->(device:IntuneManagedDevice) WHERE policy.applies_to_all_devices = true AND policy.lastupdated = $UPDATE_TAG AND device.lastupdated = $UPDATE_TAG MERGE (policy)-[r:APPLIES_TO]->(device) ON CREATE SET r.firstseen = $UPDATE_TAG SET r.lastupdated = $UPDATE_TAG RETURN COUNT(*) AS TotalCompleted",
        ),
    ),
)
