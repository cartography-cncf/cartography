"""NIST AI RMF framework helpers."""

from cartography.rules.spec.model import Framework

NIST_AI_RMF_FRAMEWORK_NAME = "NIST AI Risk Management Framework"
NIST_AI_RMF_SHORT_NAME = "NIST-AI-RMF"
NIST_AI_RMF_REVISION = "1.0"

NIST_AI_RMF_CONTROL_TITLES = {
    "govern 1": "Policies, processes, procedures, and practices across the organization related to the mapping, measuring, and managing of AI risks are in place, transparent, and implemented effectively",
    "govern 5": "Processes are in place for robust engagement with relevant AI actors",
    "manage 2": "Strategies to maximize AI benefits and minimize negative impacts are planned, prepared, implemented, documented, and informed by input from relevant AI actors",
    "map 1": "Context is established and understood",
    "measure 2": "AI systems are evaluated for trustworthy characteristics",
}


def nist_ai_rmf(requirement: str, control_title: str | None = None) -> Framework:
    normalized_requirement = requirement.strip().lower()
    return Framework(
        name=NIST_AI_RMF_FRAMEWORK_NAME,
        short_name=NIST_AI_RMF_SHORT_NAME,
        requirement=requirement,
        revision=NIST_AI_RMF_REVISION,
        control_title=control_title
        or NIST_AI_RMF_CONTROL_TITLES.get(normalized_requirement),
    )
