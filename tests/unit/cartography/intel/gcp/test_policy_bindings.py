import pytest

from cartography.intel.gcp.policy_bindings import _parse_full_resource_name


@pytest.mark.parametrize(
    "full_name, expected",
    [
        # CRM
        (
            "//cloudresourcemanager.googleapis.com/projects/project-abc",
            ("GCPProject", "project-abc"),
        ),
        (
            "//cloudresourcemanager.googleapis.com/folders/1414",
            ("GCPFolder", "folders/1414"),
        ),
        (
            "//cloudresourcemanager.googleapis.com/organizations/1337",
            ("GCPOrganization", "organizations/1337"),
        ),
        # Storage
        (
            "//storage.googleapis.com/buckets/test-bucket",
            ("GCPBucket", "test-bucket"),
        ),
        # Storage sub-resource resolves to owning bucket
        (
            "//storage.googleapis.com/buckets/test-bucket/objects/foo.txt",
            ("GCPBucket", "test-bucket"),
        ),
        # KMS — cryptoKey wins over keyRing
        (
            "//cloudkms.googleapis.com/projects/p/locations/us/keyRings/r/cryptoKeys/k",
            ("GCPCryptoKey", "projects/p/locations/us/keyRings/r/cryptoKeys/k"),
        ),
        # KMS — plain keyRing
        (
            "//cloudkms.googleapis.com/projects/p/locations/us/keyRings/r",
            ("GCPKeyRing", "projects/p/locations/us/keyRings/r"),
        ),
        # KMS — cryptoKey version resolves up to the cryptoKey
        (
            "//cloudkms.googleapis.com/projects/p/locations/us/keyRings/r/cryptoKeys/k/cryptoKeyVersions/1",
            ("GCPCryptoKey", "projects/p/locations/us/keyRings/r/cryptoKeys/k"),
        ),
        # Secret Manager — version wins over secret
        (
            "//secretmanager.googleapis.com/projects/p/secrets/s/versions/1",
            (
                "GCPSecretManagerSecretVersion",
                "projects/p/secrets/s/versions/1",
            ),
        ),
        # Secret Manager — plain secret
        (
            "//secretmanager.googleapis.com/projects/p/secrets/s",
            ("GCPSecretManagerSecret", "projects/p/secrets/s"),
        ),
        # Artifact Registry
        (
            "//artifactregistry.googleapis.com/projects/p/locations/us/repositories/r",
            (
                "GCPArtifactRegistryRepository",
                "projects/p/locations/us/repositories/r",
            ),
        ),
        # Cloud Run service
        (
            "//run.googleapis.com/projects/p/locations/us-central1/services/svc",
            (
                "GCPCloudRunService",
                "projects/p/locations/us-central1/services/svc",
            ),
        ),
        # Compute — instance (partial_uri format)
        (
            "//compute.googleapis.com/projects/p/zones/us-central1-a/instances/vm1",
            ("GCPInstance", "projects/p/zones/us-central1-a/instances/vm1"),
        ),
        # Compute — VPC
        (
            "//compute.googleapis.com/projects/p/global/networks/default",
            ("GCPVpc", "projects/p/global/networks/default"),
        ),
        # Compute — subnet
        (
            "//compute.googleapis.com/projects/p/regions/us-central1/subnetworks/sub",
            ("GCPSubnet", "projects/p/regions/us-central1/subnetworks/sub"),
        ),
        # Compute — firewall
        (
            "//compute.googleapis.com/projects/p/global/firewalls/fw-allow-ssh",
            ("GCPFirewall", "projects/p/global/firewalls/fw-allow-ssh"),
        ),
        # Unknown service
        (
            "//bigquery.googleapis.com/projects/p/datasets/d",
            (None, None),
        ),
        # Empty suffix
        (
            "//cloudresourcemanager.googleapis.com/projects/",
            (None, None),
        ),
        # Marker absent from path
        (
            "//storage.googleapis.com/something-else/foo",
            (None, None),
        ),
    ],
)
def test_parse_full_resource_name(full_name, expected):
    assert _parse_full_resource_name(full_name) == expected
