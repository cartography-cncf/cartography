from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# Tag is a cross-provider semantic label for key/value tags applied to cloud
# resources. The node already carries the canonical `key` and `value`
# properties, so no `_ont_*` field projection is needed - the empty-fields
# entry exists only so `_ont_source` is written and the `:Tag` label is
# recognised by the ontology mapping framework.

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[OntologyNodeMapping(node_label="AWSTag", fields=[])],
)

azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[OntologyNodeMapping(node_label="AzureTag", fields=[])],
)

gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[OntologyNodeMapping(node_label="GCPLabel", fields=[])],
)

tenable_mapping = OntologyMapping(
    module_name="tenable",
    nodes=[OntologyNodeMapping(node_label="TenableAssetTag", fields=[])],
)


TAGS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "azure": azure_mapping,
    "gcp": gcp_mapping,
    "tenable": tenable_mapping,
}
