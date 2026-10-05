"""DISA Security Technical Implementation Guide (STIG) framework helpers.

STIG requirements are keyed by their Vulnerability ID (e.g. ``V-273188``), which
stays stable across rule revisions, rather than by the ``SV-...`` rule ID that
changes on every edit.
"""

from cartography.rules.spec.model import Framework

STIG_FRAMEWORK_SHORT_NAME = "STIG"

STIG_OKTA_FRAMEWORK_NAME = "DISA Okta Identity as a Service (IDaaS) STIG"
STIG_OKTA_SCOPE = "okta"
STIG_OKTA_REVISION = "V1R2"

STIG_OKTA_CONTROL_TITLES = {
    "V-273188": "Okta must automatically disable accounts after a 35-day period of account inactivity.",
    "V-273205": "The Okta Verify application must be configured to connect only to FIPS-compliant devices.",
}


def _control_title(requirement: str, titles: dict[str, str]) -> str | None:
    # Vulnerability IDs are published upper-case; tolerate caller casing/spacing.
    return titles.get(requirement.strip().upper())


def stig_okta(requirement: str, control_title: str | None = None) -> Framework:
    return Framework(
        name=STIG_OKTA_FRAMEWORK_NAME,
        short_name=STIG_FRAMEWORK_SHORT_NAME,
        scope=STIG_OKTA_SCOPE,
        revision=STIG_OKTA_REVISION,
        requirement=requirement,
        control_title=control_title
        or _control_title(requirement, STIG_OKTA_CONTROL_TITLES),
    )
