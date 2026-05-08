from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

useraccount_mapping = OntologyMapping(
    module_name="ontology",
    nodes=[
        OntologyNodeMapping(
            node_label="UserAccount",
            fields=[
                OntologyFieldMapping(
                    ontology_field="email", node_field="_ont_email", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="fullname", node_field="_ont_fullname"
                ),
                OntologyFieldMapping(
                    ontology_field="firstname", node_field="_ont_firstname"
                ),
                OntologyFieldMapping(
                    ontology_field="lastname", node_field="_ont_lastname"
                ),
                OntologyFieldMapping(
                    ontology_field="inactive", node_field="_ont_inactive"
                ),
            ],
        ),
    ],
)


USERS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "ontology": useraccount_mapping,
}
