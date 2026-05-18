"""NIST AI RMF framework helpers."""

from cartography.rules.spec.model import Framework

NIST_AI_RMF_FRAMEWORK_NAME = "NIST AI Risk Management Framework"
NIST_AI_RMF_SHORT_NAME = "NIST-AI-RMF"
NIST_AI_RMF_REVISION = "1.0"


def nist_ai_rmf(requirement: str) -> Framework:
    return Framework(
        name=NIST_AI_RMF_FRAMEWORK_NAME,
        short_name=NIST_AI_RMF_SHORT_NAME,
        requirement=requirement,
        revision=NIST_AI_RMF_REVISION,
    )
