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
    rels=[
        OntologyRelMapping(
            __comment__="Link AWSSSOUser to User based on external_id mapping to arbitrary UserAccount node",
            query="MATCH (sso:AWSSSOUser) MATCH (u:User)-[:HAS_ACCOUNT]->(:UserAccount {id: sso.external_id}) MERGE (u)-[r:HAS_ACCOUNT]->(sso) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
            iterative=False,
        ),
        OntologyRelMapping(
            __comment__="Link GitHubUser to User based on organization_verified_domain_emails on GitHubUser node",
            query="MATCH (u:User) WHERE u.email is not NULL MATCH (g:GitHubUser) WHERE u.email in g.organization_verified_domain_emails MERGE (u)-[r:HAS_ACCOUNT]->(g) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
            iterative=False,
        ),
        OntologyRelMapping(
            __comment__="Link User to APIKey",
            query="MATCH (u:User)-[:HAS_ACCOUNT]->(:UserAccount)-[:OWNS|HAS]->(k:APIKey) MERGE (u)-[r:OWNS]->(k) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
            iterative=False,
        ),
        OntologyRelMapping(
            __comment__="Link User to ThirdPartyApp",
            query="MATCH (u:User)-[:HAS_ACCOUNT]->(:UserAccount)-[authr:AUTHORIZED|APPLICATION]->(a:ThirdPartyApp) MERGE (u)-[r:AUTHORIZED]->(a) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG, r.scopes = coalesce(authr.scopes, [])",
            iterative=False,
        ),
        # TODO: Change this when we have a Ontology Group node
        OntologyRelMapping(
            __comment__="Link User to ThirdPartyApp (via groups) (okta specific)",
            query="MATCH (u:User)-[:HAS_ACCOUNT]->(:OktaUser)-[:MEMBER_OF_OKTA_GROUP]->(:OktaGroup)-[:APPLICATION]->(a:ThirdPartyApp) MERGE (u)-[r:AUTHORIZED]->(a) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
            iterative=False,
        ),
    ],
)


USERS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "ontology": useraccount_mapping,
}
