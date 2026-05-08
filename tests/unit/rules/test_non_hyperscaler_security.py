from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.device_security_posture_gaps import (
    device_security_posture_gaps,
)
from cartography.rules.data.rules.identity_mfa_gaps import identity_mfa_gaps
from cartography.rules.data.rules.tailscale_security_configuration_gaps import (
    tailscale_security_configuration_gaps,
)
from cartography.rules.spec.model import Module

NON_HYPERSCALER_RULES = [
    identity_mfa_gaps,
    tailscale_security_configuration_gaps,
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
    assert {fact.module for fact in tailscale_security_configuration_gaps.facts} == {
        Module.TAILSCALE,
    }


def test_device_security_posture_gaps_cover_expected_providers():
    assert {fact.module for fact in device_security_posture_gaps.facts} == {
        Module.DUO,
        Module.JAMF,
        Module.TAILSCALE,
    }
