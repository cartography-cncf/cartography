"""
Framework and Fact execution logic for Cartography rules.
"""

import json
from dataclasses import asdict

from neo4j import Driver
from neo4j import GraphDatabase

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.frameworks import FRAMEWORKS
from cartography.rules.formatters import _generate_neo4j_browser_url
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Framework
from cartography.rules.spec.model import Requirement
from cartography.rules.spec.result import FactResult
from cartography.rules.spec.result import FrameworkResult
from cartography.rules.spec.result import RequirementResult


def _run_fact(
    fact: Fact,
    requirement: Requirement,
    framework: Framework,
    driver: Driver,
    database: str,
    fact_counter: int,
    total_facts: int,
    output_format: str,
    neo4j_uri: str,
):
    """Execute a single fact and return the result."""
    if output_format == "text":
        print(f"\n\033[1mFact {fact_counter}/{total_facts}: {fact.name}\033[0m")
        print(f"  \033[36m{'Framework:':<12}\033[0m {framework.name}")
        # Display requirement with optional clickable link
        if requirement.requirement_url:
            print(
                f"  \033[36m{'Requirement:':<12}\033[0m \033]8;;{requirement.requirement_url}\033\\{requirement.id}\033]8;;\033\\ - {requirement.name}"
            )
        else:
            print(
                f"  \033[36m{'Requirement:':<12}\033[0m {requirement.id} - {requirement.name}"
            )
        print(f"  \033[36m{'Fact ID:':<12}\033[0m {fact.id}")
        print(f"  \033[36m{'Description:':<12}\033[0m {fact.description}")
        print(f"  \033[36m{'Provider:':<12}\033[0m {fact.module.value}")

        # Generate and display clickable Neo4j Browser URL
        browser_url = _generate_neo4j_browser_url(neo4j_uri, fact.cypher_visual_query)
        print(
            f"  \033[36m{'Neo4j Query:':<12}\033[0m \033]8;;{browser_url}\033\\Click to run visual query\033]8;;\033\\"
        )

    with driver.session(database=database) as session:
        findings = session.execute_read(read_list_of_dicts_tx, fact.cypher_query)
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
        fact_id=fact.id,
        fact_name=fact.name,
        fact_description=fact.description,
        fact_provider=fact.module.value,
        finding_count=finding_count,
        findings=findings if output_format == "json" else findings[:10],
    )


def _run_single_framework(
    framework_name: str,
    driver: GraphDatabase.driver,
    database: str,
    output_format: str,
    neo4j_uri: str,
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
    requirement_results = []
    fact_counter = 0

    for requirement in framework.requirements:
        fact_results = []
        requirement_findings = 0

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
                neo4j_uri,
            )
            fact_results.append(fact_result)
            requirement_findings += fact_result.finding_count

        # Create requirement result
        requirement_result = RequirementResult(
            requirement_id=requirement.id,
            requirement_name=requirement.name,
            requirement_url=requirement.requirement_url,
            facts=fact_results,
            total_facts=len(fact_results),
            total_findings=requirement_findings,
        )
        requirement_results.append(requirement_result)
        total_findings += requirement_findings

    # Create and return framework result
    return FrameworkResult(
        framework_id=framework.id,
        framework_name=framework.name,
        framework_version=framework.version,
        requirements=requirement_results,
        total_requirements=len(framework.requirements),
        total_facts=total_facts,
        total_findings=total_findings,
    )


def _format_and_output_results(
    all_results: list[FrameworkResult],
    framework_names: list[str],
    output_format: str,
    total_requirements: int,
    total_facts: int,
    total_findings: int,
):
    """Format and output the results of framework execution."""
    if output_format == "json":
        combined_output = [asdict(result) for result in all_results]
        print(json.dumps(combined_output, indent=2))
    else:
        # Text summary
        print("\n" + "=" * 60)
        if len(framework_names) == 1:
            print(f"EXECUTION SUMMARY - {FRAMEWORKS[framework_names[0]].name}")
        else:
            print("OVERALL SUMMARY")
        print("=" * 60)

        if len(framework_names) > 1:
            print(f"Frameworks executed: {len(framework_names)}")
        print(f"Requirements: {total_requirements}")
        print(f"Total facts: {total_facts}")
        print(f"Total results: {total_findings}")

        if total_findings > 0:
            print(
                f"\n\033[36mFramework execution completed with {total_findings} total results\033[0m"
            )
        else:
            print("\n\033[90mFramework execution completed with no results\033[0m")


def run_frameworks(
    framework_names: list[str],
    uri: str,
    neo4j_user: str,
    neo4j_password: str,
    neo4j_database: str,
    output_format: str = "text",
):
    """
    Execute the specified frameworks and present results.

    :param framework_names: The names of the frameworks to execute.
    :param uri: The URI of the Neo4j database. E.g. "bolt://localhost:7687" or "neo4j+s://tenant123.databases.neo4j.io:7687"
    :param neo4j_user: The username for the Neo4j database.
    :param neo4j_password: The password for the Neo4j database.
    :param neo4j_database: The name of the Neo4j database.
    :param output_format: Either "text" or "json". Defaults to "text".
    :return: The exit code.
    """
    # Validate all frameworks exist
    for framework_name in framework_names:
        if framework_name not in FRAMEWORKS:
            if output_format == "text":
                print(f"Unknown framework: {framework_name}")
                print(f"Available frameworks: {', '.join(FRAMEWORKS.keys())}")
            return 1

    # Connect to Neo4j
    if output_format == "text":
        print(f"Connecting to Neo4j at {uri}...")
    driver = GraphDatabase.driver(uri, auth=(neo4j_user, neo4j_password))

    try:
        driver.verify_connectivity()

        # Execute frameworks
        all_results = []
        total_requirements = 0
        total_facts = 0
        total_findings = 0

        for i, framework_name in enumerate(framework_names):
            if output_format == "text" and len(framework_names) > 1:
                if i > 0:
                    print("\n" + "=" * 60)
                print(
                    f"Executing framework {i + 1}/{len(framework_names)}: {framework_name}"
                )

            framework_result = _run_single_framework(
                framework_name, driver, neo4j_database, output_format, uri
            )
            all_results.append(framework_result)

            total_requirements += framework_result.total_requirements
            total_facts += framework_result.total_facts
            total_findings += framework_result.total_findings

        # Output results
        _format_and_output_results(
            all_results,
            framework_names,
            output_format,
            total_requirements,
            total_facts,
            total_findings,
        )

        return 0
    finally:
        driver.close()
