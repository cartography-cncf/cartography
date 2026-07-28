from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# ComputeInstance fields:
# _ont_state - Normalized lifecycle/power state of the instance. Providers use
#   heterogeneous vocabularies, so each is mapped to the shared canonical set:
#   running, starting, stopping, stopped, pending, suspended, terminated, error, unknown.
#   The raw provider value stays on the source node's own state/status property.

# AWS EC2 InstanceState.Name
_AWS_EC2_STATE = {
    "pending": "pending",
    "running": "running",
    "shutting-down": "stopping",
    "stopping": "stopping",
    "stopped": "stopped",
    "terminated": "terminated",
}

# GCP Compute Instance.status
_GCP_INSTANCE_STATE = {
    "PROVISIONING": "pending",
    "STAGING": "starting",
    "RUNNING": "running",
    "STOPPING": "stopping",
    "SUSPENDING": "stopping",
    "SUSPENDED": "suspended",
    "REPAIRING": "error",
    # GCP TERMINATED means powered off, not deleted.
    "TERMINATED": "stopped",
    "DEPROVISIONING": "stopping",
}

# DigitalOcean Droplet status
_DO_DROPLET_STATE = {
    "new": "pending",
    "active": "running",
    "off": "stopped",
    "archive": "terminated",
}

# Scaleway instance ServerState
_SCALEWAY_INSTANCE_STATE = {
    "running": "running",
    "starting": "starting",
    "stopping": "stopping",
    "stopped": "stopped",
    "stopped_in_place": "stopped",
    "locked": "suspended",
}

# Scaleway Elastic Metal (baremetal) ServerStatus
_SCALEWAY_BAREMETAL_STATE = {
    "unknown": "unknown",
    "delivering": "pending",
    "ordered": "pending",
    "ready": "running",
    "starting": "starting",
    "resetting": "starting",
    "stopping": "stopping",
    "stopped": "stopped",
    "error": "error",
    "deleting": "terminated",
    "locked": "suspended",
    "out_of_stock": "unknown",
    "migrating": "unknown",
}

# Scaleway Apple Silicon ServerStatus
_SCALEWAY_APPLESILICON_STATE = {
    "unknown_status": "unknown",
    "starting": "starting",
    "rebooting": "starting",
    "reinstalling": "starting",
    "unlocking": "starting",
    "updating": "starting",
    "ready": "running",
    "busy": "running",
    "error": "error",
    "locking": "suspended",
    "locked": "suspended",
}

# Scaleway Dedibox server ServerStatus
_SCALEWAY_DEDIBOX_STATE = {
    "unknown": "unknown",
    "delivering": "pending",
    "installing": "pending",
    "ready": "running",
    "rescue": "running",
    "busy": "running",
    "stopped": "stopped",
    "locked": "suspended",
    "error": "error",
}

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSEC2Instance",
            fields=[
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
                OntologyFieldMapping(
                    ontology_field="state",
                    node_field="state",
                    special_handling="mapping",
                    extra={"map": _AWS_EC2_STATE},
                ),
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
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="region", node_field="zone"),
                OntologyFieldMapping(
                    ontology_field="private_ip_address", node_field="private_ip"
                ),
                OntologyFieldMapping(
                    ontology_field="state",
                    node_field="state",
                    special_handling="mapping",
                    extra={"map": _SCALEWAY_INSTANCE_STATE},
                ),
                OntologyFieldMapping(
                    ontology_field="type", node_field="commercial_type"
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="creation_date"
                ),
            ],
        ),
        OntologyNodeMapping(
            node_label="ScalewayElasticMetalServer",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="region", node_field="zone"),
                OntologyFieldMapping(
                    ontology_field="public_ip_address", node_field="public_ip"
                ),
                OntologyFieldMapping(
                    ontology_field="state",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _SCALEWAY_BAREMETAL_STATE},
                ),
                OntologyFieldMapping(ontology_field="type", node_field="offer_name"),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_at"
                ),
            ],
        ),
        OntologyNodeMapping(
            node_label="ScalewayAppleSiliconServer",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="region", node_field="zone"),
                OntologyFieldMapping(
                    ontology_field="public_ip_address", node_field="ip"
                ),
                OntologyFieldMapping(
                    ontology_field="state",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _SCALEWAY_APPLESILICON_STATE},
                ),
                OntologyFieldMapping(ontology_field="type", node_field="type"),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_at"
                ),
            ],
        ),
        OntologyNodeMapping(
            node_label="ScalewayDediboxServer",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="hostname", required=True
                ),
                OntologyFieldMapping(ontology_field="region", node_field="zone"),
                OntologyFieldMapping(
                    ontology_field="public_ip_address", node_field="public_ip"
                ),
                OntologyFieldMapping(
                    ontology_field="state",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _SCALEWAY_DEDIBOX_STATE},
                ),
                OntologyFieldMapping(ontology_field="type", node_field="offer_name"),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_at"
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
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="public_ip_address", node_field="ip_address"
                ),
                OntologyFieldMapping(
                    ontology_field="private_ip_address", node_field="private_ip_address"
                ),
                OntologyFieldMapping(
                    ontology_field="state",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _DO_DROPLET_STATE},
                ),
                OntologyFieldMapping(ontology_field="type", node_field="size"),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_at"
                ),
            ],
        ),
    ],
)
gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPInstance",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="instancename", required=True
                ),
                OntologyFieldMapping(ontology_field="region", node_field="zone_name"),
                OntologyFieldMapping(
                    ontology_field="state",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _GCP_INSTANCE_STATE},
                ),
                OntologyFieldMapping(ontology_field="type", node_field="machine_type"),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="creation_timestamp"
                ),
                OntologyFieldMapping(
                    ontology_field="public_ip_address", node_field="public_ip"
                ),
                OntologyFieldMapping(
                    ontology_field="private_ip_address", node_field="private_ip"
                ),
            ],
        ),
    ],
)
azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureVirtualMachine",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="region", node_field="location"),
                OntologyFieldMapping(ontology_field="type", node_field="size"),
                # public_ip_address: not available in AzureVirtualMachine
                # private_ip_address: not available in AzureVirtualMachine
                # state: not available in AzureVirtualMachine
                # created_at: not available in AzureVirtualMachine
            ],
        ),
    ],
)

COMPUTE_INSTANCE_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "scaleway": scaleway_mapping,
    "digitalocean": digitalocean_mapping,
    "gcp": gcp_mapping,
    "azure": azure_mapping,
}
