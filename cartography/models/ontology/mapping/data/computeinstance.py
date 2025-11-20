from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="EC2Instance",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="id", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="name", node_field="instanceid", required=True
                ),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="public_ip_address", node_field="publicipaddress"
                ),
                OntologyFieldMapping(
                    ontology_field="private_ip_address", node_field="privateipaddress"
                ),
                OntologyFieldMapping(ontology_field="state", node_field="state"),
                OntologyFieldMapping(ontology_field="type", node_field="instancetype"),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="launchtime"
                ),
            ],
        ),
    ],
)

scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayInstance",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="id", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="region", node_field="zone"),
                OntologyFieldMapping(
                    ontology_field="private_ip_address", node_field="private_ip"
                ),
                OntologyFieldMapping(ontology_field="state", node_field="state"),
                OntologyFieldMapping(
                    ontology_field="type", node_field="commercial_type"
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="creation_date"
                ),
            ],
        ),
    ],
)

digitalocean_mapping = OntologyMapping(
    module_name="digitalocean",
    nodes=[
        OntologyNodeMapping(
            node_label="DODroplet",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="id", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="public_ip_address", node_field="ip_address"
                ),
                OntologyFieldMapping(
                    ontology_field="private_ip_address", node_field="private_ip_address"
                ),
                OntologyFieldMapping(ontology_field="state", node_field="status"),
                OntologyFieldMapping(ontology_field="type", node_field="size"),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_at"
                ),
            ],
        ),
    ],
)

COMPUTE_INSTANCE_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "scaleway": scaleway_mapping,
    "digitalocean": digitalocean_mapping,
}
