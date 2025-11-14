"""
Output formatting utilities for Cartography rules.
"""

import json
import re
from dataclasses import asdict
from dataclasses import is_dataclass
from urllib.parse import quote

from pydantic import BaseModel

from cartography.rules.data.findings import FINDINGS
from cartography.rules.spec.result import FindingResult


def _generate_neo4j_browser_url(neo4j_uri: str, cypher_query: str) -> str:
    """Generate a clickable Neo4j Browser URL with pre-populated query."""
    # Handle different Neo4j URI protocols
    if neo4j_uri.startswith("bolt://"):
        browser_uri = neo4j_uri.replace("bolt://", "http://", 1)
    elif neo4j_uri.startswith("bolt+s://"):
        browser_uri = neo4j_uri.replace("bolt+s://", "https://", 1)
    elif neo4j_uri.startswith("bolt+ssc://"):
        browser_uri = neo4j_uri.replace("bolt+ssc://", "https://", 1)
    elif neo4j_uri.startswith("neo4j://"):
        browser_uri = neo4j_uri.replace("neo4j://", "http://", 1)
    elif neo4j_uri.startswith("neo4j+s://"):
        browser_uri = neo4j_uri.replace("neo4j+s://", "https://", 1)
    elif neo4j_uri.startswith("neo4j+ssc://"):
        browser_uri = neo4j_uri.replace("neo4j+ssc://", "https://", 1)
    else:
        browser_uri = neo4j_uri

    # Handle port mapping for local instances
    if ":7687" in browser_uri and (
        "localhost" in browser_uri or "127.0.0.1" in browser_uri
    ):
        browser_uri = browser_uri.replace(":7687", ":7474")

    # For Neo4j Aura (cloud), remove the port as it uses standard HTTPS port
    if ".databases.neo4j.io" in browser_uri:
        # Remove any port number for Aura URLs
        browser_uri = re.sub(r":\d+", "", browser_uri)

    # Ensure the URL ends properly
    if not browser_uri.endswith("/"):
        browser_uri += "/"

    # URL encode the cypher query
    encoded_query = quote(cypher_query.strip())

    # Construct the Neo4j Browser URL with pre-populated query
    return f"{browser_uri}browser/?cmd=edit&arg={encoded_query}"


def to_serializable(obj):
    # Pydantic model (v2)
    if isinstance(obj, BaseModel):
        return to_serializable(obj.model_dump())

    # Dataclass
    if is_dataclass(obj):
        return to_serializable(asdict(obj))

    # Dict
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}

    # List / Tuple / Set
    if isinstance(obj, (list, tuple, set)):
        return [to_serializable(v) for v in obj]

    # Primitive
    return obj


def _format_and_output_results(
    all_results: list[FindingResult],
    finding_names: list[str],
    output_format: str,
    total_facts: int,
    total_matches: int,
):
    """Format and output the results of framework execution."""
    if output_format == "json":
        combined_output = [asdict(result) for result in all_results]
        print(json.dumps(to_serializable(combined_output), indent=2))
    else:
        # Text summary
        print("\n" + "=" * 60)
        if len(finding_names) == 1:
            print(f"EXECUTION SUMMARY - {FINDINGS[finding_names[0]].name}")
        else:
            print("OVERALL SUMMARY")
        print("=" * 60)

        if len(finding_names) > 1:
            print(f"Findings executed: {len(finding_names)}")
        print(f"Total facts: {total_facts}")
        print(f"Total results: {total_matches}")

        if total_matches > 0:
            print(
                f"\n\033[36mFinding execution completed with {total_matches} total results\033[0m"
            )
        else:
            print("\n\033[90mFinding execution completed with no results\033[0m")
