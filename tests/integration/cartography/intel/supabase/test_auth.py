from unittest.mock import patch

import requests

import cartography.intel.supabase.auth
import tests.data.supabase.auth
from tests.integration.cartography.intel.supabase.test_organizations import (
    _ensure_local_neo4j_has_test_organizations,
)
from tests.integration.cartography.intel.supabase.test_projects import (
    _ensure_local_neo4j_has_test_projects,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_SLUG = "simpson-corp"
TEST_PROJECT_REF = "nuclearplantdbaaaaaa"
TEST_BASE_URL = "https://api.fake-supabase.com"
# A later tag, so cleanup removes the nodes loaded by earlier tests in this
# module: the integration suite shares one database per test module.
TEST_CLEANUP_UPDATE_TAG = TEST_UPDATE_TAG + 1


def _common_job_parameters():
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_SLUG": TEST_ORG_SLUG,
        "PROJECT_REF": TEST_PROJECT_REF,
    }


def _patch_auth_endpoints(func):
    """
    Patch the three GET helpers auth.sync() calls with the standard fixtures.

    Decorated tests take (mock_get, mock_sso, mock_tpa) in that order.
    """
    for decorator in (
        patch.object(
            cartography.intel.supabase.auth,
            "get",
            return_value=tests.data.supabase.auth.SUPABASE_AUTH_CONFIG,
        ),
        patch.object(
            cartography.intel.supabase.auth,
            "get_sso_providers",
            return_value=tests.data.supabase.auth.SUPABASE_SSO_PROVIDERS,
        ),
        patch.object(
            cartography.intel.supabase.auth,
            "get_third_party_auth",
            return_value=tests.data.supabase.auth.SUPABASE_THIRD_PARTY_AUTH,
        ),
    ):
        func = decorator(func)
    return func


@_patch_auth_endpoints
def test_load_supabase_auth_config(mock_get, mock_sso, mock_tpa, neo4j_session):
    """
    Ensure the curated auth config subset is loaded and attached to its project.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.auth.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    assert check_nodes(neo4j_session, "SupabaseAuthConfig", ["id"]) == {
        (f"{TEST_PROJECT_REF}/auth",),
    }

    record = neo4j_session.run(
        """
        MATCH (a:SupabaseAuthConfig {id: $id})
        RETURN a.mfa_totp_enroll_enabled AS mfa_totp,
               a.password_min_length AS password_min_length,
               a.password_hibp_enabled AS hibp,
               a.security_captcha_provider AS captcha_provider,
               a.jwt_exp AS jwt_exp,
               a.refresh_token_rotation_enabled AS rotation,
               a.site_url AS site_url,
               a.enabled_external_providers AS providers
        """,
        id=f"{TEST_PROJECT_REF}/auth",
    ).single()
    assert record["mfa_totp"] is True
    assert record["password_min_length"] == 8
    assert record["hibp"] is False
    assert record["captcha_provider"] == "hcaptcha"
    assert record["jwt_exp"] == 3600
    assert record["rotation"] is True
    assert record["site_url"] == "https://plant.simpson.corp"
    # Derived from the truthy external_*_enabled flags. `anonymous_users` is a
    # sign-up mode rather than a federated provider, so it is excluded.
    assert sorted(record["providers"]) == ["email", "github", "google"]

    assert check_rels(
        neo4j_session,
        "SupabaseAuthConfig",
        "id",
        "SupabaseProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(f"{TEST_PROJECT_REF}/auth", TEST_PROJECT_REF)}


@_patch_auth_endpoints
def test_supabase_auth_config_drops_secrets(
    mock_get, mock_sso, mock_tpa, neo4j_session
):
    """
    Ensure only the curated allowlist is ingested: the captcha secret, SMTP
    password, hook secrets and test OTP present in the response must not land.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.auth.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    record = neo4j_session.run(
        """
        MATCH (a:SupabaseAuthConfig {id: $id})
        RETURN [k IN keys(a) WHERE k IN ['security_captcha_secret', 'smtp_pass',
                'sms_test_otp', 'hook_mfa_verification_attempt_secrets',
                'mailer_subjects_invite']] AS forbidden
        """,
        id=f"{TEST_PROJECT_REF}/auth",
    ).single()
    assert record["forbidden"] == []


@_patch_auth_endpoints
def test_load_supabase_sso_providers(mock_get, mock_sso, mock_tpa, neo4j_session):
    """
    Ensure SAML providers are loaded with their routed domains.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.auth.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    assert check_nodes(neo4j_session, "SupabaseSSOProvider", ["id", "entity_id"]) == {
        ("sso-provider-1", "https://idp.simpson.corp/saml/metadata")
    }

    record = neo4j_session.run(
        """
        MATCH (p:SupabaseSSOProvider {id: 'sso-provider-1'})
        RETURN p.domains AS domains, p.name_id_format AS name_id_format
        """,
    ).single()
    assert sorted(record["domains"]) == [
        "simpson.corp",
        "springfield.simpson.corp",
    ]
    assert record["name_id_format"].endswith("emailAddress")

    assert check_rels(
        neo4j_session,
        "SupabaseSSOProvider",
        "id",
        "SupabaseProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {("sso-provider-1", TEST_PROJECT_REF)}


@_patch_auth_endpoints
def test_load_supabase_third_party_auth(mock_get, mock_sso, mock_tpa, neo4j_session):
    """
    Ensure external OIDC issuers the project trusts are loaded.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.auth.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "SupabaseThirdPartyAuthIntegration",
        ["id", "type", "oidc_issuer_url"],
    ) == {
        (
            "tpa-firebase-1",
            "firebase",
            "https://securetoken.google.com/simpson-corp",
        ),
    }

    assert check_rels(
        neo4j_session,
        "SupabaseThirdPartyAuthIntegration",
        "id",
        "SupabaseProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {("tpa-firebase-1", TEST_PROJECT_REF)}


@_patch_auth_endpoints
def test_supabase_auth_ontology_labels(mock_get, mock_sso, mock_tpa, neo4j_session):
    """
    Ensure both provider kinds carry the IdentityProvider semantic label with the
    right protocol and issuer.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.auth.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    sso = neo4j_session.run(
        """
        MATCH (p:SupabaseSSOProvider:IdentityProvider {id: 'sso-provider-1'})
        RETURN p._ont_protocol AS protocol,
               p._ont_issuer AS issuer,
               p._ont_source AS source
        """,
    ).single()
    assert sso["protocol"] == "SAML"
    assert sso["issuer"] == "https://idp.simpson.corp/saml/metadata"
    assert sso["source"] == "supabase"

    tpa = neo4j_session.run(
        """
        MATCH (p:SupabaseThirdPartyAuthIntegration:IdentityProvider
               {id: 'tpa-firebase-1'})
        RETURN p._ont_protocol AS protocol, p._ont_issuer AS issuer
        """,
    ).single()
    assert tpa["protocol"] == "OIDC"
    assert tpa["issuer"] == "https://securetoken.google.com/simpson-corp"


def test_supabase_auth_unavailable_keeps_existing_inventory(neo4j_session):
    """
    A tolerated status must not delete the auth inventory already in the graph.

    SSO is plan-gated, so this is the realistic regression: losing the entitlement
    must not erase the record of which identity providers a project trusts.
    """
    # Arrange: a successful sync first, so there is real inventory to protect.
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)
    with (
        patch.object(
            cartography.intel.supabase.auth,
            "get",
            return_value=tests.data.supabase.auth.SUPABASE_AUTH_CONFIG,
        ),
        patch.object(
            cartography.intel.supabase.auth,
            "get_sso_providers",
            return_value=tests.data.supabase.auth.SUPABASE_SSO_PROVIDERS,
        ),
        patch.object(
            cartography.intel.supabase.auth,
            "get_third_party_auth",
            return_value=tests.data.supabase.auth.SUPABASE_THIRD_PARTY_AUTH,
        ),
    ):
        cartography.intel.supabase.auth.sync(
            neo4j_session,
            api_session,
            _common_job_parameters(),
        )
    config_before = check_nodes(neo4j_session, "SupabaseAuthConfig", ["id"])
    sso_before = check_nodes(neo4j_session, "SupabaseSSOProvider", ["id"])
    tpa_before = check_nodes(
        neo4j_session,
        "SupabaseThirdPartyAuthIntegration",
        ["id"],
    )
    assert config_before and sso_before and tpa_before, "arrange should load all three"

    # Act: all three endpoints go unavailable, on a later update tag so a cleanup
    # would consider every existing node stale and delete it.
    with (
        patch.object(cartography.intel.supabase.auth, "get", return_value=None),
        patch.object(
            cartography.intel.supabase.auth, "get_sso_providers", return_value=None
        ),
        patch.object(
            cartography.intel.supabase.auth, "get_third_party_auth", return_value=None
        ),
    ):
        cartography.intel.supabase.auth.sync(
            neo4j_session,
            api_session,
            {**_common_job_parameters(), "UPDATE_TAG": TEST_CLEANUP_UPDATE_TAG},
        )

    # Assert: nothing was deleted.
    assert check_nodes(neo4j_session, "SupabaseAuthConfig", ["id"]) == config_before
    assert check_nodes(neo4j_session, "SupabaseSSOProvider", ["id"]) == sso_before
    assert (
        check_nodes(neo4j_session, "SupabaseThirdPartyAuthIntegration", ["id"])
        == tpa_before
    )
