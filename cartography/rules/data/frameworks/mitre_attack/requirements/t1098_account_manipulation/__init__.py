from cartography.rules.data.frameworks.mitre_attack.requirements.t1098_account_manipulation.delegation_boundary_modifiable import (
    delegation_boundary_modifiable,
)
from cartography.rules.data.frameworks.mitre_attack.requirements.t1098_account_manipulation.identity_administration_privileges import (
    identity_administration_privileges,
)
from cartography.rules.data.frameworks.mitre_attack.requirements.t1098_account_manipulation.policy_administration_privileges import (
    policy_administration_privileges,
)
from cartography.rules.data.frameworks.mitre_attack.requirements.t1098_account_manipulation.workload_identity_admin_capabilities import (
    workload_identity_admin_capabilities,
)
from cartography.rules.spec.model import Requirement

t1098 = Requirement(
    id="t1098",
    name="Account Manipulation",
    description=(
        "Adversaries may manipulate accounts to maintain or elevate access to victim systems. "
        "Activity that subverts security policies. For example in cloud this is "
        "updating IAM policies or adding new global admins."
    ),
    target_assets="Identities that can manipulate other identities",
    findings=(
        policy_administration_privileges,
        identity_administration_privileges,
        delegation_boundary_modifiable,
        workload_identity_admin_capabilities,
    ),
    requirement_url="https://attack.mitre.org/techniques/T1098/",
    attributes={
        "tactic": "persistence,privilege_escalation",
        "technique_id": "T1098",
        "services": [
            "iam",
            "sts",
            "ec2",
            "lambda",
        ],
        "providers": ["AWS"],
    },
)
