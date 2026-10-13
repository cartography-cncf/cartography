import pytest

import cartography.intel.gcp.policy_bindings
import cartography.intel.gcp.workload_identity
import tests.data.gcp.workload_identity as wif_data

TEST_PROJECT_ID = "project-abc"


def test_transform_providers_marks_disabled_as_not_enabled():
    """
    An ACTIVE-but-disabled provider must report enabled=false so cross-
    provider IdentityProvider queries do not see it as active.
    """
    pool = {
        "name": "projects/p/locations/global/workloadIdentityPools/x",
        "state": "ACTIVE",
        "disabled": False,
    }
    raw = [
        {
            "name": "providers/active-enabled",
            "state": "ACTIVE",
            "disabled": False,
            "oidc": {"issuerUri": "https://example"},
        },
        {
            "name": "providers/active-disabled",
            "state": "ACTIVE",
            "disabled": True,
            "oidc": {"issuerUri": "https://example"},
        },
        {
            "name": "providers/deleted",
            "state": "DELETED",
            "disabled": False,
            "oidc": {"issuerUri": "https://example"},
        },
    ]
    transformed = cartography.intel.gcp.workload_identity.transform_providers(
        raw, pool, "p"
    )
    by_id = {p["id"]: p for p in transformed}
    assert by_id["providers/active-enabled"]["enabled"] is True
    assert by_id["providers/active-disabled"]["enabled"] is False
    assert by_id["providers/deleted"]["enabled"] is False


def test_transform_providers_disabled_pool_disables_all_providers():
    """
    A disabled pool blocks federation entirely. Even an ACTIVE+enabled
    provider under a disabled pool must report enabled=false.
    """
    disabled_pool = {
        "name": "projects/p/locations/global/workloadIdentityPools/x",
        "state": "ACTIVE",
        "disabled": True,
    }
    deleted_pool = {
        "name": "projects/p/locations/global/workloadIdentityPools/y",
        "state": "DELETED",
        "disabled": False,
    }
    raw = [
        {
            "name": "providers/active-enabled",
            "state": "ACTIVE",
            "disabled": False,
            "oidc": {"issuerUri": "https://example"},
        },
    ]
    for pool in (disabled_pool, deleted_pool):
        transformed = cartography.intel.gcp.workload_identity.transform_providers(
            raw, pool, "p"
        )
        assert transformed[0]["enabled"] is False


def test_detect_protocol_handles_x509():
    """
    GCP also supports X509 (mTLS) providers. They must be classified so the
    ontology mapping carries the right protocol instead of None.
    """
    fn = cartography.intel.gcp.workload_identity._detect_protocol
    assert fn({"oidc": {}}) == "OIDC"
    assert fn({"aws": {}}) == "AWS"
    assert fn({"saml": {}}) == "SAML"
    assert fn({"x509": {"trustStore": {"trustAnchors": []}}}) == "X509"
    assert fn({}) is None


def test_transform_providers_classifies_x509_provider():
    """
    An x509 provider should land in the graph with protocol="X509" and
    inherit the pool-driven enabled flag, even though no issuer URI exists.
    """
    pool = {
        "name": "projects/p/locations/global/workloadIdentityPools/x",
        "state": "ACTIVE",
        "disabled": False,
    }
    raw = [
        {
            "name": "projects/p/locations/global/workloadIdentityPools/x/providers/mtls",
            "state": "ACTIVE",
            "disabled": False,
            "x509": {"trustStore": {"trustAnchors": [{"pemCertificate": "..."}]}},
        },
    ]
    transformed = cartography.intel.gcp.workload_identity.transform_providers(
        raw, pool, "p"
    )
    assert transformed[0]["protocol"] == "X509"
    assert transformed[0]["enabled"] is True
    assert transformed[0]["oidcIssuerUri"] is None


@pytest.mark.parametrize(
    "wif_member",
    wif_data.WIF_BINDING_MEMBERS,
    ids=["principal", "principalSet"],
)
def test_transform_bindings_extracts_wif_pools(wif_member):
    """
    The policy binding transformer should extract the pool resource name from
    both ``principal://`` and ``principalSet://`` URIs and skip the per-subject
    detail.
    """
    raw = {
        "project_id": TEST_PROJECT_ID,
        "policy_results": [
            {
                "policies": [
                    {
                        "attached_resource": (
                            f"//cloudresourcemanager.googleapis.com/projects/{TEST_PROJECT_ID}"
                        ),
                        "policy": {
                            "bindings": [
                                {
                                    "role": "roles/iam.workloadIdentityUser",
                                    "members": [
                                        "serviceAccount:sa@example.iam.gserviceaccount.com",
                                        wif_member,
                                    ],
                                },
                            ],
                        },
                    },
                ],
            },
        ],
    }
    bindings = cartography.intel.gcp.policy_bindings.transform_bindings(raw)
    assert len(bindings) == 1
    binding = bindings[0]
    assert binding["wif_pools"] == [wif_data.WIF_GITHUB_POOL_ID]
    assert binding["members"] == ["sa@example.iam.gserviceaccount.com"]
