"""Shared catalog of GCP resources supported by policy bindings."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GCPFullNameMapping:
    """Map a Cloud Asset full resource name to a Cartography node."""

    service_prefix: str
    marker: str
    label: str
    id_mode: str
    asset_type: str | None = None
    additional_asset_types: tuple[str, ...] = ()


# More specific nested resource markers must precede their parents.
GCP_FULL_NAME_MAPPINGS: tuple[GCPFullNameMapping, ...] = (
    GCPFullNameMapping(
        "//cloudresourcemanager.googleapis.com/", "projects", "GCPProject", "last_segment"
    ),
    GCPFullNameMapping(
        "//cloudresourcemanager.googleapis.com/", "folders", "GCPFolder", "type_prefixed"
    ),
    GCPFullNameMapping(
        "//cloudresourcemanager.googleapis.com/",
        "organizations",
        "GCPOrganization",
        "type_prefixed",
    ),
    GCPFullNameMapping(
        "//storage.googleapis.com/",
        "buckets",
        "GCPBucket",
        "last_segment",
        "storage.googleapis.com/Bucket",
    ),
    GCPFullNameMapping(
        "//bigquery.googleapis.com/",
        "tables",
        "GCPBigQueryTable",
        "bigquery_table",
        "bigquery.googleapis.com/Table",
    ),
    GCPFullNameMapping(
        "//bigquery.googleapis.com/",
        "datasets",
        "GCPBigQueryDataset",
        "bigquery_dataset",
        "bigquery.googleapis.com/Dataset",
    ),
    GCPFullNameMapping(
        "//cloudkms.googleapis.com/",
        "cryptoKeys",
        "GCPCryptoKey",
        "full_path",
        "cloudkms.googleapis.com/CryptoKey",
    ),
    GCPFullNameMapping(
        "//cloudkms.googleapis.com/",
        "keyRings",
        "GCPKeyRing",
        "full_path",
        "cloudkms.googleapis.com/KeyRing",
    ),
    GCPFullNameMapping(
        "//secretmanager.googleapis.com/",
        "versions",
        "GCPSecretManagerSecretVersion",
        "full_path",
        "secretmanager.googleapis.com/SecretVersion",
    ),
    GCPFullNameMapping(
        "//secretmanager.googleapis.com/",
        "secrets",
        "GCPSecretManagerSecret",
        "full_path",
        "secretmanager.googleapis.com/Secret",
    ),
    GCPFullNameMapping(
        "//artifactregistry.googleapis.com/",
        "repositories",
        "GCPArtifactRegistryRepository",
        "full_path",
        "artifactregistry.googleapis.com/Repository",
    ),
    GCPFullNameMapping(
        "//run.googleapis.com/",
        "services",
        "GCPCloudRunService",
        "full_path",
        "run.googleapis.com/Service",
    ),
    GCPFullNameMapping(
        "//iam.googleapis.com/",
        "serviceAccounts",
        "GCPServiceAccount",
        "last_segment",
        "iam.googleapis.com/ServiceAccount",
    ),
    GCPFullNameMapping(
        "//cloudfunctions.googleapis.com/",
        "functions",
        "GCPCloudFunction",
        "full_path",
        "cloudfunctions.googleapis.com/Function",
        ("cloudfunctions.googleapis.com/CloudFunction",),
    ),
    GCPFullNameMapping(
        "//compute.googleapis.com/",
        "instances",
        "GCPInstance",
        "full_path",
        "compute.googleapis.com/Instance",
    ),
    GCPFullNameMapping(
        "//compute.googleapis.com/",
        "networks",
        "GCPVpc",
        "full_path",
        "compute.googleapis.com/Network",
    ),
    GCPFullNameMapping(
        "//compute.googleapis.com/",
        "subnetworks",
        "GCPSubnet",
        "full_path",
        "compute.googleapis.com/Subnetwork",
    ),
    GCPFullNameMapping(
        "//compute.googleapis.com/",
        "firewalls",
        "GCPFirewall",
        "full_path",
        "compute.googleapis.com/Firewall",
    ),
)

GCP_POLICY_BINDING_TARGET_LABELS: tuple[str, ...] = tuple(
    dict.fromkeys(mapping.label for mapping in GCP_FULL_NAME_MAPPINGS)
)
