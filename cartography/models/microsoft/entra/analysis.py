from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisScope
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import PropertyEffect

ENTRA_SCOPE = AnalysisScope("EntraTenant", "TENANT_ID")

ENTRA_APPLICATION_PROJECTION = AnalysisJob(
    name="Ontology - Entra application projection",
    short_name="ontology_entra_application_projection",
    scope=ENTRA_SCOPE,
    effect=PropertyEffect("EntraApplication", ("_ont_enabled",)),
    statements=(
        AnalysisStatement(
            "MATCH (app:EntraApplication)<-[:RESOURCE]-(tenant:EntraTenant {id: $TENANT_ID}) "
            "OPTIONAL MATCH (tenant)-[:RESOURCE]->(sp:EntraServicePrincipal {app_id: app.app_id}) "
            "WITH app, sp "
            "SET app._ont_enabled = sp.account_enabled",
        ),
    ),
)
