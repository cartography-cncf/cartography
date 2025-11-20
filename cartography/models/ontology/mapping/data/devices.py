from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping
from cartography.models.ontology.mapping.specs import OntologyRelMapping

bigfix_mapping = OntologyMapping(
    module_name="bigfix",
    nodes=[
        OntologyNodeMapping(
            node_label="BigfixComputer",
            fields=[
                OntologyFieldMapping(
                    ontology_field="hostname", node_field="computername", required=True
                ),
                OntologyFieldMapping(ontology_field="os", node_field="os"),
            ],
        ),
    ],
)
crowdstrike_mapping = OntologyMapping(
    module_name="crowdstrike",
    nodes=[
        OntologyNodeMapping(
            node_label="CrowdstrikeHost",
            fields=[
                OntologyFieldMapping(
                    ontology_field="hostname", node_field="hostname", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="os_version", node_field="os_version"
                ),
                OntologyFieldMapping(
                    ontology_field="platform", node_field="platform_name"
                ),
                OntologyFieldMapping(
                    ontology_field="serial_number", node_field="serial_number"
                ),
                OntologyFieldMapping(
                    ontology_field="instance_id", node_field="instance_id"
                ),
            ],
        ),
    ],
)
duo_mapping = OntologyMapping(
    module_name="duo",
    nodes=[
        OntologyNodeMapping(
            node_label="DuoEndpoint",
            fields=[
                OntologyFieldMapping(
                    ontology_field="hostname", node_field="device_name", required=True
                ),
                OntologyFieldMapping(ontology_field="os", node_field="os_family"),
                OntologyFieldMapping(
                    ontology_field="os_version", node_field="os_version"
                ),
                OntologyFieldMapping(ontology_field="model", node_field="model"),
            ],
        ),
        OntologyNodeMapping(
            node_label="DuoPhone",
            fields=[
                OntologyFieldMapping(
                    ontology_field="hostname", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="model", node_field="model"),
                OntologyFieldMapping(ontology_field="platform", node_field="platform"),
            ],
        ),
    ],
    rels=[
        OntologyRelMapping(
            __comment__="Link Device to User based on DuoUser-DuoPhone relationship",
            query="MATCH (u:User)-[:HAS_ACCOUNT]->(:DuoUser)-[:HAS_DUO_PHONE]-(:DuoPhone)<-[:OBSERVED_AS]-(d:Device) MERGE (u)-[r:OWNS]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
            iterative=False,
        ),
        OntologyRelMapping(
            __comment__="Link Device to User based on DuoUser-DuoEndpoint relationship",
            query="MATCH (u:User)-[:HAS_ACCOUNT]->(:DuoUser)-[:HAS_DUO_ENDPOINT]-(:DuoEndpoint)<-[:OBSERVED_AS]-(d:Device) MERGE (u)-[r:OWNS]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
            iterative=False,
        ),
    ],
)
kandji_mapping = OntologyMapping(
    module_name="kandji",
    nodes=[
        OntologyNodeMapping(
            node_label="KandjiDevice",
            fields=[
                OntologyFieldMapping(
                    ontology_field="hostname", node_field="device_name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="serial_number", node_field="serial_number"
                ),
                OntologyFieldMapping(
                    ontology_field="os_version", node_field="os_version"
                ),
                OntologyFieldMapping(ontology_field="model", node_field="model"),
                OntologyFieldMapping(ontology_field="platform", node_field="platform"),
            ],
        ),
    ],
)
snipeit_mapping = OntologyMapping(
    module_name="snipeit",
    nodes=[
        OntologyNodeMapping(
            node_label="SnipeitAsset",
            fields=[
                OntologyFieldMapping(
                    ontology_field="hostname", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="serial_number", node_field="serial"
                ),
                OntologyFieldMapping(ontology_field="model", node_field="model"),
            ],
        ),
    ],
    rels=[
        OntologyRelMapping(
            __comment__="Link Device to User based on SnipeitUser-SnipeitAsset relationship",
            query="MATCH (u:User)-[:HAS_ACCOUNT]->(:SnipeitUser)-[:HAS_CHECKED_OUT]-(:SnipeitAsset)<-[:OBSERVED_AS]-(d:Device) MERGE (u)-[r:OWNS]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
            iterative=False,
        )
    ],
)
tailscale_mapping = OntologyMapping(
    module_name="tailscale",
    nodes=[
        OntologyNodeMapping(
            node_label="TailscaleDevice",
            fields=[
                OntologyFieldMapping(
                    ontology_field="hostname", node_field="hostname", required=True
                ),
                OntologyFieldMapping(ontology_field="os", node_field="os"),
            ],
        ),
    ],
    rels=[
        OntologyRelMapping(
            __comment__="Link Device to User based on TailscaleUser-TailscaleDevice relationship",
            query="MATCH (u:User)-[:HAS_ACCOUNT]->(:TailscaleUser)-[:OWNS]-(:TailscaleDevice)<-[:OBSERVED_AS]-(d:Device) MERGE (u)-[r:OWNS]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
            iterative=False,
        )
    ],
)

googleworkspace_mapping = OntologyMapping(
    module_name="googleworkspace",
    nodes=[
        OntologyNodeMapping(
            node_label="GoogleWorkspaceDevice",
            fields=[
                OntologyFieldMapping(
                    ontology_field="hostname", node_field="hostname", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="os_version", node_field="os_version"
                ),
                OntologyFieldMapping(ontology_field="model", node_field="model"),
                OntologyFieldMapping(
                    ontology_field="manufacturer", node_field="manufacturer"
                ),
                OntologyFieldMapping(
                    ontology_field="serial_number", node_field="serial_number"
                ),
                OntologyFieldMapping(
                    ontology_field="platform", node_field="device_type"
                ),
            ],
        ),
    ],
    rels=[
        OntologyRelMapping(
            __comment__="Link Device to User based on GoogleWorkspaceUser-GoogleWorkspaceDevice relationship",
            query="MATCH (u:User)-[:HAS_ACCOUNT]->(:GoogleWorkspaceUser)-[:OWNS]-(:GoogleWorkspaceDevice)<-[:OBSERVED_AS]-(d:Device) MERGE (u)-[r:OWNS]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
            iterative=False,
        )
    ],
)

DEVICES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "bigfix": bigfix_mapping,
    "crowdstrike": crowdstrike_mapping,
    "duo": duo_mapping,
    "googleworkspace": googleworkspace_mapping,
    "kandji": kandji_mapping,
    "snipeit": snipeit_mapping,
    "tailscale": tailscale_mapping,
}
