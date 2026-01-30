import logging
from typing import List

import neo4j

from cartography.client.core.tx import run_write_query
from cartography.config import Config
from cartography.util import load_resource_binary

logger = logging.getLogger(__name__)


def get_index_statements() -> List[str]:
    statements = []
    with load_resource_binary("cartography.data", "indexes.cypher") as f:
        for line in f.readlines():
            statements.append(
                line.decode("UTF-8").rstrip("\r\n"),
            )
    return statements


def run(neo4j_session: neo4j.Session, config: Config) -> None:
    logger.info("Creating indexes for cartography node types.")
    for statement in get_index_statements():
        logger.debug("Executing statement: %s", statement)
        run_write_query(neo4j_session, statement)
