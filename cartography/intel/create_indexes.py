import logging
from typing import List

import neo4j

from cartography.client.core.tx import run_write_query
from cartography.config import Config
from cartography.intel.deprecated_indexes import drop_deprecated_matchlink_rel_indexes
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
    # DEPRECATED: drop this call (and cartography.intel.deprecated_indexes) in v1.0.0. MatchLink
    # relationship indexes are created lazily by ensure_indexes_for_matchlinks() rather than from
    # indexes.cypher, but this stage runs first and exactly once, so it is the only place where we
    # can drop the old churning index shape without racing a module that recreates the new one.
    drop_deprecated_matchlink_rel_indexes(neo4j_session)

    logger.info("Creating indexes for cartography node types.")
    for statement in get_index_statements():
        logger.debug("Executing statement: %s", statement)
        run_write_query(neo4j_session, statement)
