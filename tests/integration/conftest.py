import logging

import neo4j
import pytest

from tests.integration import settings

logging.basicConfig(level=logging.INFO)
logging.getLogger("neo4j").setLevel(logging.WARNING)


@pytest.fixture(scope="module")
def neo4j_session():
    auth = None
    if settings.get("NEO4J_USER") and settings.get("NEO4J_PASSWORD"):
        auth = neo4j.basic_auth(settings.get("NEO4J_USER"), settings.get("NEO4J_PASSWORD"))
    
    driver = neo4j.GraphDatabase.driver(
        settings.get("NEO4J_URL"),
        auth=auth,
    )
    with driver.session() as session:
        yield session
        session.run("MATCH (n) DETACH DELETE n;")
