"""
Output formatting utilities for Cartography rules.
"""

import re
from urllib.parse import quote


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
