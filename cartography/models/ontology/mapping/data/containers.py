from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping
from cartography.models.ontology.mapping.specs import OntologyRelMapping

aws_ecs_container_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="ECSContainer",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="arn", required=True
                ),
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="image", node_field="image"),
                OntologyFieldMapping(
                    ontology_field="image_digest", node_field="image_digest"
                ),
                OntologyFieldMapping(ontology_field="state", node_field="last_status"),
                OntologyFieldMapping(ontology_field="cpu", node_field="cpu"),
                OntologyFieldMapping(ontology_field="memory", node_field="memory"),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="architecture", node_field="architecture"
                ),
                # namespace: Not applicable for ECS containers (AWS does not use namespaces)
                OntologyFieldMapping(
                    ontology_field="health_status", node_field="health_status"
                ),
            ],
        ),
    ],
    rels=[
        OntologyRelMapping(
            __comment__="Delete stale ECSContainer RESOLVED_IMAGE relationships for this run.",
            query=(
                "MATCH (c:ECSContainer {lastupdated: $UPDATE_TAG})-[r:RESOLVED_IMAGE]->(:Image) "
                "DELETE r"
            ),
        ),
        OntologyRelMapping(
            __comment__="Create deterministic architecture-aware RESOLVED_IMAGE for ECSContainer.",
            query=(
                "MATCH (c:ECSContainer {lastupdated: $UPDATE_TAG}) "
                "OPTIONAL MATCH (c)-[:HAS_IMAGE]->(img_direct:Image) "
                "WITH c, collect(DISTINCT {id: img_direct.id, priority: 0}) AS direct_candidates "
                "OPTIONAL MATCH (c)-[:HAS_IMAGE]->(:ImageManifestList)-[:CONTAINS_IMAGE]->(img_child:Image) "
                "WHERE coalesce(c.architecture, 'unknown') <> 'unknown' AND img_child.architecture = c.architecture "
                "WITH c, [x IN (direct_candidates + collect(DISTINCT {id: img_child.id, priority: 1})) WHERE x.id IS NOT NULL] AS candidates "
                "CALL { "
                "  WITH candidates "
                "  UNWIND candidates AS cand "
                "  RETURN cand "
                "  ORDER BY cand.priority ASC, cand.id ASC "
                "  LIMIT 1 "
                "} "
                "MATCH (resolved:Image {id: cand.id}) "
                "MERGE (c)-[r:RESOLVED_IMAGE]->(resolved) "
                "ON CREATE SET r.firstseen = timestamp() "
                "SET r.lastupdated = $UPDATE_TAG"
            ),
        ),
    ],
)

kubernetes_mapping = OntologyMapping(
    module_name="kubernetes",
    nodes=[
        OntologyNodeMapping(
            node_label="KubernetesContainer",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="id", required=True
                ),
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="image", node_field="image"),
                OntologyFieldMapping(
                    ontology_field="image_digest", node_field="status_image_sha"
                ),
                OntologyFieldMapping(ontology_field="state", node_field="status_state"),
                # cpu: Not exposed as a direct field in KubernetesContainer node
                # memory: Not exposed as a direct field in KubernetesContainer node
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="architecture", node_field="architecture"
                ),
                OntologyFieldMapping(
                    ontology_field="namespace", node_field="namespace"
                ),
                # health_status: Kubernetes uses status_ready and status_started separately, not a unified health_status field
            ],
        ),
    ],
    rels=[
        OntologyRelMapping(
            __comment__="Delete stale KubernetesContainer RESOLVED_IMAGE relationships for this run.",
            query=(
                "MATCH (c:KubernetesContainer {lastupdated: $UPDATE_TAG})-[r:RESOLVED_IMAGE]->(:Image) "
                "DELETE r"
            ),
        ),
        OntologyRelMapping(
            __comment__="Create deterministic architecture-aware RESOLVED_IMAGE for KubernetesContainer.",
            query=(
                "MATCH (c:KubernetesContainer {lastupdated: $UPDATE_TAG}) "
                "OPTIONAL MATCH (c)-[:HAS_IMAGE]->(img_direct:Image) "
                "WITH c, collect(DISTINCT {id: img_direct.id, priority: 0}) AS direct_candidates "
                "OPTIONAL MATCH (c)-[:HAS_IMAGE]->(:ImageManifestList)-[:CONTAINS_IMAGE]->(img_child:Image) "
                "WHERE coalesce(c.architecture, 'unknown') <> 'unknown' AND img_child.architecture = c.architecture "
                "WITH c, [x IN (direct_candidates + collect(DISTINCT {id: img_child.id, priority: 1})) WHERE x.id IS NOT NULL] AS candidates "
                "CALL { "
                "  WITH candidates "
                "  UNWIND candidates AS cand "
                "  RETURN cand "
                "  ORDER BY cand.priority ASC, cand.id ASC "
                "  LIMIT 1 "
                "} "
                "MATCH (resolved:Image {id: cand.id}) "
                "MERGE (c)-[r:RESOLVED_IMAGE]->(resolved) "
                "ON CREATE SET r.firstseen = timestamp() "
                "SET r.lastupdated = $UPDATE_TAG"
            ),
        ),
    ],
)

azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureContainerInstance",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="id", required=True
                ),
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                # image: Not exposed as a direct field in AzureContainerInstance node (image info is in nested container properties)
                # image_digest: Not exposed as a direct field in AzureContainerInstance node
                OntologyFieldMapping(
                    ontology_field="state", node_field="provisioning_state"
                ),
                # cpu: Not exposed as a direct field in AzureContainerInstance node
                # memory: Not exposed as a direct field in AzureContainerInstance node
                OntologyFieldMapping(ontology_field="region", node_field="location"),
                OntologyFieldMapping(
                    ontology_field="architecture", node_field="architecture"
                ),
                # namespace: Not applicable for Azure Container Instances (Azure does not use namespaces in this context)
                # health_status: Not exposed as a direct field in AzureContainerInstance node
            ],
        ),
    ],
    rels=[
        OntologyRelMapping(
            __comment__="Delete stale AzureContainerInstance RESOLVED_IMAGE relationships for this run.",
            query=(
                "MATCH (c:AzureContainerInstance {lastupdated: $UPDATE_TAG})-[r:RESOLVED_IMAGE]->(:Image) "
                "DELETE r"
            ),
        ),
        OntologyRelMapping(
            __comment__="Create deterministic digest-based RESOLVED_IMAGE for AzureContainerInstance.",
            query=(
                "MATCH (c:AzureContainerInstance {lastupdated: $UPDATE_TAG}) "
                "WITH c, coalesce(c.image_digests, []) AS image_digests "
                "OPTIONAL MATCH (img_direct:Image) "
                "WHERE img_direct.digest IN image_digests "
                "WITH c, [x IN collect(DISTINCT {id: img_direct.id, priority: 0}) WHERE x.id IS NOT NULL] AS candidates "
                "CALL { "
                "  WITH candidates "
                "  UNWIND candidates AS cand "
                "  RETURN cand "
                "  ORDER BY cand.priority ASC, cand.id ASC "
                "  LIMIT 1 "
                "} "
                "MATCH (resolved:Image {id: cand.id}) "
                "MERGE (c)-[r:RESOLVED_IMAGE]->(resolved) "
                "ON CREATE SET r.firstseen = timestamp() "
                "SET r.lastupdated = $UPDATE_TAG"
            ),
        ),
    ],
)

CONTAINER_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws_ecs_container": aws_ecs_container_mapping,
    "kubernetes": kubernetes_mapping,
    "azure": azure_mapping,
}
