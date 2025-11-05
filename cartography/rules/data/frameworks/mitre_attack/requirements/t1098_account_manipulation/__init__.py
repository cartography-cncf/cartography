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
