from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# ObjectStorage fields:
# _ont_name - The name/identifier of the storage bucket/container
# _ont_location - The region/location of the storage
# _ont_encrypted - Whether the storage is encrypted
# _ont_versioning - Whether versioning is enabled
# _ont_public - Whether the storage has public access (not available for all providers)

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="S3Bucket",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="name",
                    required=True,
                ),
                OntologyFieldMapping(ontology_field="location", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="encrypted",
                    node_field="default_encryption",
                    special_handling="to_boolean",
                ),
                OntologyFieldMapping(
                    ontology_field="versioning",
                    node_field="versioning_status",
                    special_handling="equal_boolean",
                    extra={"values": ["Enabled"]},
                ),
                OntologyFieldMapping(
                    ontology_field="public", node_field="anonymous_access"
                ),
            ],
        ),
    ],
)

gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPBucket",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="id",
                    required=True,
                ),
                OntologyFieldMapping(ontology_field="location", node_field="location"),
                # GCS encrypts every bucket at rest by default; `default_kms_key_name`
                # is set only for CMEK buckets, so use a static value rather than
                # mistakenly reporting Google-managed-key buckets as unencrypted.
                OntologyFieldMapping(
                    ontology_field="encrypted",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": True},
                ),
                OntologyFieldMapping(
                    ontology_field="versioning", node_field="versioning_enabled"
                ),
                # _ont_public is derived from ACLs + IAM policy bindings by the
                # `gcp_bucket_public_projection.json` analysis job — not from a
                # single bucket field.
            ],
        ),
    ],
)

azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureStorageBlobContainer",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="name",
                    required=True,
                ),
                # _ont_location: Not directly available at container level (account-level)
                OntologyFieldMapping(
                    ontology_field="encrypted",
                    node_field="default_encryption_scope",
                    special_handling="to_boolean",
                ),
                # _ont_versioning: Not directly available at container level (account-level)
                OntologyFieldMapping(
                    ontology_field="public",
                    node_field="public_access",
                    special_handling="to_boolean",
                ),
            ],
        ),
    ],
)

scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayObjectStorageBucket",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="name",
                    required=True,
                ),
                OntologyFieldMapping(ontology_field="location", node_field="region"),
                # Scaleway Object Storage encrypts every object at rest by default,
                # so report encrypted=True statically (as GCP does) rather than
                # leaving it unset.
                OntologyFieldMapping(
                    ontology_field="encrypted",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": True},
                ),
                OntologyFieldMapping(
                    ontology_field="versioning",
                    node_field="versioning_status",
                    special_handling="equal_boolean",
                    extra={"values": ["Enabled"]},
                ),
                # `public` is the tri-state combined signal (policy anonymous
                # access OR ACL AllUsers/AuthenticatedUsers; null when both
                # sources were unreadable). Mapped directly to preserve the
                # unknown state instead of coalescing it to false.
                OntologyFieldMapping(
                    ontology_field="public",
                    node_field="public",
                ),
            ],
        ),
    ],
)

OBJECT_STORAGE_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "gcp": gcp_mapping,
    "azure": azure_mapping,
    "scaleway": scaleway_mapping,
}
