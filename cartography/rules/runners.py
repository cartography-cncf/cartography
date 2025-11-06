"""
Framework and Fact execution logic for Cartography rules.
"""

from neo4j import Driver
from neo4j import GraphDatabase

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.frameworks import FRAMEWORKS
from cartography.rules.formatters import _format_and_output_results
from cartography.rules.formatters import _generate_neo4j_browser_url
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Framework
from cartography.rules.spec.model import Requirement
from cartography.rules.spec.result import CounterResult
from cartography.rules.spec.result import FactResult
from cartography.rules.spec.result import FindingResult
from cartography.rules.spec.result import FrameworkResult
from cartography.rules.spec.result import RequirementResult


def _run_fact(
    fact: Fact,
    finding: Finding,
    requirement: Requirement,
    framework: Framework,
    driver: Driver,
    database: str,
    counter: CounterResult,
    output_format: str,
    neo4j_uri: str,
) -> FactResult:
    """Execute a single fact and return the result."""
    if output_format == "text":
        print(
            f"\n\033[1mFact {counter.current_fact}/{counter.total_facts}: {fact.name}\033[0m"
        )
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
        # Display finding
        print(f"  \033[36m{'Finding:':<12}\033[0m {finding.id} - {finding.name}")
        # Display fact details
        print(f"  \033[36m{'Fact ID:':<12}\033[0m {fact.id}")
        print(f"  \033[36m{'Description:':<12}\033[0m {fact.description}")
        print(f"  \033[36m{'Provider:':<12}\033[0m {fact.module.value}")

        # Generate and display clickable Neo4j Browser URL
        browser_url = _generate_neo4j_browser_url(neo4j_uri, fact.cypher_visual_query)
        print(
            f"  \033[36m{'Neo4j Query:':<12}\033[0m \033]8;;{browser_url}\033\\Click to run visual query\033]8;;\033\\"
        )

    with driver.session(database=database) as session:
        raw_matches = session.execute_read(read_list_of_dicts_tx, fact.cypher_query)
        matches = finding.parse_results(raw_matches)
        matches_count = len(matches)

    if output_format == "text":
        if matches_count > 0:
            print(f"  \033[36m{'Results:':<12}\033[0m {matches_count} item(s) found")

            # Show sample findings
            print("    Sample results:")
            for idx, match in enumerate(matches[:3]):  # Show first 3
                # Format finding nicely
                formatted_items = []
                for key, value in match.__class__.model_fields.items():
                    if value is not None:
                        # Truncate long values
                        str_value = str(value)
                        if len(str_value) > 50:
                            str_value = str_value[:47] + "..."
                        formatted_items.append(f"{key}={getattr(match, key)}")

                if formatted_items:
                    print(f"      {idx + 1}. {', '.join(formatted_items)}")

            if matches_count > 3:
                print(
                    f"      ... and {matches_count - 3} more (use --output json to see all)"
                )
        else:
            print(f"  \033[36m{'Results:':<12}\033[0m No items found")

    # Create and return fact result
    counter.total_matches += matches_count

    return FactResult(
        fact_id=fact.id,
        fact_name=fact.name,
        fact_description=fact.description,
        fact_provider=fact.module.value,
        matches=matches if output_format == "json" else matches[:10],
    )


def _run_single_finding(
    framework: Framework,
    requirement: Requirement,
    finding: Finding,
    driver: Driver,
    database: str,
    output_format: str,
    neo4j_uri: str,
    counter: CounterResult,
    fact_filter: str | None = None,
) -> tuple[FindingResult, int]:
    """
    Execute a single finding and return its result.

    Returns:
        A tuple of (FindingResult, facts_executed_count)
    """
    # Filter facts if needed
    facts_to_run = finding.facts
    if fact_filter:
        facts_to_run = tuple(
            f for f in finding.facts if f.id.lower() == fact_filter.lower()
        )

    fact_results = []

    for fact in facts_to_run:
        counter.current_fact += 1
        fact_result = _run_fact(
            fact,
            finding,
            requirement,
            framework,
            driver,
            database,
            counter,
            output_format,
            neo4j_uri,
        )
        fact_results.append(fact_result)

    # Create finding result
    finding_result = FindingResult(
        finding_id=finding.id,
        finding_name=finding.name,
        finding_description=finding.description,
        facts=fact_results,
    )

    return finding_result, len(facts_to_run)


def _run_single_requirement(
    requirement: Requirement,
    framework: Framework,
    driver: Driver,
    database: str,
    output_format: str,
    neo4j_uri: str,
    counter: CounterResult,
    fact_filter: str | None = None,
    finding_filter: str | None = None,
) -> tuple[RequirementResult, int]:
    """
    Execute a single requirement and return its result.

    Returns:
        A tuple of (RequirementResult, facts_executed_count)
    """
    # Filter findings if needed
    findings_to_run = requirement.findings
    if finding_filter:
        findings_to_run = tuple(
            f for f in requirement.findings if f.id.lower() == finding_filter.lower()
        )

    findings_results = []
    for finding in findings_to_run:
        counter.current_finding += 1
        finding_result, _ = _run_single_finding(
            framework,
            requirement,
            finding,
            driver,
            database,
            output_format,
            neo4j_uri,
            counter,
            fact_filter,
        )
        findings_results.append(finding_result)

    requirement_result = RequirementResult(
        requirement_id=requirement.id,
        requirement_name=requirement.name,
        requirement_url=requirement.requirement_url,
        findings=findings_results,
    )

    return requirement_result, len(findings_to_run)


def _run_single_framework(
    framework_name: str,
    driver: GraphDatabase.driver,
    database: str,
    output_format: str,
    neo4j_uri: str,
    requirement_filter: str | None = None,
    finding_filter: str | None = None,
    fact_filter: str | None = None,
) -> FrameworkResult:
    """Execute a single framework and return results."""
    framework = FRAMEWORKS[framework_name]

    # Filter requirements if needed
    requirements_to_run = framework.requirements
    if requirement_filter:
        requirements_to_run = tuple(
            req
            for req in framework.requirements
            if req.id.lower() == requirement_filter.lower()
        )

    counter = CounterResult(total_requirements=len(requirements_to_run))

    for req in requirements_to_run:
        if finding_filter:
            filtered_findings = tuple(
                f for f in req.findings if f.id.lower() == finding_filter.lower()
            )
        else:
            filtered_findings = req.findings
        counter.total_findings += len(filtered_findings)
        for finding in filtered_findings:
            if fact_filter:
                filtered_facts = tuple(
                    f for f in finding.facts if f.id.lower() == fact_filter.lower()
                )
            else:
                filtered_facts = finding.facts
            counter.total_facts += len(filtered_facts)

    if output_format == "text":
        print(f"Executing {framework.name} framework")
        if requirement_filter:
            print(f"Filtered to requirement: {requirement_filter}")
            if finding_filter:
                print(f"Filtered to finding: {finding_filter}")
            if fact_filter:
                print(f"Filtered to fact: {fact_filter}")
        print(f"Requirements: {len(requirements_to_run)}")
        print(f"Total findings: {counter.total_findings}")
        print(f"Total facts: {counter.total_facts}")

    # Execute requirements and collect results
    requirement_results = []

    for requirement in requirements_to_run:
        counter.current_requirement += 1
        requirement_result, _ = _run_single_requirement(
            requirement,
            framework,
            driver,
            database,
            output_format,
            neo4j_uri,
            counter,
            fact_filter,
            finding_filter,
        )
        requirement_results.append(requirement_result)

    # Create and return framework result
    return FrameworkResult(
        framework_id=framework.id,
        framework_name=framework.name,
        framework_version=framework.version,
        requirements=requirement_results,
        counter=counter,
    )


def run_frameworks(
    framework_names: list[str],
    uri: str,
    neo4j_user: str,
    neo4j_password: str,
    neo4j_database: str,
    output_format: str = "text",
    requirement_filter: str | None = None,
    finding_filter: str | None = None,
    fact_filter: str | None = None,
):
    """
    Execute the specified frameworks and present results.

    :param framework_names: The names of the frameworks to execute.
    :param uri: The URI of the Neo4j database. E.g. "bolt://localhost:7687" or "neo4j+s://tenant123.databases.neo4j.io:7687"
    :param neo4j_user: The username for the Neo4j database.
    :param neo4j_password: The password for the Neo4j database.
    :param neo4j_database: The name of the Neo4j database.
    :param output_format: Either "text" or "json". Defaults to "text".
    :param requirement_filter: Optional requirement ID to filter execution (case-insensitive).
    :param finding_filter: Optional finding ID to filter execution (case-insensitive).
    :param fact_filter: Optional fact ID to filter execution (case-insensitive).
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
        total_findings = 0
        total_facts = 0
        total_matches = 0

        for i, framework_name in enumerate(framework_names):
            if output_format == "text" and len(framework_names) > 1:
                if i > 0:
                    print("\n" + "=" * 60)
                print(
                    f"Executing framework {i + 1}/{len(framework_names)}: {framework_name}"
                )

            framework_result = _run_single_framework(
                framework_name,
                driver,
                neo4j_database,
                output_format,
                uri,
                requirement_filter,
                finding_filter,
                fact_filter,
            )
            all_results.append(framework_result)

            total_requirements += framework_result.counter.total_requirements
            total_facts += framework_result.counter.total_facts
            total_findings += framework_result.counter.total_findings
            total_matches += framework_result.counter.total_matches

        # Output results
        _format_and_output_results(
            all_results,
            framework_names,
            output_format,
            total_requirements,
            total_findings,
            total_facts,
            total_matches,
        )

        return 0
    finally:
        driver.close()
