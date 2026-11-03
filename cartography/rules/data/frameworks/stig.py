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
    "V-273186": "Okta must log out a session after a 15-minute period of inactivity.",
    "V-273187": "The Okta Admin Console must log out a session after a 15-minute period of inactivity.",
    "V-273188": "Okta must automatically disable accounts after a 35-day period of account inactivity.",
    "V-273189": "Okta must enforce the limit of three consecutive invalid login attempts by a user during a 15-minute time period.",
    "V-273190": "The Okta Dashboard application must be configured to allow authentication only via non-phishable authenticators.",
    "V-273191": "The Okta Admin Console application must be configured to allow authentication only via non-phishable authenticators.",
    "V-273193": "The Okta Admin Console application must be configured to use multifactor authentication.",
    "V-273194": "The Okta Dashboard application must be configured to use multifactor authentication.",
    "V-273195": "Okta must enforce a minimum 15-character password length.",
    "V-273196": "Okta must enforce password complexity by requiring that at least one uppercase character be used.",
    "V-273197": "Okta must enforce password complexity by requiring that at least one lowercase character be used.",
    "V-273198": "Okta must enforce password complexity by requiring that at least one numeric character be used.",
    "V-273199": "Okta must enforce password complexity by requiring that at least one special character be used.",
    "V-273200": "Okta must enforce 24 hours/one day as the minimum password lifetime.",
    "V-273201": "Okta must enforce a 60-day maximum password lifetime restriction.",
    "V-273202": "Okta must off-load audit records onto a central log server.",
    "V-273203": "Okta must be configured to limit the global session lifetime to 18 hours.",
    "V-273205": "The Okta Verify application must be configured to connect only to FIPS-compliant devices.",
    "V-273206": "Okta must be configured to disable persistent global session cookies.",
    "V-273208": "Okta must validate passwords against a list of commonly used, expected, or compromised passwords.",
    "V-273209": "Okta must prohibit password reuse for a minimum of five generations.",
    "V-279689": "Okta API tokens must be configured with Network Zones to restrict authorization from known networks.",
    "V-279690": "Okta API tokens must be created under new dedicated user accounts.",
    "V-279691": "The Okta Global Session policy must be configured to allow or deny IP based access in accordance with the Access Control policy for Okta.",
    "V-279692": "Okta must be configured with Network Zones defined to block anonymized proxies according to organizationally defined policy.",
    "V-279693": "For each application integrated with Okta, network zones must be defined in its authentication policy.",
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
