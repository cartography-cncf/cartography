from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import CleanupScopedTo
from cartography.graph.analysis import Param

INTUNE_COMPLIANCE_POLICY_DEVICE = AnalysisJob(
    name="Intune compliance policy to device resolution",
    short_name="intune_compliance_policy_device",
    scope=CleanupScopedTo("EntraTenant", "TENANT_ID"),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="MATCH (:EntraTenant {id: $TENANT_ID})-[:RESOURCE]->(policy:IntuneCompliancePolicy)-[:ASSIGNED_TO]->(g:EntraGroup)<-[:MEMBER_OF]-(u:EntraUser)-[:ENROLLED_TO]->(device:IntuneManagedDevice) WHERE policy.lastupdated = $UPDATE_TAG AND device.lastupdated = $UPDATE_TAG",
            effects=(
                AddRelationship(
                    "policy",
                    "APPLIES_TO",
                    "device",
                    firstseen=Param("UPDATE_TAG"),
                    source_label="IntuneCompliancePolicy",
                    target_label="IntuneManagedDevice",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (policy:IntuneCompliancePolicy)<-[:RESOURCE]-(t:EntraTenant {id: $TENANT_ID})-[:RESOURCE]->(device:IntuneManagedDevice) WHERE policy.applies_to_all_users = true AND policy.lastupdated = $UPDATE_TAG AND device.lastupdated = $UPDATE_TAG MATCH (u:EntraUser)-[:ENROLLED_TO]->(device)",
            effects=(
                AddRelationship(
                    "policy",
                    "APPLIES_TO",
                    "device",
                    firstseen=Param("UPDATE_TAG"),
                    source_label="IntuneCompliancePolicy",
                    target_label="IntuneManagedDevice",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (policy:IntuneCompliancePolicy)<-[:RESOURCE]-(t:EntraTenant {id: $TENANT_ID})-[:RESOURCE]->(device:IntuneManagedDevice) WHERE policy.applies_to_all_devices = true AND policy.lastupdated = $UPDATE_TAG AND device.lastupdated = $UPDATE_TAG",
            effects=(
                AddRelationship(
                    "policy",
                    "APPLIES_TO",
                    "device",
                    firstseen=Param("UPDATE_TAG"),
                    source_label="IntuneCompliancePolicy",
                    target_label="IntuneManagedDevice",
                ),
            ),
        ),
    ),
)
