from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping
from cartography.models.ontology.mapping.specs import OntologyRelMapping


useraccount_mapping = OntologyMapping(
    module_name="ontology",
    nodes=[
        OntologyNodeMapping(
            node_label="UserAccount",
            fields=[
                OntologyFieldMapping(
                    ontology_field="email", node_field="email_address", required=True
                ),
                OntologyFieldMapping(ontology_field="fullname", node_field="full_name"),
                OntologyFieldMapping(
                    ontology_field="firstname", node_field="first_name"
                ),
                OntologyFieldMapping(ontology_field="lastname", node_field="last_name"),
            ],
        ),
    ],
    rels=[
        OntologyRelMapping(
            __comment__="Link AWSSSOUser to User based on external_id mapping to arbitrary UserAccount node",
            query="MATCH (sso:AWSSSOUser) MATCH (u:User)-[:HAS_ACCOUNT]->(:UserAccount {id: sso.external_id}) MERGE (u)-[r:HAS_ACCOUNT]->(sso) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
            iterative=False,
        ),
    ],
)


USERS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "ontology": useraccount_mapping,
}
