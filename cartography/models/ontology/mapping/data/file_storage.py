from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# FileStorage fields:
# _ont_name - The name/identifier of the file system/share
# _ont_location - The region/location of the file storage
# _ont_encrypted - Whether the storage is encrypted at rest

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="EfsFileSystem",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="location", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="encrypted", node_field="encrypted"
                ),
            ],
        ),
    ],
)

azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureStorageFileShare",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
            ],
        ),
    ],
)

FILE_STORAGE_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "azure": azure_mapping,
}
