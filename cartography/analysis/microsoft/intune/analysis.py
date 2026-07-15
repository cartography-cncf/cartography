from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import Param
from cartography.graph.analysis import ScopeById

INTUNE_COMPLIANCE_POLICY_DEVICE = AnalysisJob(
    name="Intune compliance policy to device resolution",
    short_name="intune_compliance_policy_device",
    scope=ScopeById("EntraTenant", "TENANT_ID", scope_on="policy"),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="MATCH (policy:IntuneCompliancePolicy)-[:ASSIGNED_TO]->(g:EntraGroup)<-[:MEMBER_OF]-(u:EntraUser)-[:ENROLLED_TO]->(device:IntuneManagedDevice)",
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
            incremental_on=("policy", "device"),
        ),
        AnalysisStatement(
            match="MATCH (policy:IntuneCompliancePolicy)<-[:RESOURCE]-(t:EntraTenant)-[:RESOURCE]->(device:IntuneManagedDevice) WHERE policy.applies_to_all_users = true MATCH (u:EntraUser)-[:ENROLLED_TO]->(device)",
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
            incremental_on=("policy", "device"),
        ),
        AnalysisStatement(
            match="MATCH (policy:IntuneCompliancePolicy)<-[:RESOURCE]-(t:EntraTenant)-[:RESOURCE]->(device:IntuneManagedDevice) WHERE policy.applies_to_all_devices = true",
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
            incremental_on=("policy", "device"),
        ),
    ),
)
