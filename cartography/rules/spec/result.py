# Execution result classes
from dataclasses import dataclass
from dataclasses import field

from cartography.rules.spec.model import Finding


@dataclass
class CounterResult:
    current_fact: int = 0
    total_facts: int = 0
    total_findings: int = 0
    # Aggregate asset compliance metrics
    total_assets: int = 0  # Sum of total_assets across all facts
    total_failing: int = 0  # Sum of failing across all facts
    total_passing: int = 0  # Sum of passing across all facts


@dataclass
class FactResult:
    """
    Results for a single Fact.
    """

    fact_id: str
    fact_name: str
    fact_description: str
    fact_provider: str
    findings: list[Finding] = field(default_factory=list)
    # Asset compliance metrics
    total_assets: int | None = None  # Total assets evaluated (from cypher_count_query)
    failing: int | None = None  # Assets that match the finding criteria (len(findings))
    passing: int | None = None  # Assets that don't match (total_assets - failing)


@dataclass
class RuleResult:
    """
    Results for a single Rule.
    """

    rule_id: str
    rule_name: str
    rule_description: str
    counter: CounterResult
    facts: list[FactResult] = field(default_factory=list)
