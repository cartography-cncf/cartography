# Execution result classes
from dataclasses import dataclass
from typing import Any


@dataclass
class FactResult:
    """
    Results for a single Fact.
    """

    fact_id: str
    fact_name: str
    fact_description: str
    fact_provider: str
    finding_count: int = 0
    findings: list[dict[str, Any]] | None = None


@dataclass
class RequirementResult:
    """
    Results for a single requirement, containing all its Facts.
    """

    requirement_id: str
    requirement_name: str
    requirement_url: str | None
    facts: list[FactResult]
    total_facts: int
    total_findings: int


@dataclass
class FrameworkResult:
    """
    The formal object output by `--output json` from the `cartography-rules` CLI.
    """

    framework_id: str
    framework_name: str
    framework_version: str
    requirements: list[RequirementResult]
    total_requirements: int
    total_facts: int
    total_findings: int
