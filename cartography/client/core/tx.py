import logging
import time
from functools import partial
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import TypeVar
from typing import Union

import backoff
import neo4j
import neo4j.exceptions

from cartography.graph.querybuilder import build_create_index_queries
from cartography.graph.querybuilder import build_create_index_queries_for_matchlink
from cartography.graph.querybuilder import build_ingestion_query
from cartography.graph.querybuilder import build_matchlink_query
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema
from cartography.util import backoff_handler
from cartography.util import batch

logger = logging.getLogger(__name__)

T = TypeVar("T")

_MAX_NETWORK_RETRIES = 5
_MAX_ENTITY_NOT_FOUND_RETRIES = 5
_NETWORK_EXCEPTIONS: tuple[type[BaseException], ...] = (
    ConnectionResetError,
    neo4j.exceptions.ServiceUnavailable,
    neo4j.exceptions.SessionExpired,
    neo4j.exceptions.TransientError,
)


def _is_retryable_client_error(exc: Exception) -> bool:
    """
    Determine if a ClientError should be retried.

    EntityNotFound during concurrent write operations is a known transient error in Neo4j
    that occurs due to the database's query execution pipeline design. When multiple threads
    run concurrent MERGE/DELETE operations, one thread can delete an entity that another
    thread has already referenced but hasn't locked yet.

    Neo4j maintainers explicitly recommend retrying EntityNotFound errors during
    multi-threaded operations, even though the driver classifies it as a non-retryable
    ClientError. See: https://github.com/neo4j/neo4j/issues/6823

    This is particularly common in Cartography when:
    - Multiple providers sync concurrently (e.g., AWS + GCP + Okta)
    - Large batch sizes (10,000 nodes per transaction) are used
    - Page cache evictions occur under memory pressure (especially in Aura)
    - Concurrent MERGE and DETACH DELETE operations overlap

    :param exc: The exception to check
    :return: True if this is a retryable ClientError (EntityNotFound), False otherwise
    """
    if not isinstance(exc, neo4j.exceptions.ClientError):
        return False

    # Only retry EntityNotFound errors - all other ClientErrors are permanent failures
    # Note: exc.code can be None for locally-created errors (per neo4j driver docs)
    code = exc.code
    if code is None:
        return False
    return code == "Neo.ClientError.Statement.EntityNotFound"


def _entity_not_found_backoff_handler(details: Dict) -> None:
    """
    Custom backoff handler that provides enhanced logging for EntityNotFound retries.

    This handler logs additional context when retrying EntityNotFound errors to help
    diagnose concurrent write issues and page cache pressure in Neo4j.

    :param details: Backoff details dict containing 'exception', 'wait', 'tries', 'target'
    """
    exc = details.get("exception")
    if isinstance(exc, Exception) and _is_retryable_client_error(exc):
        wait = details.get("wait")
        wait_str = f"{wait:0.1f}" if wait is not None else "unknown"
        tries = details.get("tries", 0)

        if tries == 1:
            log_msg = (
                f"Encountered EntityNotFound error (attempt 1/{_MAX_ENTITY_NOT_FOUND_RETRIES}). "
                f"This is expected during concurrent write operations. "
                f"Retrying after {wait_str} seconds backoff. "
                f"Function: {details.get('target')}. Error: {details.get('exception')}"
            )
        else:
            log_msg = (
                f"EntityNotFound retry {tries}/{_MAX_ENTITY_NOT_FOUND_RETRIES}. "
                f"Backing off {wait_str} seconds before next attempt. "
                f"Function: {details.get('target')}. Error: {details.get('exception')}"
            )

        logger.warning(log_msg)
    else:
        # Fall back to standard backoff handler for other errors
        backoff_handler(details)


def _run_with_retry(operation: Callable[[], T], target: str) -> T:
    """
    Execute the supplied callable with retry logic for transient network errors and
    EntityNotFound ClientErrors.
    """
    network_attempts = 0
    entity_attempts = 0
    network_wait = backoff.expo()
    entity_wait = backoff.expo()

    while True:
        try:
            result = operation()
            # Log success if we recovered from errors
            if network_attempts > 0:
                logger.info(
                    f"Successfully recovered from network error after {network_attempts} "
                    f"{'retry' if network_attempts == 1 else 'retries'}. Function: {target}"
                )
            if entity_attempts > 0:
                logger.info(
                    f"Successfully recovered from EntityNotFound error after {entity_attempts} "
                    f"{'retry' if entity_attempts == 1 else 'retries'}. Function: {target}"
                )
            return result
        except _NETWORK_EXCEPTIONS as exc:
            if network_attempts >= _MAX_NETWORK_RETRIES - 1:
                raise
            network_attempts += 1
            wait = next(network_wait)
            if wait is None:
                logger.error(
                    f"Unexpected: backoff generator returned None for wait time. "
                    f"target={target}, attempts={network_attempts}, exc={exc}"
                )
                wait = 1.0  # Fallback to 1 second wait
            backoff_handler(
                {
                    "exception": exc,
                    "target": target,
                    "tries": network_attempts,
                    "wait": wait,
                }
            )
            time.sleep(wait)
            continue
        except neo4j.exceptions.ClientError as exc:
            if not _is_retryable_client_error(exc):
                raise
            if entity_attempts >= _MAX_ENTITY_NOT_FOUND_RETRIES - 1:
                raise
            entity_attempts += 1
            wait = next(entity_wait)
            if wait is None:
                logger.error(
                    f"Unexpected: backoff generator returned None for wait time. "
                    f"target={target}, attempts={entity_attempts}, exc={exc}"
                )
                wait = 1.0  # Fallback to 1 second wait
            _entity_not_found_backoff_handler(
                {
                    "exception": exc,
                    "target": target,
                    "tries": entity_attempts,
                    "wait": wait,
                }
            )
            time.sleep(wait)
            continue


@backoff.on_exception(  # type: ignore
    backoff.expo,
    (
        ConnectionResetError,
        neo4j.exceptions.ServiceUnavailable,
        neo4j.exceptions.SessionExpired,
        neo4j.exceptions.TransientError,
    ),
    max_tries=5,
    on_backoff=backoff_handler,
)
def _run_index_query_with_retry(neo4j_session: neo4j.Session, query: str) -> None:
    """
    Execute an index creation query with retry logic.
    Index creation requires autocommit transactions and can experience transient errors.

    Handles the EquivalentSchemaRuleAlreadyExists error that can occur when multiple
    parallel sync operations attempt to create the same index simultaneously. Even though
    we use CREATE INDEX IF NOT EXISTS, Neo4j has a race condition where concurrent
    index creation can fail if another session creates the index between the existence
    check and the actual creation.
    """
    try:
        neo4j_session.run(query)
    except neo4j.exceptions.ClientError as e:
        # EquivalentSchemaRuleAlreadyExists means another parallel sync already created
        # this index, which is the desired end state. Safe to ignore.
        if e.code == "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
            logger.debug(
                f"Index already exists (likely created by parallel sync): {query}"
            )
            return
        raise


def execute_write_with_retry(
    neo4j_session: neo4j.Session,
    tx_func: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """
    Execute a custom transaction function with retry logic for transient errors.

    This is a generic wrapper for any custom transaction function that needs retry logic
    for EntityNotFound and other transient errors. Use this when you have complex
    transaction logic that doesn't fit the standard load_graph_data pattern.

    Example usage:
        def my_custom_tx(tx, data_list, update_tag):
            for item in data_list:
                tx.run(query, **item).consume()

        execute_write_with_retry(
            neo4j_session,
            my_custom_tx,
            data_list,
            update_tag
        )

    :param neo4j_session: The Neo4j session
    :param tx_func: The transaction function to execute (takes neo4j.Transaction as first arg)
    :param args: Positional arguments to pass to tx_func
    :param kwargs: Keyword arguments to pass to tx_func
    :return: The return value of tx_func
    """

    target = getattr(tx_func, "__qualname__", repr(tx_func))
    operation = partial(neo4j_session.execute_write, tx_func, *args, **kwargs)
    return _run_with_retry(operation, target)


def run_write_query(
    neo4j_session: neo4j.Session, query: str, **parameters: Any
) -> None:
    """
    Execute a write query inside a managed transaction with retry logic.

    This function now includes retry logic for:
    - Network errors (ConnectionResetError)
    - Service unavailability (ServiceUnavailable, SessionExpired)
    - Transient database errors (TransientError)
    - EntityNotFound errors during concurrent operations (specific ClientError)

    Used by intel modules that run manual transactions (e.g., GCP firewalls, AWS resources).

    :param neo4j_session: The Neo4j session
    :param query: The Cypher query to execute
    :param parameters: Parameters to pass to the query
    :return: None
    """

    def _run_query_tx(tx: neo4j.Transaction) -> None:
        tx.run(query, **parameters).consume()

    def _operation() -> None:
        neo4j_session.execute_write(_run_query_tx)

    _run_with_retry(_operation, _run_query_tx.__qualname__)


def read_list_of_values_tx(
    tx: neo4j.Transaction,
    query: str,
    **kwargs,
) -> List[Union[str, int]]:
    """
    Runs the given Neo4j query in the given transaction object and returns a list of either str or int. This is intended
    to be run only with queries that return a list of a single field.

    Example usage:
        query = "MATCH (a:TestNode) RETURN a.name ORDER BY a.name"

        values = neo4j_session.execute_read(read_list_of_values_tx, query)

    :param tx: A neo4j read transaction object
    :param query: A neo4j query string that returns a list of single values. For example,
        `MATCH (a:TestNode) RETURN a.name ORDER BY a.name` is intended to work, but
        `MATCH (a:TestNode) RETURN a.name ORDER BY a.name, a.age, a.x, a.y, a.z` is not.
        If the query happens to return a list of complex objects with more than one field, then only the value of the
        first field of each item in the list will be returned. This is not a supported scenario for this function though
        so please ensure that the `query` does return a list of single values.
    :param kwargs: kwargs that are passed to tx.run()'s kwargs argument.
    :return: A list of str or int.
    """
    result: neo4j.BoltStatementResult = tx.run(query, kwargs)
    values = [n.value() for n in result]
    result.consume()
    return values


def read_single_value_tx(
    tx: neo4j.Transaction,
    query: str,
    **kwargs,
) -> Optional[Union[str, int]]:
    """
    Runs the given Neo4j query in the given transaction object and returns a str, int, or None. This is intended to be
    run only with queries that return a single str, int, or None value.

    Example usage:
        query = '''MATCH (a:TestNode{name: "Lisa"}) RETURN a.age'''  # Ensure that we are querying just one node!

        value = neo4j_session.read_transaction(read_single_value_tx, query)

    :param tx: A neo4j read transaction object
    :param query: A neo4j query string that returns a single value. For example,
        `MATCH (a:TestNode{name: "Lisa"}) RETURN a.age` is intended to work (assuming that there is only one `TestNode`
         where `name=Lisa`), but
        `MATCH (a:TestNode) RETURN a.age ORDER BY a.age` is not (assuming that there is more than one `TestNode` in the
        graph. If the query happens to match more than one value, only the first one will be returned. If the query
        happens to return a dictionary or complex object, this scenario is not supported and can result in unpredictable
        behavior. Be careful in selecting the query.
        To return more complex objects, see the "*dict*" or the "*tuple*" functions in this library.
    :param kwargs: kwargs that are passed to tx.run()'s kwargs argument.
    :return: The result of the query as a single str, int, or None
    """
    result: neo4j.BoltStatementResult = tx.run(query, kwargs)
    record: neo4j.Record = result.single()

    value = record.value() if record else None

    result.consume()
    return value


def read_list_of_dicts_tx(
    tx: neo4j.Transaction,
    query: str,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    Runs the given Neo4j query in the given transaction object and returns the results as a list of dicts.

    Example usage:
        query = "MATCH (a:TestNode) RETURN a.name AS name, a.age AS age ORDER BY age"

        data = neo4j_session.read_transaction(read_list_of_dicts_tx, query)

        # expected returned data shape -> data = [{'name': 'Lisa', 'age': 8}, {'name': 'Homer', 'age': 39}]

    :param tx: A neo4j read transaction object
    :param query: A neo4j query string that returns one or more values.
    :param kwargs: kwargs that are passed to tx.run()'s kwargs argument.
    :return: The result of the query as a list of dicts.
    """
    result: neo4j.BoltStatementResult = tx.run(query, kwargs)
    values = [n.data() for n in result]
    result.consume()
    return values


def read_list_of_tuples_tx(
    tx: neo4j.Transaction,
    query: str,
    **kwargs,
) -> List[Tuple[Any, ...]]:
    """
    Runs the given Neo4j query in the given transaction object and returns the results as a list of tuples.

    Example usage:
        ```
        query = "MATCH (a:TestNode) RETURN a.name AS name, a.age AS age ORDER BY age"

        simpsons_characters = neo4j_session.read_transaction(read_list_of_tuples_tx, query)

        # expected returned data shape -> simpsons_characters = [('Lisa', 8), ('Homer', 39)]

        # The advantage of this function over `read_list_of_dicts_tx()` is that you can now run things like this:

        for name, age in simpsons_characters:
            print(name, age)
        ```

    :param tx: A neo4j read transaction object
    :param query: A neo4j query string that returns one or more values.
    :param kwargs: kwargs that are passed to tx.run()'s kwargs argument.
    :return: The result of the query as a list of tuples.
    """
    result: neo4j.BoltStatementResult = tx.run(query, kwargs)
    values: List[Any] = result.values()
    result.consume()
    # All neo4j APIs return List type- https://neo4j.com/docs/api/python-driver/current/api.html#result - so we do this:
    return [tuple(val) for val in values]


def read_single_dict_tx(tx: neo4j.Transaction, query: str, **kwargs) -> Any:
    """
    Runs the given Neo4j query in the given transaction object and returns the single dict result. This is intended to
    be run only with queries that return a single dict.

    Example usage:
        query = '''MATCH (a:TestNode{name: "Homer"}) RETURN a.name AS name, a.age AS age'''
        result = neo4j_session.read_transaction(read_single_dict_tx, query)

        # expected returned data shape -> result = {'name': 'Lisa', 'age': 8}

    :param tx: A neo4j read transaction object
    :param query: A neo4j query string that returns a single dict. For example,
        `MATCH (a:TestNode{name: "Lisa"}) RETURN a.age, a.name` is intended to work (assuming that there is only one
        `TestNode` where `name=Lisa`), but
        `MATCH (a:TestNode) RETURN a.age ORDER BY a.age, a.name` is not (assuming that there is more than one `TestNode`
        in the graph. If the query happens to match more than one node, only the first one will be returned.
        If the query happens to return more than one dict, only the first dict will be returned however
        `read_list_of_dicts_tx()` is better suited for this use-case.
    :param kwargs: kwargs that are passed to tx.run()'s kwargs argument.
    :return: The result of the query as a single dict.
    """
    result: neo4j.BoltStatementResult = tx.run(query, kwargs)
    record: neo4j.Record = result.single()

    value = record.data() if record else None

    result.consume()
    return value


def write_list_of_dicts_tx(
    tx: neo4j.Transaction,
    query: str,
    **kwargs,
) -> None:
    """
    Writes a list of dicts to Neo4j.

    Example usage:
        import neo4j
        dict_list: List[Dict[Any, Any]] = [{...}, ...]

        neo4j_driver = neo4j.driver(... args ...)
        neo4j_session = neo4j_driver.Session(... args ...)

        neo4j_session.execute_write(
            write_list_of_dicts_tx,
            '''
            UNWIND $DictList as data
                MERGE (a:SomeNode{id: data.id})
                SET
                    a.other_field = $other_field,
                    a.yet_another_kwarg_field = $yet_another_kwarg_field
                ...
            ''',
            DictList=dict_list,
            other_field='some extra value',
            yet_another_kwarg_field=1234
        )

    :param tx: The neo4j write transaction.
    :param query: The Neo4j write query to run.
    :param kwargs: Keyword args to be supplied to the Neo4j query.
    :return: None
    """
    tx.run(query, kwargs).consume()


def load_graph_data(
    neo4j_session: neo4j.Session,
    query: str,
    dict_list: List[Dict[str, Any]],
    batch_size: int = 10000,
    **kwargs,
) -> None:
    """
    Writes data to the graph with retry logic for transient errors.

    This function handles retries for:
    - Network errors (ConnectionResetError)
    - Service unavailability (ServiceUnavailable, SessionExpired)
    - Transient database errors (TransientError)
    - EntityNotFound errors during concurrent operations (ClientError with specific code)

    EntityNotFound errors are retried because they commonly occur during concurrent
    write operations when multiple threads access the same node space. This is expected
    behavior in Neo4j's query execution pipeline, not a permanent failure.

    :param neo4j_session: The Neo4j session
    :param query: The Neo4j write query to run. This query is not meant to be handwritten, rather it should be generated
    with cartography.graph.querybuilder.build_ingestion_query().
    :param dict_list: The data to load to the graph represented as a list of dicts.
    :param batch_size: The number of items to process per transaction. Defaults to 10000.
    :param kwargs: Allows additional keyword args to be supplied to the Neo4j query.
    :return: None
    """
    if batch_size <= 0:
        raise ValueError(f"batch_size must be greater than 0, got {batch_size}")

    for data_batch in batch(dict_list, size=batch_size):
        execute_write_with_retry(
            neo4j_session,
            write_list_of_dicts_tx,
            query,
            DictList=data_batch,
            **kwargs,
        )


def ensure_indexes(
    neo4j_session: neo4j.Session,
    node_schema: CartographyNodeSchema,
) -> None:
    """
    Creates indexes if they don't exist for the given CartographyNodeSchema object, as well as for all of the
    relationships defined on its `other_relationships` and `sub_resource_relationship` fields. This operation is
    idempotent.

    This ensures that every time we need to MATCH on a node to draw a relationship to it, the field used for the MATCH
    will be indexed, making the operation fast.
    :param neo4j_session: The neo4j session
    :param node_schema: The node_schema object to create indexes for.
    """
    queries = build_create_index_queries(node_schema)

    for query in queries:
        if not query.startswith("CREATE INDEX IF NOT EXISTS"):
            raise ValueError(
                'Query provided to `ensure_indexes()` does not start with "CREATE INDEX IF NOT EXISTS".',
            )
        _run_index_query_with_retry(neo4j_session, query)


def ensure_indexes_for_matchlinks(
    neo4j_session: neo4j.Session,
    rel_schema: CartographyRelSchema,
) -> None:
    """
    Creates indexes for node fields if they don't exist for the given CartographyRelSchema object.
    This is only used for load_rels() where we match on and connect existing nodes.
    This is not used for CartographyNodeSchema objects.
    """
    queries = build_create_index_queries_for_matchlink(rel_schema)
    logger.debug(f"CREATE INDEX queries for {rel_schema.rel_label}: {queries}")
    for query in queries:
        if not query.startswith("CREATE INDEX IF NOT EXISTS"):
            raise ValueError(
                'Query provided to `ensure_indexes_for_matchlinks()` does not start with "CREATE INDEX IF NOT EXISTS".',
            )
        _run_index_query_with_retry(neo4j_session, query)


def load(
    neo4j_session: neo4j.Session,
    node_schema: CartographyNodeSchema,
    dict_list: List[Dict[str, Any]],
    batch_size: int = 10000,
    **kwargs,
) -> None:
    """
    Main entrypoint for intel modules to write data to the graph. Ensures that indexes exist for the datatypes loaded
    to the graph and then performs the load operation.
    :param neo4j_session: The Neo4j session
    :param node_schema: The CartographyNodeSchema object to create indexes for and generate a query.
    :param dict_list: The data to load to the graph represented as a list of dicts.
    :param batch_size: The number of items to process per transaction. Defaults to 10000.
    :param kwargs: Allows additional keyword args to be supplied to the Neo4j query.
    :return: None
    """
    if batch_size <= 0:
        raise ValueError(f"batch_size must be greater than 0, got {batch_size}")
    if len(dict_list) == 0:
        # If there is no data to load, save some time.
        return
    ensure_indexes(neo4j_session, node_schema)
    ingestion_query = build_ingestion_query(node_schema)
    load_graph_data(
        neo4j_session, ingestion_query, dict_list, batch_size=batch_size, **kwargs
    )


def load_matchlinks(
    neo4j_session: neo4j.Session,
    rel_schema: CartographyRelSchema,
    dict_list: list[dict[str, Any]],
    batch_size: int = 10000,
    **kwargs,
) -> None:
    """
    Main entrypoint for intel modules to write relationships to the graph between two existing nodes.
    :param neo4j_session: The Neo4j session
    :param rel_schema: The CartographyRelSchema object to generate a query.
    :param dict_list: The data to load to the graph represented as a list of dicts. The dicts must contain the source and
    target node ids.
    :param batch_size: The number of items to process per transaction. Defaults to 10000.
    :param kwargs: Allows additional keyword args to be supplied to the Neo4j query.
    :return: None
    """
    if batch_size <= 0:
        raise ValueError(f"batch_size must be greater than 0, got {batch_size}")
    if len(dict_list) == 0:
        # If there is no data to load, save some time.
        return

    # Validate that required kwargs are provided for cleanup queries
    if "_sub_resource_label" not in kwargs:
        raise ValueError(
            f"Required kwarg '_sub_resource_label' not provided for {rel_schema.rel_label}. "
            "This is needed for cleanup queries."
        )
    if "_sub_resource_id" not in kwargs:
        raise ValueError(
            f"Required kwarg '_sub_resource_id' not provided for {rel_schema.rel_label}. "
            "This is needed for cleanup queries."
        )

    ensure_indexes_for_matchlinks(neo4j_session, rel_schema)
    matchlink_query = build_matchlink_query(rel_schema)
    logger.debug(f"Matchlink query: {matchlink_query}")
    load_graph_data(
        neo4j_session, matchlink_query, dict_list, batch_size=batch_size, **kwargs
    )
