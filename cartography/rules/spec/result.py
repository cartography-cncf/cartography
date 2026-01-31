"""
Execution result classes for Cartography rules.

This module defines the data structures used to represent the results
of rule and fact execution.
"""

from dataclasses import dataclass
from dataclasses import field

from cartography.rules.spec.model import Finding


@dataclass
class CounterResult:
    """
    Counter for tracking rule execution progress and aggregate metrics.

    This class maintains running totals during rule execution, including
    the current progress and aggregate compliance metrics across all facts.

    Attributes:
        current_fact (int): The index of the currently executing fact.
        total_facts (int): The total number of facts to execute.
        total_findings (int): The cumulative count of findings across all facts.
        total_assets (int): Sum of total_assets across all facts (for compliance).
        total_failing (int): Sum of failing assets across all facts (for compliance).
        total_passing (int): Sum of passing assets across all facts (for compliance).
    """

    current_fact: int = 0
    total_facts: int = 0
    total_findings: int = 0
    total_assets: int = 0
    total_failing: int = 0
    total_passing: int = 0


@dataclass
class FactResult:
    """
    Results for a single Fact execution.

    Contains the findings from executing a Fact's Cypher query along with
    optional compliance metrics when a count query is provided.

    Attributes:
        fact_id (str): The unique identifier of the executed Fact.
        fact_name (str): The human-readable name of the Fact.
        fact_description (str): A description of what the Fact checks for.
        fact_provider (str): The cloud provider or module this Fact applies to.
        findings (list[Finding]): The list of findings from the Fact query.
        total_assets (int | None): Total assets evaluated (from cypher_count_query).
            None if no count query was provided.
        failing (int | None): Number of assets that match the finding criteria.
            None if no count query was provided.
        passing (int | None): Number of assets that don't match (total_assets - failing).
            None if no count query was provided.
    """

    fact_id: str
    fact_name: str
    fact_description: str
    fact_provider: str
    findings: list[Finding] = field(default_factory=list)
    total_assets: int | None = None
    failing: int | None = None
    passing: int | None = None


@dataclass
class RuleResult:
    """
    Results for a single Rule execution.

    Contains the aggregated results from executing all Facts within a Rule,
    along with execution counters and metadata.

    Attributes:
        rule_id (str): The unique identifier of the executed Rule.
        rule_name (str): The human-readable name of the Rule.
        rule_description (str): A description of the security issue or misconfiguration.
        counter (CounterResult): Execution counters and aggregate metrics.
        facts (list[FactResult]): Results from each Fact executed within this Rule.
    """

    rule_id: str
    rule_name: str
    rule_description: str
    counter: CounterResult
    facts: list[FactResult] = field(default_factory=list)
