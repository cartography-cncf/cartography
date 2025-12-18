"""Helpers for evaluating OAuth scope risk levels for Google Workspace apps.

The mappings are derived from Cisco Cloudlock's published Google OAuth scope risk
tables. Each scope is assigned a qualitative risk rating (``low``, ``medium``,
or ``high``) to make it easier to understand the potential impact of a token.
"""

from __future__ import annotations

from typing import Iterable
from typing import Literal

RiskLevel = Literal["low", "medium", "high"]

# Cloudlock assigns risk across scopes using Low/Medium/High buckets. The
# mapping below captures the published values for common Workspace scopes so
# they can be unit tested and reused across the ingestion pipeline.
CLOUDLOCK_SCOPE_RISK: dict[str, RiskLevel] = {
    # Identity and profile
    "openid": "low",
    "profile": "low",
    "email": "low",
    "https://www.googleapis.com/auth/userinfo.email": "low",
    "https://www.googleapis.com/auth/userinfo.profile": "low",

    # Calendar
    "https://www.googleapis.com/auth/calendar": "medium",
    "https://www.googleapis.com/auth/calendar.readonly": "low",

    # Drive
    "https://www.googleapis.com/auth/drive": "high",
    "https://www.googleapis.com/auth/drive.file": "medium",
    "https://www.googleapis.com/auth/drive.readonly": "medium",

    # Gmail
    "https://www.googleapis.com/auth/gmail.readonly": "high",
    "https://www.googleapis.com/auth/gmail.modify": "high",
    "https://www.googleapis.com/auth/gmail.compose": "medium",
    "https://www.googleapis.com/auth/gmail.settings.basic": "high",
    "https://www.googleapis.com/auth/gmail.settings.sharing": "high",

    # Admin directory
    "https://www.googleapis.com/auth/admin.directory.user": "high",
    "https://www.googleapis.com/auth/admin.directory.user.readonly": "medium",
    "https://www.googleapis.com/auth/admin.directory.group": "high",
    "https://www.googleapis.com/auth/admin.directory.group.readonly": "medium",
    "https://www.googleapis.com/auth/admin.directory.domain": "high",
    "https://www.googleapis.com/auth/admin.directory.rolemanagement": "high",
    "https://www.googleapis.com/auth/admin.reports.audit.readonly": "medium",
}

DEFAULT_SCOPE_RISK: RiskLevel = "medium"
_RISK_ORDER: dict[RiskLevel, int] = {"low": 0, "medium": 1, "high": 2}
_ORDER_TO_RISK: dict[int, RiskLevel] = {value: key for key, value in _RISK_ORDER.items()}


def get_scope_risk(scope: str) -> RiskLevel:
    """Return the Cloudlock risk level for a given scope.

    Unknown scopes fall back to ``DEFAULT_SCOPE_RISK`` to avoid underestimating
    risk when the mapping is incomplete.
    """

    return CLOUDLOCK_SCOPE_RISK.get(scope, DEFAULT_SCOPE_RISK)


def evaluate_scope_risk(scopes: Iterable[str]) -> tuple[RiskLevel, list[str]]:
    """Compute aggregate and per-scope risk for an authorization.

    :param scopes: Iterable of OAuth scopes granted to the token
    :returns: Tuple of (aggregate risk level, per-scope risk summaries). The
        per-scope values are stored as strings in the form ``"<scope>|<risk>"``
        to keep them easy to persist as Neo4j properties.
    """

    scope_risk_levels: list[str] = []
    highest_risk_rank = _RISK_ORDER[DEFAULT_SCOPE_RISK]

    for scope in scopes:
        risk = get_scope_risk(scope)
        highest_risk_rank = max(highest_risk_rank, _RISK_ORDER[risk])
        scope_risk_levels.append(f"{scope}|{risk}")

    aggregate_risk = _ORDER_TO_RISK[highest_risk_rank]
    return aggregate_risk, scope_risk_levels
