import logging
import os
import time

import neo4j
import pytest
from testcontainers.core.container import DockerContainer

from tests.integration import settings

logging.basicConfig(level=logging.INFO)
logging.getLogger("neo4j").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def _wait_for_neo4j(uri: str, timeout_seconds: int = 180) -> None:
    """Block until Neo4j answers a query on its default database.

    A successful Bolt handshake is not enough: Neo4j accepts connections while the
    default database is still starting, and the first query then fails. The overall
    deadline is long because in CI the container may still be pulling its image when
    this starts. Each attempt gives up quickly (no driver-side retries, 5s to connect)
    and this loop does the retrying, so the deadline is what bounds the wait.
    """
    deadline = time.monotonic() + timeout_seconds
    last_error = None

    while time.monotonic() < deadline:
        driver = neo4j.GraphDatabase.driver(
            uri,
            connection_timeout=5,
            max_transaction_retry_time=0,
        )
        try:
            driver.execute_query("RETURN 1")
            return
        # This branch only executes if the container is still booting.
        except Exception as exc:  # pragma: no cover
            last_error = exc
            time.sleep(1)
        finally:
            driver.close()

    raise RuntimeError(
        f"Neo4j did not become ready in {timeout_seconds}s"
    ) from last_error


@pytest.fixture(scope="session", autouse=True)
def neo4j_url():
    configured_neo4j_url = os.environ.get("NEO4J_URL")
    if configured_neo4j_url:
        logger.info(
            "Using externally configured Neo4j instance at %s", configured_neo4j_url
        )
        _wait_for_neo4j(configured_neo4j_url)
        yield configured_neo4j_url
        return

    image = settings.get("NEO4J_DOCKER_IMAGE")
    logger.info("Starting Neo4j testcontainer using image %s", image)
    container = (
        DockerContainer(image).with_exposed_ports(7687).with_env("NEO4J_AUTH", "none")
    )

    with container as started_container:
        container_url = (
            f"bolt://{started_container.get_container_host_ip()}:"
            f"{started_container.get_exposed_port(7687)}"
        )
        _wait_for_neo4j(container_url)
        os.environ["NEO4J_URL"] = container_url

        try:
            yield container_url
        finally:
            os.environ.pop("NEO4J_URL", None)


@pytest.fixture(scope="module")
def neo4j_session(neo4j_url):
    driver = neo4j.GraphDatabase.driver(neo4j_url)
    with driver.session() as session:
        yield session
        session.run("MATCH (n) DETACH DELETE n;")
    driver.close()
