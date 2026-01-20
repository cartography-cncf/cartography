import logging
import os

import neo4j
import pytest

from tests.integration import settings

logging.basicConfig(level=logging.INFO)
logging.getLogger("neo4j").setLevel(logging.WARNING)


@pytest.fixture(scope="module")
def neo4j_session():
    # Get authentication from environment variables
    neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
    neo4j_password = os.environ.get("NEO4J_PASSWORD", "neo4j")
    
    driver = neo4j.GraphDatabase.driver(
        settings.get("NEO4J_URL"),
        auth=(neo4j_user, neo4j_password)
    )
    with driver.session() as session:
        yield session
        session.run("MATCH (n) DETACH DELETE n;")
