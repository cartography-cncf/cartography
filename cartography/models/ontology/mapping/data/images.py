from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# Image ontology fields:
# - id: Unique identifier (digest for most registries)
# - digest: SHA256 digest of the image
# - uri: Full URI to pull the image
# - architecture: CPU architecture (amd64, arm64, etc.)
# - os: Operating system (linux, windows)

aws_ecr_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="ECRImage",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="id", required=True
                ),
                OntologyFieldMapping(ontology_field="digest", node_field="digest"),
                OntologyFieldMapping(
                    ontology_field="architecture", node_field="architecture"
                ),
                OntologyFieldMapping(ontology_field="os", node_field="os"),
            ],
        ),
    ],
)

gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPArtifactRegistryContainerImage",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="id", required=True
                ),
                OntologyFieldMapping(ontology_field="digest", node_field="digest"),
                OntologyFieldMapping(ontology_field="uri", node_field="uri"),
            ],
        ),
        OntologyNodeMapping(
            node_label="GCPArtifactRegistryPlatformImage",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="id", required=True
                ),
                OntologyFieldMapping(ontology_field="digest", node_field="digest"),
                OntologyFieldMapping(
                    ontology_field="architecture", node_field="architecture"
                ),
                OntologyFieldMapping(ontology_field="os", node_field="os"),
            ],
        ),
    ],
)

gitlab_mapping = OntologyMapping(
    module_name="gitlab",
    nodes=[
        OntologyNodeMapping(
            node_label="GitLabContainerImage",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="id", required=True
                ),
                OntologyFieldMapping(ontology_field="digest", node_field="digest"),
                OntologyFieldMapping(ontology_field="uri", node_field="uri"),
                OntologyFieldMapping(
                    ontology_field="architecture", node_field="architecture"
                ),
                OntologyFieldMapping(ontology_field="os", node_field="os"),
            ],
        ),
    ],
)

IMAGES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_ecr_mapping,
    "gcp": gcp_mapping,
    "gitlab": gitlab_mapping,
}
