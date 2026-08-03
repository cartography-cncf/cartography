"""AICPA SOC 2 Trust Services Criteria framework helpers.

Cartography exposes this framework as ``soc2:tsc:2022``. The criteria are from
the 2017 Trust Services Criteria; the 2022 update revised the points of focus
without changing the criteria themselves, so the revision filter tracks the 2022
edition while the criteria identifiers stay those of 2017.
"""

from cartography.rules.spec.model import Framework

SOC2_FRAMEWORK_NAME = "SOC 2: Trust Services Criteria"
SOC2_SHORT_NAME = "SOC2"
SOC2_SCOPE = "TSC"
SOC2_REVISION = "2022"

# Only declare a criterion here once at least one rule maps to it. Criteria that
# no rule covers stay out of this lookup; the coverage gap is tracked with a
# ``# TODO: SOC 2 <criterion>:`` comment in the closest rule file instead.
SOC2_TSC_TITLES = {
    "a1.2": (
        "The entity authorizes, designs, develops or acquires, implements, "
        "operates, approves, maintains, and monitors environmental protections, "
        "software, data backup processes, and recovery infrastructure to meet "
        "its objectives."
    ),
    "cc6.1": (
        "The entity implements logical access security software, infrastructure, "
        "and architectures over protected information assets to protect them "
        "from security events to meet the entity's objectives."
    ),
    "cc6.2": (
        "Prior to issuing system credentials and granting system access, the "
        "entity registers and authorizes new internal and external users whose "
        "access is administered by the entity. For those users whose access is "
        "administered by the entity, user system credentials are removed when "
        "user access is no longer authorized."
    ),
    "cc6.3": (
        "The entity authorizes, modifies, or removes access to data, software, "
        "functions, and other protected information assets based on roles, "
        "responsibilities, or the system design and changes, giving consideration "
        "to the concepts of least privilege and segregation of duties, to meet "
        "the entity's objectives."
    ),
    "cc6.6": (
        "The entity implements logical access security measures to protect "
        "against threats from sources outside its system boundaries."
    ),
    "cc6.7": (
        "The entity restricts the transmission, movement, and removal of "
        "information to authorized internal and external users and processes, and "
        "protects it during transmission, movement, or removal to meet the "
        "entity's objectives."
    ),
    "cc6.8": (
        "The entity implements controls to prevent or detect and act upon the "
        "introduction of unauthorized or malicious software to meet the "
        "entity's objectives."
    ),
    "cc7.1": (
        "To meet its objectives, the entity uses detection and monitoring "
        "procedures to identify (1) changes to configurations that result in the "
        "introduction of new vulnerabilities, and (2) susceptibilities to newly "
        "discovered vulnerabilities."
    ),
    "cc7.2": (
        "The entity monitors system components and the operation of those "
        "components for anomalies that are indicative of malicious acts, natural "
        "disasters, and errors affecting the entity's ability to meet its "
        "objectives; anomalies are analyzed to determine whether they represent "
        "security events."
    ),
    "cc9.2": (
        "The entity assesses and manages risks associated with vendors and "
        "business partners."
    ),
}

# Coverage-gap index. Each criterion below is detailed in a
# ``# TODO: SOC 2 <criterion>:`` block in the rule file closest to its subject,
# so grep that pattern under cartography/rules/data/rules/ for the specifics.
# "uncovered" means no rule maps to it; "partial" means rules map to it but only
# reach part of what the criterion asks for.
#   uncovered: A1.1, A1.3, C1.1, C1.2, CC6.5, CC7.3, CC7.4, CC7.5
#   partial: A1.2, CC6.7, CC6.8, CC7.2
# tests/unit/rules/test_soc2_mappings.py keeps this index honest.


def soc2_tsc(requirement: str, control_title: str | None = None) -> Framework:
    """Build a SOC 2 Trust Services Criteria framework mapping."""
    normalized_requirement = requirement.strip().lower()
    return Framework(
        name=SOC2_FRAMEWORK_NAME,
        short_name=SOC2_SHORT_NAME,
        scope=SOC2_SCOPE,
        revision=SOC2_REVISION,
        requirement=requirement,
        control_title=control_title or SOC2_TSC_TITLES.get(normalized_requirement),
    )
