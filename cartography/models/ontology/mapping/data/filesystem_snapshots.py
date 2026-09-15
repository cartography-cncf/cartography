from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# FilesystemSnapshot fields:
# _ont_kind - Snapshot type, initially `source`; future host snapshots may use `rootfs`.
# _ont_source_revision - Immutable source revision represented by the snapshot.
# _ont_root_directory - Repository-relative directory represented by the snapshot.

railway_mapping = OntologyMapping(
    module_name="railway",
    nodes=[
        OntologyNodeMapping(
            node_label="RailwayFilesystemSnapshot",
            fields=[
                OntologyFieldMapping(ontology_field="kind", node_field="kind"),
                OntologyFieldMapping(
                    ontology_field="source_revision",
                    node_field="source_revision",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="root_directory", node_field="root_directory"
                ),
            ],
        ),
    ],
)

FILESYSTEM_SNAPSHOTS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "railway": railway_mapping,
}
