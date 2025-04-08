import os
import json
from typing import Dict, Any
import requests
from neo4j import GraphDatabase


def get_neo4j_session():
    """
    Connect to a real Neo4j instance using environment variables.
    Returns a Neo4j session object.
    """
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    assert uri and user and password, "❌ Neo4j connection settings missing from environment variables"

    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver.session()


def load_fixture(filename: str) -> Dict[str, Any]:
    """
    Load a JSON test fixture from the fixtures directory.
    """
    fixture_path = os.path.join(
        os.path.dirname(__file__),
        "fixtures",
        filename
    )
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _mock_auth_response() -> requests.Response:
    """
    Return a mocked successful response object for MS Graph auth.
    """
    mock_response = requests.Response()
    mock_response.status_code = 200
    mock_response._content = b'{"access_token": "mocked_token"}'
    return mock_response


def _mock_api_response(data: Any) -> requests.Response:
    """
    Return a mocked successful response object for MS Graph API data.
    """
    mock_response = requests.Response()
    mock_response.status_code = 200
    mock_response._content = json.dumps({
        "value": data
    }).encode("utf-8")
    return mock_response
