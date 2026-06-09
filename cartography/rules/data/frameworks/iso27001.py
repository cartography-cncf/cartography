"""ISO/IEC 27001:2022 Annex A framework helpers.

Cartography exposes this as framework short name "ISO27001". The requirement
identifiers below are Annex A control identifiers from ISO/IEC 27001:2022,
which are derived from and aligned with ISO/IEC 27002:2022 controls.
"""

from cartography.rules.spec.model import Framework

ISO27001_FRAMEWORK_NAME = "ISO/IEC 27001:2022 Annex A"
ISO27001_SHORT_NAME = "ISO27001"
ISO27001_REVISION = "2022"

ISO27001_ANNEX_A_TITLES = {
    "5.9": "Inventory of information and other associated assets",
    "5.15": "Access control",
    "5.16": "Identity management",
    "5.17": "Authentication information",
    "5.18": "Access rights",
    "5.21": "Managing information security in the ICT supply chain",
    "5.23": "Information security for use of cloud services",
    "8.1": "User endpoint devices",
    "8.2": "Privileged access rights",
    "8.3": "Information access restriction",
    "8.5": "Secure authentication",
    "8.8": "Management of technical vulnerabilities",
    "8.9": "Configuration management",
    "8.10": "Information deletion",
    "8.12": "Data leakage prevention",
    "8.13": "Information backup",
    "8.15": "Logging",
    "8.16": "Monitoring activities",
    "8.20": "Network security",
    "8.22": "Segregation of networks",
    "8.24": "Use of cryptography",
    "8.28": "Secure coding",
    "8.32": "Change management",
}


def iso27001_annex_a(requirement: str, control_title: str | None = None) -> Framework:
    normalized_requirement = requirement.strip().lower()
    return Framework(
        name=ISO27001_FRAMEWORK_NAME,
        short_name=ISO27001_SHORT_NAME,
        revision=ISO27001_REVISION,
        requirement=requirement,
        control_title=control_title
        or ISO27001_ANNEX_A_TITLES.get(normalized_requirement),
    )
