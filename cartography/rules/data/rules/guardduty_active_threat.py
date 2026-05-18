from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# GuardDuty finding "type" strings follow the pattern
# `ThreatPurpose:ResourceTypeAffected/ThreatFamilyName.DetectionMechanism!Artifact`.
# The ThreatPurpose prefixes below describe categories where the finding is
# action-indicative: GuardDuty is reporting evidence of active compromise or
# attacker activity (rather than reconnaissance or policy drift).
_ACTIVE_THREAT_PREFIXES = (
    "Backdoor:",
    "CryptoCurrency:",
    "Exfiltration:",
    "Impact:",
    "Trojan:",
    "UnauthorizedAccess:",
)

_ACTIVE_THREAT_WHERE = " OR ".join(
    f"f.type STARTS WITH '{prefix}'" for prefix in _ACTIVE_THREAT_PREFIXES
)

aws_guardduty_active_threat = Fact(
    id="aws_guardduty_active_threat",
    name="GuardDuty Active Threat Finding",
    description=(
        "Finds high-severity, unarchived GuardDuty findings whose type "
        "ThreatPurpose belongs to an action-indicative category "
        "(Backdoor, CryptoCurrency, Exfiltration, Impact, Trojan, "
        "UnauthorizedAccess). These represent evidence of an active "
        "compromise or attacker activity rather than reconnaissance."
    ),
    cypher_query=f"""
    MATCH (a:AWSAccount)-[:RESOURCE]->(f:GuardDutyFinding)
    WHERE f.severity >= 7
      AND coalesce(f.archived, false) = false
      AND ({_ACTIVE_THREAT_WHERE})
    RETURN
        f.id AS finding_id,
        f.arn AS finding_arn,
        f.title AS title,
        f.type AS type,
        f.severity AS severity,
        f.region AS region,
        f.resource_type AS resource_type,
        f.resource_id AS resource_id,
        a.id AS account_id,
        a.name AS account_name
    ORDER BY f.severity DESC, f.eventlastseen DESC
    """,
    cypher_visual_query=f"""
    MATCH (a:AWSAccount)-[:RESOURCE]->(f:GuardDutyFinding)
    WHERE f.severity >= 7
      AND coalesce(f.archived, false) = false
      AND ({_ACTIVE_THREAT_WHERE})
    RETURN *
    """,
    # Denominator: all live GuardDutyFinding nodes (unarchived). The runner
    # computes `passing = total - failing`, so this must count the full
    # evaluated population, not the failing subset.
    cypher_count_query="""
    MATCH (:AWSAccount)-[:RESOURCE]->(f:GuardDutyFinding)
    WHERE coalesce(f.archived, false) = false
    RETURN COUNT(f) AS count
    """,
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


class GuardDutyActiveThreat(Finding):
    finding_id: str | None = None
    finding_arn: str | None = None
    title: str | None = None
    type: str | None = None
    severity: float | None = None
    region: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    account_id: str | None = None
    account_name: str | None = None


guardduty_active_threat = Rule(
    id="guardduty_active_threat",
    name="GuardDuty Active Threat",
    description=(
        "Surfaces high-severity GuardDuty findings that indicate an active "
        "compromise (Backdoor, CryptoCurrency, Exfiltration, Impact, Trojan, "
        "UnauthorizedAccess). These findings are strong signals of attacker "
        "activity in the environment and should be triaged immediately."
    ),
    output_model=GuardDutyActiveThreat,
    tags=(
        "active_threat",
        "guardduty",
        "stride:tampering",
        "stride:information_disclosure",
        "stride:elevation_of_privilege",
    ),
    facts=(aws_guardduty_active_threat,),
    version="0.1.0",
)
