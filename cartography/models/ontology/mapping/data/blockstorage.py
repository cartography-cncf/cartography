from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# BlockStorage fields:
# _ont_name - The name/identifier of the block storage volume
# _ont_size_gb - The size of the volume in gigabytes
# _ont_encrypted - Whether the volume is encrypted at rest
# _ont_region - The region/zone where the volume lives
# _ont_state - The lifecycle state of the volume (e.g., "available", "in-use")

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="EBSVolume",
            fields=[
                # EBSVolume has no display name; the VolumeId (`id`) is the canonical identifier.
                OntologyFieldMapping(
                    ontology_field="name", node_field="id", required=True
                ),
                OntologyFieldMapping(ontology_field="size_gb", node_field="size"),
                OntologyFieldMapping(
                    ontology_field="encrypted", node_field="encrypted"
                ),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(ontology_field="state", node_field="state"),
            ],
        ),
    ],
)

azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureDisk",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="size_gb", node_field="disksizegb"),
                # _ont_encrypted: not mapped. The `encryption` field stored on AzureDisk is
                # `encryption_settings_collection.enabled`, which reflects the legacy Azure Disk
                # Encryption (ADE) feature. Azure managed disks are encrypted at rest by default
                # via Storage Service Encryption (SSE) regardless of that flag, so mapping it
                # here would make most disks look unencrypted in cross-cloud posture queries.
                # Revisit once SSE / disk-encryption-set posture is modelled on AzureDisk.
                OntologyFieldMapping(ontology_field="region", node_field="location"),
                OntologyFieldMapping(ontology_field="state", node_field="state"),
            ],
        ),
    ],
)

scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayVolume",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="size_gb", node_field="size_gb"),
                # _ont_encrypted: Scaleway block volumes do not expose encryption posture in the volume API.
                OntologyFieldMapping(ontology_field="region", node_field="zone"),
                OntologyFieldMapping(ontology_field="state", node_field="state"),
            ],
        ),
    ],
)

BLOCK_STORAGE_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "azure": azure_mapping,
    "scaleway": scaleway_mapping,
}
