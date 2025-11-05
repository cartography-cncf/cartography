# Execution result classes
from dataclasses import dataclass, field
from typing import Any
from cartography.rules.spec.model import FindingOutput


@dataclass
class CounterResult:
    current_requirement: int = 0
    total_requirements: int = 0
    current_finding: int = 0
    total_findings: int = 0
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
    matches: list[dict[str, Any]] | None = None # WIP: Use object


@dataclass
class FindingResult:
    """
    Results for a single Finding.
    """
    finding_id: str
    finding_name: str
    finding_description: str
    facts: list[FactResult] = field(default_factory=list)


@dataclass
class RequirementResult:
    """
    Results for a single requirement, containing all its Facts.
    """

    requirement_id: str
    requirement_name: str
    requirement_url: str | None
    findings: list[FindingResult] = field(default_factory=list)


@dataclass
class FrameworkResult:
    """
    The formal object output by `--output json` from the `cartography-rules` CLI.
    """

    framework_id: str
    framework_name: str
    framework_version: str
    counter: CounterResult
    requirements: list[RequirementResult] = field(default_factory=list)
