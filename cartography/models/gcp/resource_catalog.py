"""Shared catalog of GCP resources supported by policy bindings."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GCPFullNameMapping:
    """
    Rule that maps a Cloud Asset full resource name to a Cartography node.

    - ``service_prefix``: the full name must start with this (e.g.
      ``"//cloudkms.googleapis.com/"``).
    - ``marker``: the path segment identifying the resource type (e.g.
      ``"cryptoKeys"``). The segment immediately after the marker is the name.
    - ``label``: Cartography node label.
    - ``id_mode``:
        * ``"last_segment"``: just the name (GCPProject, GCPBucket).
        * ``"type_prefixed"``: ``"{marker}/{name}"`` (GCPFolder, GCPOrganization).
        * ``"full_path"``: the whole path up to and including the name
          (KMS, Secrets, Artifact Registry, Cloud Run, Compute).
        * ``"bigquery_dataset"``: ``"{project_id}:{dataset_id}"``.
        * ``"bigquery_table"``: ``"{project_id}:{dataset_id}.{table_id}"``.
    - ``asset_type``: Cloud Asset asset type to request from SearchAllIamPolicies for
      direct child-resource policies. Resource Manager scopes are fetched through
      BatchGetEffectiveIamPolicies instead, so they need no search asset type here.
    - ``additional_asset_types``: extra Cloud Asset asset types that use the same
      full-name shape and Cartography node label.
    """

    service_prefix: str
    marker: str
    label: str
    id_mode: str
    asset_type: str | None = None
    additional_asset_types: tuple[str, ...] = ()


# Order matters within a given service_prefix: more specific mappings first so
# nested resource types win (e.g. a cryptoKey full name also contains
# ``/keyRings/``, so GCPCryptoKey must precede GCPKeyRing).
GCP_FULL_NAME_MAPPINGS: tuple[GCPFullNameMapping, ...] = (
    # Cloud Resource Manager.
    GCPFullNameMapping(
        "//cloudresourcemanager.googleapis.com/",
        "projects",
        "GCPProject",
        "last_segment",
    ),
    GCPFullNameMapping(
        "//cloudresourcemanager.googleapis.com/",
        "folders",
        "GCPFolder",
        "type_prefixed",
    ),
    GCPFullNameMapping(
        "//cloudresourcemanager.googleapis.com/",
        "organizations",
        "GCPOrganization",
        "type_prefixed",
    ),
    # Cloud Storage.
    GCPFullNameMapping(
        "//storage.googleapis.com/",
        "buckets",
        "GCPBucket",
        "last_segment",
        "storage.googleapis.com/Bucket",
    ),
    # BigQuery: table wins over dataset (nested).
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
    # KMS: cryptoKey wins over keyRing (nested).
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
    # Secret Manager: version wins over secret (nested).
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
    # Artifact Registry.
    GCPFullNameMapping(
        "//artifactregistry.googleapis.com/",
        "repositories",
        "GCPArtifactRegistryRepository",
        "full_path",
        "artifactregistry.googleapis.com/Repository",
    ),
    # Cloud Run services.
    GCPFullNameMapping(
        "//run.googleapis.com/",
        "services",
        "GCPCloudRunService",
        "full_path",
        "run.googleapis.com/Service",
    ),
    # IAM service accounts.
    GCPFullNameMapping(
        "//iam.googleapis.com/",
        "serviceAccounts",
        "GCPServiceAccount",
        "last_segment",
        "iam.googleapis.com/ServiceAccount",
    ),
    # Cloud Functions.
    GCPFullNameMapping(
        "//cloudfunctions.googleapis.com/",
        "functions",
        "GCPCloudFunction",
        "full_path",
        "cloudfunctions.googleapis.com/Function",
        ("cloudfunctions.googleapis.com/CloudFunction",),
    ),
    # Compute: the node id is the "partial URI" (``projects/.../{kind}/{name}``),
    # which matches the path left after stripping the service prefix.
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
