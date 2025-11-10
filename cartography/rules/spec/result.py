# Execution result classes
from dataclasses import dataclass
from dataclasses import field

from cartography.rules.spec.model import FindingOutput


@dataclass
class CounterResult:
    current_fact: int = 0
    total_facts: int = 0
    total_matches: int = 0


@dataclass
class FactResult:
    """
    Results for a single Fact.
    """

    fact_id: str
    fact_name: str
    fact_description: str
    fact_provider: str
    matches: list[FindingOutput] | None = None


@dataclass
class FindingResult:
    """
    Results for a single Finding.
    """

    finding_id: str
    finding_name: str
    finding_description: str
    counter: CounterResult
    facts: list[FactResult] = field(default_factory=list)
