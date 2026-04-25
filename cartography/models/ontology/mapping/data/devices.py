from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

bigfix_mapping = OntologyMapping(
    module_name="bigfix",
    nodes=[
        OntologyNodeMapping(
            node_label="BigfixComputer",
            eligible_for_source=False,
            fields=[
                OntologyFieldMapping(
                    ontology_field="hostname", node_field="computername"
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
                OntologyFieldMapping(ontology_field="hostname", node_field="hostname"),
                OntologyFieldMapping(ontology_field="os", node_field="platform_name"),
                OntologyFieldMapping(
                    ontology_field="os_version", node_field="os_version"
                ),
                OntologyFieldMapping(
                    ontology_field="model", node_field="system_product_name"
                ),
                OntologyFieldMapping(
                    ontology_field="platform", node_field="platform_name"
                ),
                OntologyFieldMapping(
                    ontology_field="serial_number",
                    node_field="serial_number",
                    required=True,
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
            eligible_for_source=False,
            fields=[
                OntologyFieldMapping(
                    ontology_field="hostname", node_field="device_name"
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
            eligible_for_source=False,
            fields=[
                OntologyFieldMapping(ontology_field="hostname", node_field="name"),
                OntologyFieldMapping(ontology_field="model", node_field="model"),
                OntologyFieldMapping(ontology_field="platform", node_field="platform"),
            ],
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
                    ontology_field="hostname", node_field="device_name"
                ),
                OntologyFieldMapping(
                    ontology_field="serial_number",
                    node_field="serial_number",
                    required=True,
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
                OntologyFieldMapping(ontology_field="hostname", node_field="name"),
                OntologyFieldMapping(
                    ontology_field="serial_number", node_field="serial", required=True
                ),
                OntologyFieldMapping(ontology_field="model", node_field="model"),
            ],
        ),
    ],
)
tailscale_mapping = OntologyMapping(
    module_name="tailscale",
    nodes=[
        OntologyNodeMapping(
            node_label="TailscaleDevice",
            fields=[
                OntologyFieldMapping(ontology_field="hostname", node_field="hostname"),
                OntologyFieldMapping(ontology_field="os", node_field="os"),
                OntologyFieldMapping(
                    ontology_field="serial_number",
                    node_field="serial_number",
                    required=True,
                ),
            ],
        ),
    ],
)

googleworkspace_mapping = OntologyMapping(
    module_name="googleworkspace",
    nodes=[
        OntologyNodeMapping(
            node_label="GoogleWorkspaceDevice",
            fields=[
                OntologyFieldMapping(ontology_field="hostname", node_field="hostname"),
                OntologyFieldMapping(
                    ontology_field="os_version", node_field="os_version"
                ),
                OntologyFieldMapping(ontology_field="model", node_field="model"),
                OntologyFieldMapping(
                    ontology_field="manufacturer", node_field="manufacturer"
                ),
                OntologyFieldMapping(
                    ontology_field="serial_number",
                    node_field="serial_number",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="platform", node_field="device_type"
                ),
            ],
        ),
    ],
)

sentinelone_mapping = OntologyMapping(
    module_name="sentinelone",
    nodes=[
        OntologyNodeMapping(
            node_label="S1Agent",
            fields=[
                OntologyFieldMapping(
                    ontology_field="hostname",
                    node_field="computer_name",
                ),
                OntologyFieldMapping(
                    ontology_field="os",
                    node_field="os_name",
                ),
                OntologyFieldMapping(
                    ontology_field="os_version",
                    node_field="os_revision",
                ),
                OntologyFieldMapping(
                    ontology_field="serial_number",
                    node_field="serial_number",
                    required=True,
                ),
            ],
        ),
    ],
)

jamf_mapping = OntologyMapping(
    module_name="jamf",
    nodes=[
        OntologyNodeMapping(
            node_label="JamfComputer",
            fields=[
                OntologyFieldMapping(ontology_field="hostname", node_field="name"),
                OntologyFieldMapping(ontology_field="os", node_field="os_name"),
                OntologyFieldMapping(
                    ontology_field="os_version",
                    node_field="os_version",
                ),
                OntologyFieldMapping(ontology_field="model", node_field="model"),
                OntologyFieldMapping(ontology_field="platform", node_field="platform"),
                OntologyFieldMapping(
                    ontology_field="serial_number",
                    node_field="serial_number",
                    required=True,
                ),
            ],
        ),
        OntologyNodeMapping(
            node_label="JamfMobileDevice",
            fields=[
                OntologyFieldMapping(
                    ontology_field="hostname",
                    node_field="display_name",
                ),
                OntologyFieldMapping(
                    ontology_field="os",
                    node_field="os",
                ),
                OntologyFieldMapping(
                    ontology_field="os_version",
                    node_field="os_version",
                ),
                OntologyFieldMapping(ontology_field="model", node_field="model"),
                OntologyFieldMapping(ontology_field="platform", node_field="platform"),
                OntologyFieldMapping(
                    ontology_field="serial_number",
                    node_field="serial_number",
                    required=True,
                ),
            ],
        ),
    ],
)

jumpcloud_mapping = OntologyMapping(
    module_name="jumpcloud",
    nodes=[
        OntologyNodeMapping(
            node_label="JumpCloudSystem",
            fields=[
                OntologyFieldMapping(
                    ontology_field="serial_number",
                    node_field="serial_number",
                    required=True,
                ),
                OntologyFieldMapping(ontology_field="os", node_field="os"),
                OntologyFieldMapping(
                    ontology_field="os_version", node_field="os_version"
                ),
                OntologyFieldMapping(ontology_field="model", node_field="model"),
            ],
        ),
    ],
)

entra_mapping = OntologyMapping(
    module_name="microsoft",
    nodes=[
        OntologyNodeMapping(
            node_label="IntuneManagedDevice",
            fields=[
                OntologyFieldMapping(
                    ontology_field="hostname",
                    node_field="device_name",
                ),
                OntologyFieldMapping(
                    ontology_field="os",
                    node_field="operating_system",
                ),
                OntologyFieldMapping(
                    ontology_field="os_version",
                    node_field="os_version",
                ),
                OntologyFieldMapping(
                    ontology_field="model",
                    node_field="model",
                ),
                OntologyFieldMapping(
                    ontology_field="serial_number",
                    node_field="serial_number",
                    required=True,
                ),
            ],
        ),
    ],
)

DEVICES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "bigfix": bigfix_mapping,
    "crowdstrike": crowdstrike_mapping,
    "duo": duo_mapping,
    "microsoft": entra_mapping,
    "googleworkspace": googleworkspace_mapping,
    "jumpcloud": jumpcloud_mapping,
    "jamf": jamf_mapping,
    "kandji": kandji_mapping,
    "sentinelone": sentinelone_mapping,
    "snipeit": snipeit_mapping,
    "tailscale": tailscale_mapping,
}
