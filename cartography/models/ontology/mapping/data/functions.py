from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# Function fields:
# name - The name of the function (required)
# runtime - The runtime environment (e.g., python3.9, nodejs18.x)
# memory - Memory allocated to the function (in MB)
# timeout - Timeout for function execution (in seconds)
# deployment_type - The deployment type: "code" for source code functions, "container" for container-based
# image - Container image URI (for container-based deployments)
# image_digest - Digest of the container image (for container-based deployments)

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSLambda",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="runtime", node_field="runtime"),
                OntologyFieldMapping(ontology_field="memory", node_field="memory"),
                OntologyFieldMapping(ontology_field="timeout", node_field="timeout"),
                # AWS Lambda PackageType is "Zip" (code) or "Image" (container).
                # When "Image", image_uri and image_digest are populated from Code.ImageUri.
                OntologyFieldMapping(ontology_field="image", node_field="image_uri"),
                OntologyFieldMapping(
                    ontology_field="image_digest", node_field="image_digest"
                ),
                OntologyFieldMapping(
                    ontology_field="deployment_type",
                    node_field="packagetype",
                    special_handling="mapping",
                    extra={
                        "map": {
                            "Zip": "code",
                            "Image": "container",
                        },
                    },
                ),
            ],
        ),
    ],
)

gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPCloudFunction",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="runtime", node_field="runtime"),
                OntologyFieldMapping(
                    ontology_field="memory", node_field="available_memory_mb"
                ),
                OntologyFieldMapping(ontology_field="timeout", node_field="timeout"),
                OntologyFieldMapping(
                    ontology_field="deployment_type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "code"},
                ),
            ],
        ),
    ],
)

azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureFunctionApp",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # Function Apps can be code-based or container-based; image_uri is populated only
                # for DOCKER|... linuxFxVersion configurations.
                OntologyFieldMapping(ontology_field="image", node_field="image_uri"),
                OntologyFieldMapping(
                    ontology_field="image_digest", node_field="image_digest"
                ),
                OntologyFieldMapping(
                    ontology_field="deployment_type",
                    node_field="deployment_type",
                ),
                # runtime: not available in AzureFunctionApp
                # memory: not available in AzureFunctionApp
                # timeout: not available in AzureFunctionApp
            ],
        ),
    ],
)

scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayServerlessFunction",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="runtime", node_field="runtime"),
                OntologyFieldMapping(
                    ontology_field="memory", node_field="memory_limit"
                ),
                OntologyFieldMapping(ontology_field="timeout", node_field="timeout"),
                # Scaleway Serverless Functions are source-code deployments.
                OntologyFieldMapping(
                    ontology_field="deployment_type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "code"},
                ),
            ],
        ),
    ],
)

supabase_mapping = OntologyMapping(
    module_name="supabase",
    nodes=[
        OntologyNodeMapping(
            node_label="SupabaseEdgeFunction",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # Edge functions are Deno source deployments, never containers.
                OntologyFieldMapping(
                    ontology_field="deployment_type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "code"},
                ),
                # runtime / memory / timeout: Not available. Supabase does not
                # expose per-function resource limits through the Management API.
            ],
        ),
    ],
)

modal_mapping = OntologyMapping(
    module_name="modal",
    nodes=[
        OntologyNodeMapping(
            node_label="ModalFunction",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # Every Modal function runs from a Modal image, never from a zip of source.
                OntologyFieldMapping(
                    ontology_field="deployment_type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "container"},
                ),
                # runtime: Modal does not report the interpreter version of a deployed function.
                # memory / timeout: write-only in Modal's API (see the ModalFunction model).
                # image / image_digest: Modal image ids are neither digests nor pull URIs.
            ],
        ),
    ],
)

FUNCTIONS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "gcp": gcp_mapping,
    "azure": azure_mapping,
    "scaleway": scaleway_mapping,
    "supabase": supabase_mapping,
    "modal": modal_mapping,
}
