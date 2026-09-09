from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# APIGateway fields:
# name - The name of the gateway
# hostname - The DNS name clients actually call. Absent where the provider does
#   not store a resolvable address on the gateway resource itself.
# state - The provider-native lifecycle state. NOT normalized: AWS REST APIs have
#   no lifecycle state at all, GCP uses CREATING/ACTIVE/FAILED/DELETING/UPDATING,
#   and Azure APIM uses a different set again. Left raw, as with LoadBalancer.lb_type.
# created_at - When the gateway was created
# updated_at - When the gateway was last updated

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSAPIGatewayRestAPI",
            fields=[
                # AWSAPIGatewayRestAPI carries no name property; the REST API id is
                # the only stable label on the node.
                OntologyFieldMapping(
                    ontology_field="name", node_field="id", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="createddate"
                ),
                # hostname: not stored on this node. The execute-api address is
                # composed from the API id, region, and a stage, so it belongs to
                # AWSAPIGatewayStage rather than to the API.
                # state: REST APIs have no lifecycle state field.
            ],
        ),
        OntologyNodeMapping(
            node_label="AWSAPIGatewayV2API",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="hostname", node_field="apiendpoint"
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="createddate"
                ),
                # state: HTTP and WebSocket APIs have no lifecycle state field.
            ],
        ),
    ],
)

gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPApiGatewayGateway",
            fields=[
                # displayName is optional upstream; fall back to the resource name
                # so _ont_name is always populated.
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="display_name",
                    required=True,
                    special_handling="coalesce",
                    extra={"fields": ["name"]},
                ),
                OntologyFieldMapping(
                    ontology_field="hostname", node_field="default_hostname"
                ),
                OntologyFieldMapping(ontology_field="state", node_field="state"),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="create_time"
                ),
                OntologyFieldMapping(
                    ontology_field="updated_at", node_field="update_time"
                ),
            ],
        ),
    ],
)

APIGATEWAYS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "gcp": gcp_mapping,
}
