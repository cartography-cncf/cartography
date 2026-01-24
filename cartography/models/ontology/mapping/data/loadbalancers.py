from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# LoadBalancer fields:
# name - The name of the load balancer
# lb_type - The type of load balancer (application, network, classic, etc.)
# scheme - The scheme (internal or internet-facing)
# dns_name - The DNS name/endpoint
# region - The region/location

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSLoadBalancerV2",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="lb_type", node_field="type"),
                OntologyFieldMapping(ontology_field="scheme", node_field="scheme"),
                OntologyFieldMapping(ontology_field="dns_name", node_field="dnsname"),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
            ],
        ),
        OntologyNodeMapping(
            node_label="AWSLoadBalancer",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="lb_type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "classic"},
                ),
                OntologyFieldMapping(ontology_field="scheme", node_field="scheme"),
                OntologyFieldMapping(ontology_field="dns_name", node_field="dnsname"),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
            ],
        ),
    ],
)

gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPForwardingRule",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="scheme", node_field="load_balancing_scheme"
                ),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                # lb_type: not directly available, depends on backend service type
                # dns_name: GCP uses IP addresses, not DNS names for forwarding rules
            ],
        ),
    ],
)

azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureLoadBalancer",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="lb_type", node_field="sku_name"),
                OntologyFieldMapping(ontology_field="region", node_field="location"),
                # scheme: not directly available in AzureLoadBalancer
                # dns_name: not directly available in AzureLoadBalancer
            ],
        ),
    ],
)

LOADBALANCERS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "gcp": gcp_mapping,
    "azure": azure_mapping,
}
