from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping
from cartography.models.ontology.mapping.specs import OntologyRelMapping

trivy_mapping = OntologyMapping(
    module_name="trivy",
    nodes=[
        OntologyNodeMapping(
            node_label="TrivyPackage",
            fields=[
                OntologyFieldMapping(
                    ontology_field="normalized_id",
                    node_field="normalized_id",
                    required=True,
                ),
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="version", node_field="version"),
                OntologyFieldMapping(ontology_field="type", node_field="type"),
                OntologyFieldMapping(ontology_field="purl", node_field="purl"),
            ],
        ),
    ],
    rels=[
        OntologyRelMapping(
            __comment__="Link Package to ECRImage via TrivyPackage DEPLOYED",
            query=(
                "MATCH (p:Package)-[:DETECTED_AS]->(tp:TrivyPackage)-[:DEPLOYED]->(img:ECRImage) "
                "MERGE (p)-[r:DEPLOYED]->(img) "
                "ON CREATE SET r.firstseen = timestamp() "
                "SET r.lastupdated = $UPDATE_TAG"
            ),
            iterative=False,
        ),
        OntologyRelMapping(
            __comment__="Link Package to GCPArtifactRegistryContainerImage via TrivyPackage DEPLOYED",
            query=(
                "MATCH (p:Package)-[:DETECTED_AS]->(tp:TrivyPackage)"
                "-[:DEPLOYED]->(img:GCPArtifactRegistryContainerImage) "
                "MERGE (p)-[r:DEPLOYED]->(img) "
                "ON CREATE SET r.firstseen = timestamp() "
                "SET r.lastupdated = $UPDATE_TAG"
            ),
            iterative=False,
        ),
        OntologyRelMapping(
            __comment__="Link Package to GCPArtifactRegistryPlatformImage via TrivyPackage DEPLOYED",
            query=(
                "MATCH (p:Package)-[:DETECTED_AS]->(tp:TrivyPackage)"
                "-[:DEPLOYED]->(img:GCPArtifactRegistryPlatformImage) "
                "MERGE (p)-[r:DEPLOYED]->(img) "
                "ON CREATE SET r.firstseen = timestamp() "
                "SET r.lastupdated = $UPDATE_TAG"
            ),
            iterative=False,
        ),
        OntologyRelMapping(
            __comment__="Link Package to GitLabContainerImage via TrivyPackage DEPLOYED",
            query=(
                "MATCH (p:Package)-[:DETECTED_AS]->(tp:TrivyPackage)"
                "-[:DEPLOYED]->(img:GitLabContainerImage) "
                "MERGE (p)-[r:DEPLOYED]->(img) "
                "ON CREATE SET r.firstseen = timestamp() "
                "SET r.lastupdated = $UPDATE_TAG"
            ),
            iterative=False,
        ),
        # TODO: When a canonical Vulnerability ontology node exists, migrate this
        # propagation to link Vulnerability -> Package and deprecate this finding-based edge.
        OntologyRelMapping(
            __comment__="Link TrivyImageFinding AFFECTS to canonical Package via TrivyPackage",
            query=(
                "MATCH (f:TrivyImageFinding)-[:AFFECTS]->(tp:TrivyPackage)"
                "<-[:DETECTED_AS]-(p:Package) "
                "MERGE (f)-[r:AFFECTS]->(p) "
                "ON CREATE SET r.firstseen = timestamp() "
                "SET r.lastupdated = $UPDATE_TAG"
            ),
            iterative=False,
        ),
        # DEPRECATED: compatibility edge; remove in Cartography v1.
        OntologyRelMapping(
            __comment__="Link Package SHOULD_UPDATE_TO TrivyFix via TrivyPackage for compatibility",
            query=(
                "MATCH (p:Package)-[:DETECTED_AS]->(tp:TrivyPackage)"
                "-[:SHOULD_UPDATE_TO]->(fix:TrivyFix) "
                "MERGE (p)-[r:SHOULD_UPDATE_TO]->(fix) "
                "ON CREATE SET r.firstseen = timestamp() "
                "SET r.lastupdated = $UPDATE_TAG"
            ),
            iterative=False,
        ),
    ],
)

syft_mapping = OntologyMapping(
    module_name="syft",
    nodes=[
        OntologyNodeMapping(
            node_label="SyftPackage",
            fields=[
                OntologyFieldMapping(
                    ontology_field="normalized_id",
                    node_field="normalized_id",
                    required=True,
                ),
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="version", node_field="version"),
                OntologyFieldMapping(ontology_field="type", node_field="type"),
                OntologyFieldMapping(ontology_field="purl", node_field="purl"),
            ],
        ),
    ],
    rels=[
        OntologyRelMapping(
            __comment__="Link Package DEPENDS_ON Package via SyftPackage dependency graph",
            query=(
                "MATCH (p1:Package)-[:DETECTED_AS]->(sp1:SyftPackage)"
                "-[:DEPENDS_ON]->(sp2:SyftPackage)<-[:DETECTED_AS]-(p2:Package) "
                "MERGE (p1)-[r:DEPENDS_ON]->(p2) "
                "ON CREATE SET r.firstseen = timestamp() "
                "SET r.lastupdated = $UPDATE_TAG"
            ),
            iterative=False,
        ),
    ],
)

PACKAGES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "trivy": trivy_mapping,
    "syft": syft_mapping,
}
