from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# Snapshot fields:
# _ont_name - The name/identifier of the snapshot
# _ont_encrypted - Whether the snapshot is encrypted at rest
# _ont_public - Whether the snapshot is publicly shared (a known attack vector)
# _ont_source_id - The source volume/database the snapshot was taken from
# _ont_created_at - When the snapshot was created
# _ont_region - The region/zone where the snapshot lives

aws_ebs_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="EBSSnapshot",
            fields=[
                # EBS snapshots have no display name; the SnapshotId (`id`) is the
                # canonical identifier.
                OntologyFieldMapping(
                    ontology_field="name", node_field="id", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="encrypted", node_field="encrypted"
                ),
                OntologyFieldMapping(ontology_field="public", node_field="ispublic"),
                OntologyFieldMapping(ontology_field="source_id", node_field="volumeid"),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="starttime"
                ),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
            ],
        ),
        OntologyNodeMapping(
            node_label="RDSSnapshot",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="db_snapshot_identifier",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="encrypted", node_field="encrypted"
                ),
                OntologyFieldMapping(ontology_field="public", node_field="ispublic"),
                # The source of an RDS snapshot is the database instance it was
                # taken from.
                OntologyFieldMapping(
                    ontology_field="source_id", node_field="db_instance_identifier"
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="snapshot_create_time"
                ),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
            ],
        ),
    ],
)

azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureSnapshot",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # _ont_encrypted: not mapped. The `encryption` field on AzureSnapshot
                # is `encryption_settings_collection.enabled`, the legacy Azure Disk
                # Encryption (ADE) flag. Azure snapshots are encrypted at rest by
                # default via SSE regardless of that flag, so mapping it would make
                # most snapshots look unencrypted in cross-cloud posture queries.
                # _ont_public: not mapped. Azure snapshots do not expose a public
                # sharing flag; access is governed by network_access_policy.
                # _ont_source_id: not mapped. The source disk is not stored on the
                # snapshot node.
                # _ont_created_at: not mapped. No creation timestamp is captured.
                OntologyFieldMapping(ontology_field="region", node_field="location"),
            ],
        ),
    ],
)

scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayVolumeSnapshot",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # _ont_encrypted: Scaleway volume snapshots do not expose encryption
                # posture in the API.
                # _ont_public: Scaleway volume snapshots do not expose a public
                # sharing flag.
                # _ont_source_id: the source volume is only available through the
                # HAS relationship, not as a property on the snapshot node.
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="creation_date"
                ),
                OntologyFieldMapping(ontology_field="region", node_field="zone"),
            ],
        ),
    ],
)

SNAPSHOTS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_ebs_mapping,
    "azure": azure_mapping,
    "scaleway": scaleway_mapping,
}
