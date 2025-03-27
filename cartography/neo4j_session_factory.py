import logging

import neo4j

logger = logging.getLogger(__name__)


class Neo4jSessionFactory:
    _setup = False
    _driver = None
    _database = None

    def __init__(self):
        logger.info("neo4j_session_factory init")

    def initialize(self, neo4j_driver: neo4j.Driver, neo4j_database: str) -> None:
        if self._setup:
            logger.warning("Reinitializing the Neo4j session factory is not allowed; doing nothing.")
            return

        logger.info("Setting up the Neo4j session factory")

        self._setup = True
        self._driver = neo4j_driver
        self._database = neo4j_database

    def get_new_session(self) -> neo4j.Session:
        if not self._setup or not self._driver:
            raise RuntimeError(
                "Neo4j session factory is not initialized. "
                "Make sure that initialize() is called before get_new_session().",
            )

        new_session = self._driver.session(database=self._database)
        return new_session


neo4j_session_factory = Neo4jSessionFactory()
