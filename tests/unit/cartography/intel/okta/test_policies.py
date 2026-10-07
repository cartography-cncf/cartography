import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.okta.policies
from cartography.intel.okta.common import OktaApiError
from cartography.intel.okta.policies import _transform_okta_policies
from cartography.intel.okta.policies import _transform_okta_policy_rules
from tests.data.okta.policies import AUTHENTICATOR_ENROLLMENT_POLICY
from tests.data.okta.policies import DEFAULT_ACCESS_POLICY
from tests.data.okta.policies import PASSWORD_POLICY_STRONG
from tests.data.okta.policies import POLICIES_BY_TYPE
from tests.data.okta.policies import RULES_BY_POLICY


def _rule(rule_id: str) -> dict:
    rules = _transform_okta_policy_rules(RULES_BY_POLICY)
    return next(rule for rule in rules if rule["id"] == rule_id)


def test_transform_password_policy_settings() -> None:
    # Act
    (policy,) = _transform_okta_policies([PASSWORD_POLICY_STRONG], {}, {})

    # Assert
    assert policy["auth_provider"] == "OKTA"
    assert policy["group_include_ids"] == ["00g-everyone"]
    assert policy["group_exclude_ids"] == []
    assert {
        key: policy[key]
        for key in (
            "password_min_length",
            "password_min_lowercase",
            "password_min_uppercase",
            "password_min_number",
            "password_min_symbol",
            "password_exclude_username",
            "password_exclude_attributes",
            "password_common_password_check",
            "password_max_age_days",
            "password_expire_warn_days",
            "password_min_age_minutes",
            "password_history_count",
            "lockout_max_attempts",
            "lockout_auto_unlock_minutes",
            "lockout_show_failures",
            "lockout_notification_channels",
        )
    } == {
        "password_min_length": 15,
        "password_min_lowercase": 1,
        "password_min_uppercase": 1,
        "password_min_number": 1,
        "password_min_symbol": 1,
        "password_exclude_username": True,
        "password_exclude_attributes": ["firstName", "lastName"],
        "password_common_password_check": True,
        "password_max_age_days": 60,
        "password_expire_warn_days": 7,
        "password_min_age_minutes": 1440,
        "password_history_count": 5,
        "lockout_max_attempts": 3,
        "lockout_auto_unlock_minutes": 15,
        "lockout_show_failures": False,
        "lockout_notification_channels": ["EMAIL"],
    }
    assert policy["application_ids"] == []
    assert policy["enrollment_required_authenticators"] == []


def test_transform_enrollment_policy_authenticators() -> None:
    # Act
    (policy,) = _transform_okta_policies([AUTHENTICATOR_ENROLLMENT_POLICY], {}, {})

    # Assert
    assert policy["enrollment_required_authenticators"] == ["okta_verify"]
    assert policy["enrollment_optional_authenticators"] == ["webauthn"]
    assert policy["enrollment_disabled_authenticators"] == ["phone_number"]
    assert policy["password_min_length"] is None


def test_transform_access_policy_apps() -> None:
    # Act
    (policy,) = _transform_okta_policies(
        [DEFAULT_ACCESS_POLICY],
        {"rst-default": ["0oa-slack", "0oa-admin-console"]},
        {"0oa-admin-console": "saasure"},
    )

    # Assert
    assert policy["application_ids"] == ["0oa-slack", "0oa-admin-console"]
    assert policy["first_party_app_names"] == ["saasure"]
    assert policy["conditions"] is None


def test_transform_global_session_rule() -> None:
    rule = _rule("0pr-session-hardened")

    assert rule["policy_id"] == "00p-global-session"
    assert rule["user_exclude_ids"] == ["00u-breakglass"]
    assert rule["network_connection"] == "ZONE"
    assert rule["network_include_zone_ids"] == ["nzo-corp"]
    assert rule["access"] == "ALLOW"
    assert rule["require_factor"] is True
    assert rule["session_max_idle_minutes"] == 15
    assert rule["session_max_lifetime_minutes"] == 1080
    assert rule["session_use_persistent_cookie"] is False
    assert rule["factor_mode"] is None
    assert rule["phishing_resistant_required"] is None


def test_transform_access_policy_rule_constraints() -> None:
    cases = {
        "rul-admin-phishing-resistant": True,
        # Catch-all has no constraints at all.
        "rul-admin-catch-all": False,
        "rul-dashboard-one-factor": False,
        # One alternative allows a knowledge-only path.
        "rul-default-mixed": False,
    }

    for rule_id, required in cases.items():
        rule = _rule(rule_id)
        assert rule["phishing_resistant_required"] is required, rule_id
        assert rule["hardware_protection_required"] is required, rule_id
        assert rule["device_bound_required"] is required, rule_id
        assert rule["verification_constraints"] is not None, rule_id


def test_transform_password_and_enrollment_rule_actions() -> None:
    password_rule = _rule("0pr-password-default")
    enrollment_rule = _rule("0pr-enrollment-default")
    profile_rule = _rule("rul-profile-enrollment")

    assert password_rule["password_change_access"] == "ALLOW"
    assert password_rule["self_service_password_reset_access"] == "ALLOW"
    assert password_rule["self_service_unlock_access"] == "DENY"
    assert enrollment_rule["enroll_self"] == "CHALLENGE"
    assert profile_rule["access"] == "DENY"


@patch.object(cartography.intel.okta.policies, "collect_raw_paginated")
def test_get_policies_skips_identity_engine_types_on_classic_orgs(mock_collect):
    # Arrange
    async def _collect(okta_client, path, params=None):
        if params["type"] in {"ACCESS_POLICY", "PROFILE_ENROLLMENT"}:
            raise OktaApiError(path, SimpleNamespace(error_code="E0000001"))
        return POLICIES_BY_TYPE[params["type"]]

    mock_collect.side_effect = _collect

    # Act
    policies = asyncio.run(
        cartography.intel.okta.policies._get_okta_policies(MagicMock()),
    )

    # Assert
    assert {policy["type"] for policy in policies} == {
        "OKTA_SIGN_ON",
        "PASSWORD",
        "MFA_ENROLL",
    }


@patch.object(cartography.intel.okta.policies, "collect_raw_paginated")
def test_get_policies_raises_other_errors(mock_collect):
    mock_collect.side_effect = OktaApiError(
        "/api/v1/policies",
        SimpleNamespace(error_code="E0000006"),
    )

    with pytest.raises(OktaApiError):
        asyncio.run(cartography.intel.okta.policies._get_okta_policies(MagicMock()))


@patch.object(cartography.intel.okta.policies, "_get_okta_first_party_app_names")
@patch.object(cartography.intel.okta.policies, "collect_raw_paginated")
def test_get_policy_data_drops_policies_deleted_mid_sync(mock_collect, mock_names):
    # Arrange: both policies are listed, then deleted before their rules or
    # app mappings are read.
    async def _collect(okta_client, path, params=None):
        if path == "/api/v1/policies":
            return POLICIES_BY_TYPE[params["type"]]
        if path in {
            "/api/v1/policies/00p-password-legacy/rules",
            "/api/v1/policies/rst-dashboard/mappings",
        }:
            raise OktaApiError(path, SimpleNamespace(error_code="E0000007"))
        return []

    async def _names(okta_client, app_ids):
        return {}

    mock_collect.side_effect = _collect
    mock_names.side_effect = _names

    # Act
    policies, rules_by_policy, app_ids_by_policy, _ = asyncio.run(
        cartography.intel.okta.policies._get_okta_policy_data(MagicMock(), set()),
    )

    # Assert
    policy_ids = {policy["id"] for policy in policies}
    assert "00p-password-legacy" not in policy_ids
    assert "rst-dashboard" not in policy_ids
    assert set(rules_by_policy) == policy_ids
    assert "rst-dashboard" not in app_ids_by_policy
