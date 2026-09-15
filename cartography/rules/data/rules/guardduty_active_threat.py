from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.data.frameworks.soc2 import soc2_tsc
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
    MATCH (a:AWSAccount)-[:RESOURCE]->(f:AWSGuardDutyFinding)
    WHERE f.severity >= 7
      AND coalesce(f.archived, false) = false
      AND coalesce(f.sample, false) = false
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
    MATCH (a:AWSAccount)-[:RESOURCE]->(f:AWSGuardDutyFinding)
    WHERE f.severity >= 7
      AND coalesce(f.archived, false) = false
      AND coalesce(f.sample, false) = false
      AND ({_ACTIVE_THREAT_WHERE})
    RETURN *
    """,
    # Denominator: all live AWSGuardDutyFinding nodes (unarchived, non-sample). The
    # runner computes `passing = total - failing`, so this must count the full
    # evaluated population, not the failing subset. Sample findings are excluded
    # here too so they never count toward the pass rate.
    cypher_count_query="""
    MATCH (:AWSAccount)-[:RESOURCE]->(f:AWSGuardDutyFinding)
    WHERE coalesce(f.archived, false) = false
      AND coalesce(f.sample, false) = false
    RETURN COUNT(f) AS count
    """,
    asset_label="AWSGuardDutyFinding",
    asset_id_field="finding_id",
    # Not finding_arn: `Arn` is soft-mapped at ingest, so every finding the API
    # returns without one would share a null identity. `Id` is required there and is
    # the node's primary key.
    identity_fields=("finding_id",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


class GuardDutyActiveThreat(Finding):
    title: str | None = None
    finding_id: str | None = None
    finding_arn: str | None = None
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
    version="0.1.1",
    frameworks=(
        iso27001_annex_a("8.16"),
        soc2_tsc("CC7.2"),
    ),
)


# =============================================================================
# TODO: SOC 2 CC7.3: Security-event evaluation evidence
# Missing datamodel or evidence: canonical incident nodes linked to provider
# findings, classification and triage status, evaluated_at timestamps, impact
# decisions, and the determination that an event is or is not an incident.
# =============================================================================

# =============================================================================
# TODO: SOC 2 CC7.4: Incident containment and remediation evidence
# Missing datamodel or evidence: incident ownership, acknowledgement,
# containment and remediation timestamps, response status, affected-resource
# links, response actions, and technical communication records.
# =============================================================================

# =============================================================================
# TODO: SOC 2 CC7.5: Recovery and recurrence-prevention evidence
# Missing datamodel: incident recovery timestamps and the link from an incident to
# the change that remediated it. Both are available from PagerDuty and equivalent
# incident APIs once incident nodes exist, see CC7.3 above.
# Out of reach: root-cause narratives and recovery-test sign-off. Those are
# process artifacts, not provider state.
# =============================================================================
