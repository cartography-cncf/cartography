# Execution result classes
from dataclasses import dataclass
from typing import Any


@dataclass
class FactResult:
    fact_id: str
    fact_name: str
    fact_description: str
    fact_provider: str
    requirement_id: str
    finding_count: int = 0
    findings: list[dict[str, Any]] | None = None
    requirement_url: str | None = None


@dataclass
class FrameworkResult:
    """
    The formal object output by `--output json`.
    """

    framework_id: str
    framework_name: str
    framework_version: str
    results: list[FactResult]
    total_requirements: int
    total_facts: int
    total_findings: int
