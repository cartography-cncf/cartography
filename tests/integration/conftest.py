import logging
import os
import time

import neo4j
import pytest
import requests
from testcontainers.core.container import DockerContainer

from tests.integration import settings

logging.basicConfig(level=logging.INFO)
logging.getLogger("neo4j").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def _wait_for_database(
    uri: str,
    *,
    auth: tuple[str, str] | None = None,
    database: str | None = None,
    timeout_seconds: int = 60,
) -> None:
    """Block until the configured graph database accepts Bolt queries."""
    deadline = time.monotonic() + timeout_seconds
    last_error = None

    while time.monotonic() < deadline:
        driver = neo4j.GraphDatabase.driver(uri, auth=auth)
        try:
            with driver.session(database=database) as session:
                session.run("RETURN 1").consume()
            return
        # This branch only executes if the container is still booting.
        except Exception as exc:  # pragma: no cover
            last_error = exc
            time.sleep(1)
        finally:
            driver.close()

    raise RuntimeError(
        f"Graph database did not become ready in {timeout_seconds}s"
    ) from last_error


def _wait_for_arcadedb_http(base_url: str, timeout_seconds: int = 60) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error = None

    while time.monotonic() < deadline:
        try:
            response = requests.get(f"{base_url}/api/v1/ready", timeout=2)
            if response.ok:
                return
        except requests.RequestException as exc:  # pragma: no cover
            last_error = exc
        time.sleep(1)

    raise RuntimeError(
        f"ArcadeDB HTTP API did not become ready in {timeout_seconds}s"
    ) from last_error


def _arcadedb_connection_settings() -> tuple[tuple[str, str], str]:
    return (
        (settings.get("ARCADEDB_USER"), settings.get("ARCADEDB_PASSWORD")),
        settings.get("ARCADEDB_DATABASE"),
    )


@pytest.fixture(scope="session")
def database_backend():
    return settings.get("DATABASE_BACKEND")


@pytest.fixture(scope="session", autouse=True)
def neo4j_url(database_backend):
    configured_neo4j_url = os.environ.get("NEO4J_URL")
    if configured_neo4j_url:
        logger.info(
            "Using externally configured %s instance at %s",
            database_backend,
            configured_neo4j_url,
        )
        auth = database = None
        if database_backend == "arcadedb":
            auth, database = _arcadedb_connection_settings()
        _wait_for_database(configured_neo4j_url, auth=auth, database=database)
        yield configured_neo4j_url
        return

    if database_backend == "arcadedb":
        image = settings.get("ARCADEDB_DOCKER_IMAGE")
        auth, database = _arcadedb_connection_settings()
        logger.info("Starting ArcadeDB testcontainer using image %s", image)
        container = (
            DockerContainer(image)
            .with_exposed_ports(2480, 7687)
            .with_env(
                "JAVA_OPTS",
                "-Darcadedb.server.rootPassword="
                f"{auth[1]} -Darcadedb.server.plugins="
                "Bolt:com.arcadedb.bolt.BoltProtocolPlugin",
            )
        )

        with container as started_container:
            host = started_container.get_container_host_ip()
            http_url = f"http://{host}:{started_container.get_exposed_port(2480)}"
            container_url = f"bolt://{host}:{started_container.get_exposed_port(7687)}"
            _wait_for_arcadedb_http(http_url)
            response = requests.post(
                f"{http_url}/api/v1/server",
                auth=auth,
                json={"command": f"create database {database}"},
                timeout=10,
            )
            response.raise_for_status()
            _wait_for_database(container_url, auth=auth, database=database)
            os.environ["NEO4J_URL"] = container_url

            try:
                yield container_url
            finally:
                os.environ.pop("NEO4J_URL", None)
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
        _wait_for_database(container_url)
        os.environ["NEO4J_URL"] = container_url

        try:
            yield container_url
        finally:
            os.environ.pop("NEO4J_URL", None)


@pytest.fixture(scope="module")
def neo4j_session(neo4j_url):
    auth = database = None
    if settings.get("DATABASE_BACKEND") == "arcadedb":
        auth, database = _arcadedb_connection_settings()
    driver = neo4j.GraphDatabase.driver(neo4j_url, auth=auth)
    with driver.session(database=database) as session:
        yield session
        session.run("MATCH (n) DETACH DELETE n;")
    driver.close()
