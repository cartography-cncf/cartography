from cartography.models.aws.apigateway.apigateway import APIGatewayRestAPISchema
from cartography.models.aws.apigatewayv2.apigatewayv2 import APIGatewayV2APISchema
from cartography.models.gcp.api_gateway import GCPApiGatewayApiConfigSchema
from cartography.models.gcp.api_gateway import GCPApiGatewayApiSchema
from cartography.models.gcp.api_gateway import GCPApiGatewayGatewaySchema
from cartography.models.ontology.labels import API_GATEWAY
from cartography.models.ontology.mapping.data.apigateways import (
    APIGATEWAYS_ONTOLOGY_MAPPING,
)

LABELED = [
    APIGatewayRestAPISchema(),
    APIGatewayV2APISchema(),
    GCPApiGatewayGatewaySchema(),
]


def _labels(schema) -> tuple:
    extra = schema.extra_node_labels
    return extra.labels if extra else ()


def test_api_gateway_label_sits_on_every_gateway_node():
    for schema in LABELED:
        assert API_GATEWAY in _labels(schema), schema.label


def test_api_gateway_label_stays_off_the_gcp_api_and_config_nodes():
    # The gateway serves traffic at a hostname. The Api and its configs do not,
    # so labeling them would count one GCP gateway three times.
    for schema in (GCPApiGatewayApiSchema(), GCPApiGatewayApiConfigSchema()):
        assert API_GATEWAY not in _labels(schema), schema.label


def test_every_labeled_node_has_an_ontology_mapping():
    mapped = {
        node.node_label
        for mapping in APIGATEWAYS_ONTOLOGY_MAPPING.values()
        for node in mapping.nodes
    }
    assert mapped == {schema.label for schema in LABELED}
