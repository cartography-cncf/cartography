from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import Expr
from cartography.graph.analysis import ScopedTo
from cartography.graph.analysis import SetProperty

ENTRA_APPLICATION_PROJECTION = AnalysisJob(
    name="Ontology - Entra application projection",
    short_name="ontology_entra_application_projection",
    scope=ScopedTo("EntraTenant", "TENANT_ID"),
    statements=(
        AnalysisStatement(
            match="MATCH (app:EntraApplication)<-[:RESOURCE]-(tenant:EntraTenant {id: $TENANT_ID}) OPTIONAL MATCH (tenant)-[:RESOURCE]->(sp:EntraServicePrincipal {app_id: app.app_id}) WITH app, sp",
            effects=(
                SetProperty(
                    "app",
                    "_ont_enabled",
                    Expr("sp.account_enabled"),
                    label="EntraApplication",
                ),
            ),
        ),
    ),
)
