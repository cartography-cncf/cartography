from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import CleanupScopedTo
from cartography.graph.analysis import SetProperty
from cartography.graph.analysis import Var

ENTRA_APPLICATION_PROJECTION = AnalysisJob(
    name="Ontology - Entra application projection",
    short_name="ontology_entra_application_projection",
    scope=CleanupScopedTo("EntraTenant", "TENANT_ID"),
    statements=(
        AnalysisStatement(
            match="MATCH (app:EntraApplication)<-[:RESOURCE]-(tenant:EntraTenant {id: $TENANT_ID}) OPTIONAL MATCH (tenant)-[:RESOURCE]->(sp:EntraServicePrincipal {app_id: app.app_id}) WITH app, sp",
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
