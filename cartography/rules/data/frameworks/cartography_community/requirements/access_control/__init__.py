from itertools import chain
from cartography.rules.spec.model import Requirement
from cartography.rules.data.frameworks.cartography_community.requirements.access_control.mfa_missing import (
    missing_mfa_finding,
)
from cartography.rules.data.frameworks.cartography_community.requirements.access_control.unmanaged_account import (
    unmanaged_account,
)

all_findings = (
    missing_mfa_finding,
    unmanaged_account,
)


cc_001 = Requirement(
    id="CC_001",
    name="Accounts have proper access controls",
    description=(
        "Ensure that proper access controls are in place for all accounts, including "
        "the use of Multi-Factor Authentication (MFA) to enhance security."
    ),
    target_assets="All user accounts in the environment.",
    findings=all_findings,
    attributes={
        "providers": [chain.from_iterable(finding.modules for finding in all_findings)],
    },
)
