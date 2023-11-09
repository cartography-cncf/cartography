import logging

import neo4j
import pytest

from tests.integration import settings

logging.basicConfig(level=logging.INFO)
logging.getLogger('neo4j').setLevel(logging.WARNING)


@pytest.fixture(scope="module")
def neo4j_session():
    driver = neo4j.GraphDatabase.driver(settings.get("NEO4J_URL"))
    with driver.session() as session:
        yield session
        session.run("MATCH (n) DETACH DELETE n;")
