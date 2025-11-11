"""
Framework and Fact execution logic for Cartography rules.
"""

from dataclasses import fields

from neo4j import Driver
from neo4j import GraphDatabase

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.findings import FINDINGS
from cartography.rules.formatters import _extract_entity_mappings
from cartography.rules.formatters import _format_and_output_results
from cartography.rules.formatters import _generate_neo4j_browser_url
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.result import CounterResult
from cartography.rules.spec.result import FactResult
from cartography.rules.spec.result import FindingResult


def _run_fact(
    fact: Fact,
    finding: Finding,
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
        # Display finding
        print(f"  \033[36m{'Finding:':<12}\033[0m {finding.id} - {finding.name}")
        # Display fact details
        print(f"  \033[36m{'Fact ID:':<12}\033[0m {fact.id}")
        print(f"  \033[36m{'Description:':<12}\033[0m {fact.description}")
        print(f"  \033[36m{'Provider:':<12}\033[0m {fact.module.value}")

        # Generate and display clickable Neo4j Browser URL
        browser_url = _generate_neo4j_browser_url(neo4j_uri, fact.cypher_query)
        print(
            f"  \033[36m{'Neo4j Query:':<12}\033[0m \033]8;;{browser_url}\033\\Click to run visual query\033]8;;\033\\"
        )

    with driver.session(database=database) as session:
        matches = session.execute_read(read_list_of_dicts_tx, fact.cypher_query)
        matches_count = len(matches)

    result_model = _extract_entity_mappings(fact.cypher_query)

    if output_format == "text":
        if matches_count > 0:
            print(f"  \033[36m{'Results:':<12}\033[0m {matches_count} item(s) found")

            # Show sample findings
            print("    Sample results:")
            for idx, match in enumerate(matches[:3]):  # Show first 3
                # Format results nicely
                formatted_items = []

                if not isinstance(match, dict):
                    print(f"      {idx + 1}. {match}")
                    continue

                first_node_key = list(match.keys())[0]
                first_node = match[first_node_key]

                if not isinstance(first_node, dict):
                    print(f"      {idx + 1}. {first_node}")
                    continue

                # Get corresponding model
                first_node_class = result_model.get(first_node_key)
                if first_node_class is None:
                    field_count = 0
                    for key, value in first_node.items():  # Limit to first 5 fields
                        if key in (
                            "lastupdated",
                            "firstseen",
                            "_module_version",
                            "_module_name",
                        ):
                            continue
                        field_count += 1
                        if field_count > 5:
                            break
                        # Truncate long values
                        str_value = str(value)
                        if len(str_value) > 50:
                            str_value = str_value[:47] + "..."
                        formatted_items.append(f"{key}={str_value}")
                # If we have a model, use its fields for more consistent output
                else:
                    field_count = 0
                    for key in fields(first_node_class.properties):  # type: ignore
                        # Skip metadata and common fields
                        if key.name in (
                            "lastupdated",
                            "firstseen",
                            "_module_version",
                            "_module_name",
                        ):
                            continue
                        field_count += 1
                        if field_count > 5:
                            break
                        value = first_node.get(key.name)
                        if value is not None:
                            # Truncate long values
                            str_value = str(value)
                            if len(str_value) > 50:
                                str_value = str_value[:47] + "..."
                            formatted_items.append(f"{key.name}={str_value}")

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
    finding_name: str,
    driver: GraphDatabase.driver,
    database: str,
    output_format: str,
    neo4j_uri: str,
    fact_filter: str | None = None,
    exclude_experimental: bool = False,
) -> FindingResult:
    """Execute a single finding and return results."""
    finding = FINDINGS[finding_name]
    counter = CounterResult()

    filtered_facts: list[Fact] = []
    for fact in finding.facts:
        if exclude_experimental and fact.maturity != Maturity.STABLE:
            continue
        if fact_filter:
            if fact.id.lower() != fact_filter.lower():
                continue
        counter.total_facts += 1
        filtered_facts.append(fact)

    if output_format == "text":
        print(f"Executing {finding.name} finding")
        if fact_filter:
            print(f"Filtered to fact: {fact_filter}")
        print(f"Total facts: {counter.total_facts}")

    # Execute requirements and collect results
    finding_results = []

    for fact in filtered_facts:
        counter.current_fact += 1
        fact_result = _run_fact(
            fact,
            finding,
            driver,
            database,
            counter,
            output_format,
            neo4j_uri,
        )
        finding_results.append(fact_result)

    # Create and return finding result
    return FindingResult(
        finding_id=finding.id,
        finding_name=finding.name,
        finding_description=finding.description,
        facts=finding_results,
        counter=counter,
    )


def run_findings(
    finding_names: list[str],
    uri: str,
    neo4j_user: str,
    neo4j_password: str,
    neo4j_database: str,
    output_format: str = "text",
    fact_filter: str | None = None,
    exclude_experimental: bool = False,
):
    """
    Execute the specified findings and present results.

    :param finding_names: The names of the findings to execute.
    :param uri: The URI of the Neo4j database. E.g. "bolt://localhost:7687" or "neo4j+s://tenant123.databases.neo4j.io:7687"
    :param neo4j_user: The username for the Neo4j database.
    :param neo4j_password: The password for the Neo4j database.
    :param neo4j_database: The name of the Neo4j database.
    :param output_format: Either "text" or "json". Defaults to "text".
    :param fact_filter: Optional fact ID to filter execution (case-insensitive).
    :param exclude_experimental: Whether to exclude experimental facts from execution.
    :return: The exit code.
    """
    # Validate all findings exist
    for finding_name in finding_names:
        if finding_name not in FINDINGS:
            if output_format == "text":
                print(f"Unknown finding: {finding_name}")
                print(f"Available findings: {', '.join(FINDINGS.keys())}")
            return 1

    # Connect to Neo4j
    if output_format == "text":
        print(f"Connecting to Neo4j at {uri}...")
    driver = GraphDatabase.driver(uri, auth=(neo4j_user, neo4j_password))

    try:
        driver.verify_connectivity()

        # Execute findings
        all_results = []
        total_facts = 0
        total_matches = 0

        for i, finding_name in enumerate(finding_names):
            if output_format == "text" and len(finding_names) > 1:
                if i > 0:
                    print("\n" + "=" * 60)
                print(f"Executing finding {i + 1}/{len(finding_names)}: {finding_name}")

            finding_result = _run_single_finding(
                finding_name,
                driver,
                neo4j_database,
                output_format,
                uri,
                fact_filter,
                exclude_experimental,
            )
            all_results.append(finding_result)
            total_facts += finding_result.counter.total_facts
            total_matches += finding_result.counter.total_matches

        # Output results
        _format_and_output_results(
            all_results, finding_names, output_format, total_facts, total_matches
        )

        return 0
    finally:
        driver.close()
