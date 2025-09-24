"""
Cartography RunRules CLI

Execute security frameworks and present facts about your environment.
"""

import argparse
import getpass
import json
import logging
import os
import sys
from dataclasses import asdict
from dataclasses import dataclass
from typing import Any

from neo4j import GraphDatabase
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import JsonLexer

from cartography.rules.data.frameworks import FRAMEWORKS
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Framework

# Reduce Neo4j logging noise - only show errors
neo4j_logger = logging.getLogger("neo4j")
neo4j_logger.setLevel(logging.ERROR)


# Execution result classes
@dataclass
class FactResult:
    fact: Fact
    requirement_id: str
    finding_count: int = 0
    findings: list[dict[str, Any]] | None = None

    def __post_init__(self):
        if self.findings is None:
            self.findings = []


@dataclass
class ExecutionSummary:
    total_requirements: int
    total_facts: int
    total_findings: int


@dataclass
class FrameworkResult:
    framework: Framework
    summary: ExecutionSummary
    results: list[FactResult]


def _output_json(framework_result: FrameworkResult):
    """Output framework results as colorized JSON."""
    json_str = json.dumps(asdict(framework_result), indent=2)
    colorized = highlight(json_str, JsonLexer(), TerminalFormatter())
    print(colorized.rstrip())


def _run_fact(
    fact,
    requirement,
    framework,
    driver,
    database,
    fact_counter,
    total_facts,
    output_format,
):
    """Execute a single fact and return the result."""
    if output_format == "text":
        print(f"\n\033[1mFact {fact_counter}/{total_facts}: {fact.name}\033[0m")
        print(f"  \033[36m{'Framework:':<12}\033[0m {framework.name}")
        print(
            f"  \033[36m{'Requirement:':<12}\033[0m {requirement.name} ({requirement.id})"
        )
        print(f"  \033[36m{'Fact ID:':<12}\033[0m {fact.id}")
        print(f"  \033[36m{'Description:':<12}\033[0m {fact.description}")
        print(f"  \033[36m{'Provider:':<12}\033[0m {fact.provider}")

    with driver.session(database=database) as session:
        result = session.run(fact.cypher_query)
        findings = [dict(record) for record in result]
        finding_count = len(findings)

    if output_format == "text":
        if finding_count > 0:
            print(f"  \033[36m{'Results:':<12}\033[0m {finding_count} item(s) found")

            # Show sample findings
            print("    Sample results:")
            for idx, finding in enumerate(findings[:3]):  # Show first 3
                # Format finding nicely
                formatted_items = []
                for key, value in finding.items():
                    if value is not None:
                        # Truncate long values
                        str_value = str(value)
                        if len(str_value) > 50:
                            str_value = str_value[:47] + "..."
                        formatted_items.append(f"{key}={str_value}")

                if formatted_items:
                    print(f"      {idx + 1}. {', '.join(formatted_items)}")

            if finding_count > 3:
                print(
                    f"      ... and {finding_count - 3} more (use --output json to see all)"
                )
        else:
            print(f"  \033[36m{'Results:':<12}\033[0m No items found")

    # Create and return fact result
    return FactResult(
        fact=fact,
        requirement_id=requirement.id,
        finding_count=finding_count,
        findings=findings if output_format == "json" else findings[:10],
    )


def _run_single_framework(
    framework_name: str, driver: GraphDatabase.driver, database: str, output_format: str
) -> FrameworkResult:
    """Execute a single framework and return results."""
    framework = FRAMEWORKS[framework_name]

    # Count total facts for display
    total_facts = sum(len(req.facts) for req in framework.requirements)

    if output_format == "text":
        print(f"Executing {framework.name} framework")
        print(f"Requirements: {len(framework.requirements)}")
        print(f"Total facts: {total_facts}")

    # Execute facts and collect results
    total_findings = 0
    fact_results = []
    fact_counter = 0

    for requirement in framework.requirements:
        for fact in requirement.facts:
            fact_counter += 1
            fact_result = _run_fact(
                fact,
                requirement,
                framework,
                driver,
                database,
                fact_counter,
                total_facts,
                output_format,
            )
            fact_results.append(fact_result)
            total_findings += fact_result.finding_count

    # Create and return framework result
    return FrameworkResult(
        framework=framework,
        summary=ExecutionSummary(
            total_requirements=len(framework.requirements),
            total_facts=total_facts,
            total_findings=total_findings,
        ),
        results=fact_results,
    )


def _run_frameworks(
    framework_names: list[str],
    uri: str,
    user: str,
    password: str,
    database: str,
    output_format: str = "text",
):
    """Execute the specified frameworks and present results."""
    # Validate all frameworks exist
    for framework_name in framework_names:
        if framework_name not in FRAMEWORKS:
            if output_format == "text":
                print(f"Unknown framework: {framework_name}")
                print(f"Available frameworks: {', '.join(FRAMEWORKS.keys())}")
            sys.exit(1)

    # Connect to Neo4j
    if output_format == "text":
        print(f"Connecting to Neo4j at {uri}...")
    driver = GraphDatabase.driver(uri, auth=(user, password))

    # Test connection
    with driver.session(database=database) as session:
        result = session.run("RETURN 1 as test")
        if result.single()["test"] != 1:
            raise Exception("Connection test failed")

    if output_format == "text":
        print(f"Connected successfully as {user}")

    # For multiple frameworks, we need different output handling
    if len(framework_names) == 1:
        # Single framework - existing behavior
        framework_name = framework_names[0]
        framework_result = _run_single_framework(
            framework_name, driver, database, output_format
        )

        if output_format == "json":
            _output_json(framework_result)
        else:
            # Text summary for single framework
            print("\n" + "=" * 60)
            print(f"EXECUTION SUMMARY - {FRAMEWORKS[framework_names[0]].name}")
            print("=" * 60)
            print(f"Requirements: {framework_result.summary.total_requirements}")
            print(f"Total facts: {framework_result.summary.total_facts}")
            print(f"Total results: {framework_result.summary.total_findings}")

            if framework_result.summary.total_findings > 0:
                print(
                    f"\n\033[36mFramework execution completed with {framework_result.summary.total_findings} total results\033[0m"
                )
            else:
                print("\n\033[90mFramework execution completed with no results\033[0m")

    else:
        # Multiple frameworks
        all_results = []
        total_requirements = 0
        total_facts = 0
        total_findings = 0

        for i, framework_name in enumerate(framework_names):
            if output_format == "text":
                if i > 0:
                    print("\n" + "=" * 60)
                print(
                    f"Executing framework {i + 1}/{len(framework_names)}: {framework_name}"
                )

            framework_result = _run_single_framework(
                framework_name, driver, database, output_format
            )
            all_results.append(framework_result)

            total_requirements += framework_result.summary.total_requirements
            total_facts += framework_result.summary.total_facts
            total_findings += framework_result.summary.total_findings

        # Output combined results
        if output_format == "json":
            # For JSON, output array of framework results
            combined_output = [asdict(result) for result in all_results]
            json_str = json.dumps(combined_output, indent=2)
            colorized = highlight(json_str, JsonLexer(), TerminalFormatter())
            print(colorized.rstrip())
        else:
            # Text summary for all frameworks
            print("\n" + "=" * 60)
            print("OVERALL SUMMARY")
            print("=" * 60)
            print(f"Frameworks executed: {len(framework_names)}")
            print(f"Total requirements: {total_requirements}")
            print(f"Total facts: {total_facts}")
            print(f"Total results: {total_findings}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Execute Cartography security frameworks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    available_frameworks = list(FRAMEWORKS.keys()) + ["all"]
    parser.add_argument(
        "framework",
        nargs="?",
        choices=available_frameworks,
        help='Security framework to execute (or "all" to execute all frameworks)',
    )

    parser.add_argument(
        "--list", action="store_true", help="List available frameworks and exit"
    )

    parser.add_argument(
        "--uri",
        default=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        help="Neo4j URI (default: bolt://localhost:7687)",
    )

    parser.add_argument(
        "--user",
        default=os.getenv("NEO4J_USER", "neo4j"),
        help="Neo4j username (default: neo4j)",
    )

    parser.add_argument(
        "--database",
        default=os.getenv("NEO4J_DATABASE", "neo4j"),
        help="Neo4j database name (default: neo4j)",
    )

    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args()

    # Handle --list option
    if args.list:
        print("Available frameworks:")
        for framework_name, framework in FRAMEWORKS.items():
            print(f"  {framework_name:15} - {framework.name} v{framework.version}")
        print(f"  {'all':15} - Run all frameworks")
        sys.exit(0)

    # Framework is required if not using --list
    if not args.framework:
        parser.error(
            "framework is required (or use --list to see available frameworks)"
        )

    # Get password
    password = os.getenv("NEO4J_PASSWORD")
    if not password:
        password = getpass.getpass("Enter Neo4j password: ")

    # Determine which frameworks to run
    if args.framework == "all":
        frameworks_to_run = list(FRAMEWORKS.keys())
    else:
        frameworks_to_run = [args.framework]

    # Execute framework(s)
    _run_frameworks(
        frameworks_to_run, args.uri, args.user, password, args.database, args.output
    )


if __name__ == "__main__":
    main()
