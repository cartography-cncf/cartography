import logging
from typing import Any
from typing import Callable

import neo4j
from neo4j.exceptions import AuthError
from neo4j.exceptions import RoutingServiceUnavailable
from neo4j.exceptions import ServiceUnavailable
from neo4j.exceptions import SessionExpired
from neo4j.exceptions import TransactionError
from neo4j.exceptions import TransactionNestingError
from neo4j.exceptions import WriteServiceUnavailable


logger = logging.getLogger(__name__)

_NEO4J_WRITE_EXCEPTIONS = (
    ServiceUnavailable,
    AuthError,
    SessionExpired,
    TransactionError,
    TransactionNestingError,
    RoutingServiceUnavailable,
    WriteServiceUnavailable,
)


class Session:
    """
    A thin composition-based wrapper around neo4j.Session.

    We deliberately do NOT inherit from neo4j.Session because Neo4j 5's driver
    initialises many internal attributes (e.g. _closed) inside its own __init__,
    and skipping that call causes crashes throughout the driver internals.
    Instead we hold the real session as self.neo4j_session and delegate every
    call to it, while adding our own error-handling layer.
    """

    def __init__(self, neo4j_driver: neo4j.Driver) -> None:
        self.neo4j_session: neo4j.Session = neo4j_driver.session()

    # ------------------------------------------------------------------
    # Core query execution
    # ------------------------------------------------------------------

    def run(self, query: str, parameters: Any = None, **kwparameters: Any) -> Any:
        try:
            return self.neo4j_session.run(query, parameters, **kwparameters)
        except _NEO4J_WRITE_EXCEPTIONS as e:
            logger.warning(f"Failed run neo4j cypher query. Error - {e}", exc_info=True, stack_info=True)
        except Exception as e:
            logger.warning(f"Failed run neo4j cypher query. Error - {e}", exc_info=True, stack_info=True)
        return self

    # ------------------------------------------------------------------
    # Transaction helpers (used by cartography.graph.job / statement)
    # ------------------------------------------------------------------

    def execute_write(self, transaction_function: Callable, *args: Any, **kwargs: Any) -> Any:
        try:
            return self.neo4j_session.execute_write(transaction_function, *args, **kwargs)
        except _NEO4J_WRITE_EXCEPTIONS as e:
            logger.warning(f"Failed execute_write for neo4j. Error - {e}", exc_info=True, stack_info=True)
        except Exception as e:
            logger.warning(f"Failed execute_write for neo4j. Error - {e}", exc_info=True, stack_info=True)
        return None

    def execute_read(self, transaction_function: Callable, *args: Any, **kwargs: Any) -> Any:
        try:
            return self.neo4j_session.execute_read(transaction_function, *args, **kwargs)
        except _NEO4J_WRITE_EXCEPTIONS as e:
            logger.warning(f"Failed execute_read for neo4j. Error - {e}", exc_info=True, stack_info=True)
        except Exception as e:
            logger.warning(f"Failed execute_read for neo4j. Error - {e}", exc_info=True, stack_info=True)
        return None



    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------

    def close(self) -> None:
        self.neo4j_session.close()

    def consume(self) -> None:
        return None

    # Context-manager support so callers can do `with Session(...) as s:`
    def __enter__(self) -> "Session":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
