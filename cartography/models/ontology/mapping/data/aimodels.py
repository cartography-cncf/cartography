from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# AIModel fields:
# _ont_name - The name/identifier of the AI/ML model
# _ont_provider - The vendor (e.g. "Anthropic", "Amazon", "Meta") when known,
#                 otherwise the cloud provider hosting the model ("aws", "gcp")
# _ont_status - The lifecycle/operational status of the model
# _ont_type - One of "foundation", "custom", "fine-tuned"

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSBedrockFoundationModel",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="model_name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="provider", node_field="provider_name"
                ),
                OntologyFieldMapping(
                    ontology_field="status", node_field="model_lifecycle_status"
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "foundation"},
                ),
            ],
        ),
        OntologyNodeMapping(
            node_label="AWSBedrockCustomModel",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="model_name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="provider",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "aws"},
                ),
                OntologyFieldMapping(ontology_field="status", node_field="status"),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="customization_type",
                    special_handling="mapping",
                    extra={
                        "map": {
                            "FINE_TUNING": "fine-tuned",
                            "CONTINUED_PRE_TRAINING": "custom",
                            "DISTILLATION": "custom",
                            "IMPORTED": "custom",
                        }
                    },
                ),
            ],
        ),
        OntologyNodeMapping(
            node_label="AWSSageMakerModel",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="model_name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="provider",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "aws"},
                ),
                # _ont_status: SageMaker models do not expose a lifecycle status field
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "custom"},
                ),
            ],
        ),
    ],
)

gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPVertexAIModel",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="display_name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="provider",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "gcp"},
                ),
                # _ont_status: Vertex AI models do not expose a lifecycle status field
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "custom"},
                ),
            ],
        ),
    ],
)

aibom_mapping = OntologyMapping(
    module_name="aibom",
    nodes=[
        # AIBOMComponent already attaches a conditional :AIModel label when
        # category="model" (see cartography/models/aibom/component.py). The
        # mapping below applies to every AIBOMComponent regardless of category;
        # for non-model components model_name is null so _ont_name will not be
        # set and the row will not surface in MATCH (m:AIModel) queries.
        # _ont_type is intentionally unmapped because most categories are not
        # models (agent, tool, memory, embedding, prompt).
        OntologyNodeMapping(
            node_label="AIBOMComponent",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="model_name", required=True
                ),
                OntologyFieldMapping(ontology_field="provider", node_field="framework"),
            ],
        ),
    ],
)

AIMODELS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "gcp": gcp_mapping,
    "aibom": aibom_mapping,
}
