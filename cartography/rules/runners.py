"""
Framework and Fact execution logic for Cartography rules.
"""

from neo4j import Driver
from neo4j import GraphDatabase

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules import RULES
from cartography.rules.formatters import _format_and_output_results
from cartography.rules.formatters import _generate_neo4j_browser_url
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Rule
from cartography.rules.spec.result import CounterResult
from cartography.rules.spec.result import FactResult
from cartography.rules.spec.result import RuleResult


def _run_fact(
    fact: Fact,
    rule: Rule,
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
        # Display rule
        print(f"  \033[36m{'Rule:':<12}\033[0m {rule.id} - {rule.name}")
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
        raw_findings = session.execute_read(read_list_of_dicts_tx, fact.cypher_query)
        findings = rule.parse_results(fact, raw_findings)
        findings_count = len(findings)

    if output_format == "text":
        if findings_count > 0:
            print(f"  \033[36m{'Results:':<12}\033[0m {findings_count} item(s) found")

            # Show sample findings
            print("    Sample results:")
            for idx, finding in enumerate(findings[:3]):  # Show first 3
                # Format rule output nicely
                formatted_items = []
                for key, value in finding.__class__.model_fields.items():
                    if value is not None:
                        # Truncate long values
                        actual_value = getattr(finding, key)
                        str_value = str(actual_value)
                        if len(str_value) > 50:
                            str_value = str_value[:47] + "..."
                        formatted_items.append(f"{key}={str_value}")
                if formatted_items:
                    print(f"      {idx + 1}. {', '.join(formatted_items)}")

            if findings_count > 3:
                print(
                    f"      ... and {findings_count - 3} more (use --output json to see all)"
                )
        else:
            print(f"  \033[36m{'Results:':<12}\033[0m No items found")

    # Create and return fact result
    counter.total_findings += findings_count

    return FactResult(
        fact_id=fact.id,
        fact_name=fact.name,
        fact_description=fact.description,
        fact_provider=fact.module.value,
        findings=findings,
    )


def _run_single_rule(
    rule_name: str,
    driver: GraphDatabase.driver,
    database: str,
    output_format: str,
    neo4j_uri: str,
    fact_filter: str | None = None,
    exclude_experimental: bool = False,
) -> RuleResult:
    """Execute a single rule and return results."""
    rule = RULES[rule_name]
    counter = CounterResult()

    filtered_facts: list[Fact] = []
    for fact in rule.facts:
        if exclude_experimental and fact.maturity != Maturity.STABLE:
            continue
        if fact_filter:
            if fact.id.lower() != fact_filter.lower():
                continue
        counter.total_facts += 1
        filtered_facts.append(fact)

    if output_format == "text":
        print(f"Executing {rule.name} rule")
        if fact_filter:
            print(f"Filtered to fact: {fact_filter}")
        print(f"Total facts: {counter.total_facts}")

    # Execute requirements and collect results
    rule_results = []

    for fact in filtered_facts:
        counter.current_fact += 1
        fact_result = _run_fact(
            fact,
            rule,
            driver,
            database,
            counter,
            output_format,
            neo4j_uri,
        )
        rule_results.append(fact_result)

    # Create and return rule result
    return RuleResult(
        rule_id=rule.id,
        rule_name=rule.name,
        rule_description=rule.description,
        facts=rule_results,
        counter=counter,
    )


def run_rules(
    rule_names: list[str],
    uri: str,
    neo4j_user: str,
    neo4j_password: str,
    neo4j_database: str,
    output_format: str = "text",
    fact_filter: str | None = None,
    exclude_experimental: bool = False,
):
    """
    Execute the specified rules and present results.

    :param rule_names: The names of the rules to execute.
    :param uri: The URI of the Neo4j database. E.g. "bolt://localhost:7687" or "neo4j+s://tenant123.databases.neo4j.io:7687"
    :param neo4j_user: The username for the Neo4j database.
    :param neo4j_password: The password for the Neo4j database.
    :param neo4j_database: The name of the Neo4j database.
    :param output_format: Either "text" or "json". Defaults to "text".
    :param fact_filter: Optional fact ID to filter execution (case-insensitive).
    :param exclude_experimental: Whether to exclude experimental facts from execution.
    :return: The exit code.
    """
    # Validate all rules exist
    for rule_name in rule_names:
        if rule_name not in RULES:
            if output_format == "text":
                print(f"Unknown rule: {rule_name}")
                print(f"Available rules: {', '.join(RULES.keys())}")
            return 1

    # Connect to Neo4j
    if output_format == "text":
        print(f"Connecting to Neo4j at {uri}...")
    driver = GraphDatabase.driver(uri, auth=(neo4j_user, neo4j_password))

    try:
        driver.verify_connectivity()

        # Execute rules
        all_results = []
        total_facts = 0
        total_findings = 0

        for i, rule_name in enumerate(rule_names):
            if output_format == "text" and len(rule_names) > 1:
                if i > 0:
                    print("\n" + "=" * 60)
                print(f"Executing rule {i + 1}/{len(rule_names)}: {rule_name}")

            rule_result = _run_single_rule(
                rule_name,
                driver,
                neo4j_database,
                output_format,
                uri,
                fact_filter,
                exclude_experimental,
            )
            all_results.append(rule_result)
            total_facts += rule_result.counter.total_facts
            total_findings += rule_result.counter.total_findings

        # Output results
        _format_and_output_results(
            all_results, rule_names, output_format, total_facts, total_findings
        )

        return 0
    finally:
        driver.close()
