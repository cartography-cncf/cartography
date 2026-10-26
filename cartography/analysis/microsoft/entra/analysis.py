from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import ScopeById
from cartography.graph.analysis import SetProperty
from cartography.graph.analysis import Var

ENTRA_APPLICATION_PROJECTION = AnalysisJob(
    name="Ontology - Entra application projection",
    short_name="ontology_entra_application_projection",
    scope=ScopeById("EntraTenant", "TENANT_ID", scope_on="app"),
    statements=(
        AnalysisStatement(
            match="MATCH (app:EntraApplication)<-[:RESOURCE]-(tenant:EntraTenant) OPTIONAL MATCH (tenant)-[:RESOURCE]->(sp:EntraServicePrincipal {app_id: app.app_id}) WITH app, sp",
            effects=(
                SetProperty(
                    "app",
                    "_ont_enabled",
                    Var("sp.account_enabled"),
                    label="EntraApplication",
                ),
            ),
        ),
    ),
)

# EntraServicePrincipal's ontology mapping is its ServiceAccount one, and a node label
# takes a single mapping, so the ThirdPartyApp fields of a vendor app's service
# principal are projected here instead. `_ont_name` already comes from that mapping.
ENTRA_THIRD_PARTY_APP_PROJECTION = AnalysisJob(
    name="Ontology - Entra third-party app projection",
    short_name="ontology_entra_third_party_app_projection",
    scope=ScopeById("EntraTenant", "TENANT_ID", scope_on="sp"),
    statements=(
        AnalysisStatement(
            match="MATCH (sp:EntraServicePrincipal:ThirdPartyApp)<-[:RESOURCE]-(tenant:EntraTenant)",
            effects=(
                SetProperty(
                    "sp",
                    "_ont_client_id",
                    Var("sp.app_id"),
                    label="EntraServicePrincipal",
                ),
                SetProperty(
                    "sp",
                    "_ont_enabled",
                    Var("sp.account_enabled"),
                    label="EntraServicePrincipal",
                ),
            ),
        ),
    ),
)
