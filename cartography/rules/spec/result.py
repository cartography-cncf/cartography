# Execution result classes
from dataclasses import dataclass
from dataclasses import field

from cartography.rules.spec.model import Finding


@dataclass
class CounterResult:
    current_fact: int = 0
    total_facts: int = 0
    total_findings: int = 0


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
