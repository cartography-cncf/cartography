from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.device_security_posture_gaps import (
    device_security_posture_gaps,
)
from cartography.rules.data.rules.identity_mfa_gaps import identity_mfa_gaps
from cartography.rules.data.rules.tailscale_security_configuration_gaps import (
    tailscale_device_auto_updates_disabled,
)
from cartography.rules.data.rules.tailscale_security_configuration_gaps import (
    tailscale_device_key_expiry_disabled,
)
from cartography.rules.data.rules.tailscale_security_configuration_gaps import (
    tailscale_network_flow_logging_disabled,
)
from cartography.rules.data.rules.tailscale_security_configuration_gaps import (
    tailscale_tailnet_approval_disabled,
)
from cartography.rules.spec.model import Module

NON_HYPERSCALER_RULES = [
    identity_mfa_gaps,
    tailscale_tailnet_approval_disabled,
    tailscale_network_flow_logging_disabled,
    tailscale_device_auto_updates_disabled,
    tailscale_device_key_expiry_disabled,
    device_security_posture_gaps,
]


def test_non_hyperscaler_rules_are_registered():
    for rule in NON_HYPERSCALER_RULES:
        assert RULES[rule.id] is rule


def test_non_hyperscaler_rules_have_iso27001_mappings():
    for rule in NON_HYPERSCALER_RULES:
        assert rule.has_framework(short_name="27001", revision="2022")


def test_identity_mfa_gaps_cover_expected_providers():
    assert {fact.module for fact in identity_mfa_gaps.facts} == {
        Module.CLOUDFLARE,
        Module.DUO,
        Module.JUMPCLOUD,
        Module.LASTPASS,
    }


def test_tailscale_security_configuration_gaps_are_tailscale_only():
    for rule in (
        tailscale_tailnet_approval_disabled,
        tailscale_network_flow_logging_disabled,
        tailscale_device_auto_updates_disabled,
        tailscale_device_key_expiry_disabled,
    ):
        assert {fact.module for fact in rule.facts} == {Module.TAILSCALE}


def test_device_security_posture_gaps_cover_expected_providers():
    assert {fact.module for fact in device_security_posture_gaps.facts} == {
        Module.DUO,
        Module.JAMF,
        Module.TAILSCALE,
    }


def test_tailscale_boolean_predicates_accept_string_values():
    for rule in (
        tailscale_tailnet_approval_disabled,
        tailscale_network_flow_logging_disabled,
        tailscale_device_auto_updates_disabled,
        tailscale_device_key_expiry_disabled,
    ):
        for fact in rule.facts:
            assert "toLower(toString(" in fact.cypher_query
            assert "toLower(toString(" in fact.cypher_visual_query


def test_duo_phone_visual_query_keeps_unlinked_phones():
    duo_phone_fact = next(
        fact
        for fact in device_security_posture_gaps.facts
        if fact.id == "duo_phone_posture_gaps"
    )

    assert "MATCH (phone:DuoPhone)" in duo_phone_fact.cypher_visual_query
    assert "OPTIONAL MATCH p=(user:DuoUser)-[:HAS_DUO_PHONE]->(phone)" in (
        duo_phone_fact.cypher_visual_query
    )
