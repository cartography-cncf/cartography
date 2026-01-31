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

from cartography.graph.querybuilder import build_conditional_label_queries
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
_MAX_BUFFER_ERROR_RETRIES = 5
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


def _is_retryable_buffer_error(exc: Exception) -> bool:
    """
    Determine if a BufferError should be retried.

    BufferError with "cannot be re-sized" occurs during multi-threaded Neo4j
    operations when the underlying buffer is accessed concurrently. This is a
    known transient error that can happen when multiple threads interact with
    the Neo4j driver's internal buffer management.

    :param exc: The exception to check
    :return: True if this is a retryable BufferError, False otherwise
    """
    if not isinstance(exc, BufferError):
        return False
    return "cannot be re-sized" in str(exc)


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


def _buffer_error_backoff_handler(details: Dict) -> None:
    """
    Custom backoff handler that provides enhanced logging for BufferError retries.

    This handler logs additional context when retrying BufferError to help
    diagnose concurrent multi-threaded operation issues.

    :param details: Backoff details dict containing 'exception', 'wait', 'tries', 'target'
    """
    exc = details.get("exception")
    if isinstance(exc, Exception) and _is_retryable_buffer_error(exc):
        wait = details.get("wait")
        wait_str = f"{wait:0.1f}" if wait is not None else "unknown"
        tries = details.get("tries", 0)

        if tries == 1:
            log_msg = (
                f"Encountered BufferError (attempt 1/{_MAX_BUFFER_ERROR_RETRIES}). "
                f"This can occur during concurrent multi-threaded Neo4j operations. "
                f"Retrying after {wait_str} seconds backoff. "
                f"Function: {details.get('target')}. Error: {details.get('exception')}"
            )
        else:
            log_msg = (
                f"BufferError retry {tries}/{_MAX_BUFFER_ERROR_RETRIES}. "
                f"Backing off {wait_str} seconds before next attempt. "
                f"Function: {details.get('target')}. Error: {details.get('exception')}"
            )

        logger.warning(log_msg)
    else:
        # Fall back to standard backoff handler for other errors
        backoff_handler(details)


def _run_with_retry(operation: Callable[[], T], target: str) -> T:
    """
    Execute the supplied callable with retry logic for transient network errors,
    EntityNotFound ClientErrors, and BufferErrors.
    """
    network_attempts = 0
    entity_attempts = 0
    buffer_attempts = 0
    network_wait = backoff.expo()
    entity_wait = backoff.expo()
    buffer_wait = backoff.expo()

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
            if buffer_attempts > 0:
                logger.info(
                    f"Successfully recovered from BufferError after {buffer_attempts} "
                    f"{'retry' if buffer_attempts == 1 else 'retries'}. Function: {target}"
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
        except BufferError as exc:
            if not _is_retryable_buffer_error(exc):
                raise
            if buffer_attempts >= _MAX_BUFFER_ERROR_RETRIES - 1:
                raise
            buffer_attempts += 1
            wait = next(buffer_wait)
            if wait is None:
                logger.error(
                    f"Unexpected: backoff generator returned None for wait time. "
                    f"target={target}, attempts={buffer_attempts}, exc={exc}"
                )
                wait = 1.0  # Fallback to 1 second wait
            _buffer_error_backoff_handler(
                {
                    "exception": exc,
                    "target": target,
                    "tries": buffer_attempts,
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
    - BufferError with "cannot be re-sized" during concurrent multi-threaded operations

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
    Execute a Neo4j query and return a list of single values.

    This function is designed for queries that return a single field per record.
    It extracts the value from each record and returns them as a list.

    Args:
        tx (neo4j.Transaction): A Neo4j read transaction object.
        query (str): A Neo4j query string that returns single values per record.
            Supported: ``MATCH (a:TestNode) RETURN a.name ORDER BY a.name``
            Not supported: ``MATCH (a:TestNode) RETURN a.name, a.age, a.x``
        **kwargs: Additional keyword arguments passed to ``tx.run()``.

    Returns:
        List[Union[str, int]]: A list of string or integer values from the query results.

    Examples:
        >>> query = "MATCH (a:TestNode) RETURN a.name ORDER BY a.name"
        >>> values = neo4j_session.execute_read(read_list_of_values_tx, query)
        >>> print(values)
        ['Alice', 'Bob', 'Charlie']

    Warning:
        If the query returns multiple fields per record, only the value of the first
        field will be returned. This is not a supported use case - ensure your query
        returns only one field per record.
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
    Execute a Neo4j query and return a single value.

    This function is designed for queries that return exactly one value (string, integer, or None).
    It's useful for retrieving specific attributes from unique nodes.

    Args:
        tx (neo4j.Transaction): A Neo4j read transaction object.
        query (str): A Neo4j query string that returns a single value. The query should
            match exactly one record with one field.
        **kwargs: Additional keyword arguments passed to ``tx.run()``.

    Returns:
        Optional[Union[str, int]]: The single value returned by the query, or None if
            no record was found.

    Examples:
        >>> query = '''MATCH (a:TestNode{name: "Lisa"}) RETURN a.age'''
        >>> value = neo4j_session.read_transaction(read_single_value_tx, query)
        >>> print(value)
        8

    Warning:
        - If the query matches multiple records, only the first value will be returned.
        - If the query returns complex objects or dictionaries, the behavior is undefined.
        - Ensure your query is specific enough to match exactly one record.

    See Also:
        For complex return types, use ``read_single_dict_tx()`` or ``read_list_of_dicts_tx()``.
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
    Execute a Neo4j query and return results as a list of dictionaries.

    This function converts each record from the query result into a dictionary,
    making it easy to work with structured data from Neo4j.

    Args:
        tx (neo4j.Transaction): A Neo4j read transaction object.
        query (str): A Neo4j query string that returns one or more fields per record.
        **kwargs: Additional keyword arguments passed to ``tx.run()``.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents
            one record from the query result. Keys are the field names from the RETURN
            clause, and values are the corresponding data.

    Examples:
        >>> query = "MATCH (a:TestNode) RETURN a.name AS name, a.age AS age ORDER BY age"
        >>> data = neo4j_session.read_transaction(read_list_of_dicts_tx, query)
        >>> print(data)
        [{'name': 'Lisa', 'age': 8}, {'name': 'Homer', 'age': 39}]

        >>> # Easy iteration over structured data
        >>> for person in data:
        ...     print(f"{person['name']} is {person['age']} years old")
        Lisa is 8 years old
        Homer is 39 years old
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
    Execute a Neo4j query and return results as a list of tuples.

    This function converts each record from the query result into a tuple,
    which is useful for unpacking values during iteration and can be more
    memory-efficient than dictionaries.

    Args:
        tx (neo4j.Transaction): A Neo4j read transaction object.
        query (str): A Neo4j query string that returns one or more fields per record.
        **kwargs: Additional keyword arguments passed to ``tx.run()``.

    Returns:
        List[Tuple[Any, ...]]: A list of tuples, where each tuple represents one
            record from the query result. Values are ordered according to the
            RETURN clause in the query.

    Examples:
        >>> query = "MATCH (a:TestNode) RETURN a.name AS name, a.age AS age ORDER BY age"
        >>> data = neo4j_session.read_transaction(read_list_of_tuples_tx, query)
        >>> print(data)
        [('Lisa', 8), ('Homer', 39)]

        >>> # Easy unpacking during iteration
        >>> for name, age in data:
        ...     print(f"{name} is {age} years old")
        Lisa is 8 years old
        Homer is 39 years old

    Note:
        The advantage of this function over ``read_list_of_dicts_tx()`` is that tuples
        allow for easy unpacking during iteration and use less memory than dictionaries.
    """
    result: neo4j.BoltStatementResult = tx.run(query, kwargs)
    values: List[Any] = result.values()
    result.consume()
    # All neo4j APIs return List type- https://neo4j.com/docs/api/python-driver/current/api.html#result - so we do this:
    return [tuple(val) for val in values]


def read_single_dict_tx(tx: neo4j.Transaction, query: str, **kwargs) -> Any:
    """
    Execute a Neo4j query and return a single dictionary result.

    This function is designed for queries that return exactly one record with
    multiple fields, converting the result into a dictionary.

    Args:
        tx (neo4j.Transaction): A Neo4j read transaction object.
        query (str): A Neo4j query string that returns a single record with one or
            more fields. The query should match exactly one record.
        **kwargs: Additional keyword arguments passed to ``tx.run()``.

    Returns:
        Any: A dictionary representing the single record from the query result,
            or None if no record was found. Keys are field names from the RETURN
            clause, and values are the corresponding data.

    Examples:
        >>> query = '''MATCH (a:TestNode{name: "Homer"}) RETURN a.name AS name, a.age AS age'''
        >>> result = neo4j_session.read_transaction(read_single_dict_tx, query)
        >>> print(result)
        {'name': 'Homer', 'age': 39}

    Warning:
        - If the query matches multiple records, only the first record will be returned.
        - For multiple records, use ``read_list_of_dicts_tx()`` instead.
        - Ensure your query is specific enough to match exactly one record.
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
    Execute a Neo4j write query with a list of dictionaries.

    This function is designed to work with queries that process batches of data
    using the UNWIND clause, allowing efficient bulk operations on Neo4j.

    Args:
        tx (neo4j.Transaction): A Neo4j write transaction object.
        query (str): A Neo4j write query string that typically uses UNWIND to process
            the ``$DictList`` parameter. The query should contain data manipulation
            operations like MERGE, CREATE, or SET.
        **kwargs: Additional keyword arguments passed to the Neo4j query, including
            the ``DictList`` parameter containing the data to process.

    Examples:
        >>> import neo4j
        >>> dict_list = [
        ...     {'id': 1, 'name': 'Alice', 'age': 30},
        ...     {'id': 2, 'name': 'Bob', 'age': 25}
        ... ]
        >>>
        >>> neo4j_session.execute_write(
        ...     write_list_of_dicts_tx,
        ...     '''
        ...     UNWIND $DictList as data
        ...         MERGE (a:Person{id: data.id})
        ...         SET
        ...             a.name = data.name,
        ...             a.age = data.age,
        ...             a.updated_at = $timestamp
        ...     ''',
        ...     DictList=dict_list,
        ...     timestamp=datetime.now()
        ... )

    Note:
        This function is typically used internally by higher-level functions like
        ``load_graph_data()`` rather than being called directly by user code.
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
    Load data to the graph using batched operations.

    This function processes large datasets by splitting them into manageable batches
    and executing write transactions for each batch. This approach prevents memory
    issues and improves performance for large data loads.

    This function handles retries for:
    - Network errors (ConnectionResetError)
    - Service unavailability (ServiceUnavailable, SessionExpired)
    - Transient database errors (TransientError)
    - EntityNotFound errors during concurrent operations (ClientError with specific code)
    - BufferError with "cannot be re-sized" during concurrent multi-threaded operations

    EntityNotFound errors are retried because they commonly occur during concurrent
    write operations when multiple threads access the same node space. This is expected
    behavior in Neo4j's query execution pipeline, not a permanent failure.

    Args:
        neo4j_session (neo4j.Session): The Neo4j session for database operations.
        query (str): The Neo4j write query to execute. This query should be generated
            using ``cartography.graph.querybuilder.build_ingestion_query()`` rather
            than being handwritten to ensure proper formatting and security.
        dict_list (List[Dict[str, Any]]): The data to load to the graph, represented
            as a list of dictionaries. Each dictionary represents one record to process.
        batch_size (int): The number of items to process per transaction. Defaults to 10000.
        **kwargs: Additional keyword arguments passed to the Neo4j query.

    Examples:
        >>> # Generated query from querybuilder
        >>> query = build_ingestion_query(node_schema)
        >>> data = [
        ...     {'id': 'user1', 'name': 'Alice', 'email': 'alice@example.com'},
        ...     {'id': 'user2', 'name': 'Bob', 'email': 'bob@example.com'}
        ... ]
        >>> load_graph_data(session, query, data, lastupdated=current_time)

    Note:
        - Data is processed in batches of 10,000 records to optimize memory usage
          and transaction performance.
        - This function is typically called by higher-level functions like ``load()``
          rather than directly by user code.
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
    Create indexes for efficient node and relationship matching.

    This function creates indexes for the given CartographyNodeSchema object,
    including indexes for all relationships defined in its ``other_relationships``
    and ``sub_resource_relationship`` fields. This operation is idempotent and
    safe to run multiple times.

    Args:
        neo4j_session (neo4j.Session): The Neo4j session for database operations.
        node_schema (CartographyNodeSchema): The node schema object to create
            indexes for. This defines which properties need indexing.

    Raises:
        ValueError: If any generated query doesn't start with "CREATE INDEX IF NOT EXISTS",
            indicating a potential security issue with the query generation.

    Examples:
        >>> node_schema = CartographyNodeSchema(
        ...     label='AWSUser',
        ...     properties={'id': PropertyRef('UserId'), 'name': PropertyRef('UserName')},
        ...     sub_resource_relationship=make_target_node_matcher({'account_id': PropertyRef('AccountId')})
        ... )
        >>> ensure_indexes(session, node_schema)

    Note:
        - This ensures that every MATCH operation on nodes will be indexed, making
          relationship creation and queries fast.
        - The ``id`` and ``lastupdated`` properties automatically have indexes created.
        - All properties included in target node matchers automatically have indexes created.
        - This function should be called before performing any data loading operations.
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
    Create indexes for efficient relationship matching between existing nodes.

    This function creates indexes for node fields referenced in the given
    CartographyRelSchema object. It's specifically designed for matchlink operations
    where relationships are created between existing nodes.

    Args:
        neo4j_session (neo4j.Session): The Neo4j session for database operations.
        rel_schema (CartographyRelSchema): The relationship schema object to create
            indexes for. This defines which node properties need indexing for
            efficient relationship matching.

    Raises:
        ValueError: If any generated query doesn't start with "CREATE INDEX IF NOT EXISTS",
            indicating a potential security issue with the query generation.

    Note:
        - This function is only used for ``load_matchlinks()`` operations where
          we match and connect existing nodes.
        - It's not used for CartographyNodeSchema objects - use ``ensure_indexes()``
          for those instead.
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
    Load node data to the graph with automatic indexing.

    This is the main entry point for intel modules to write node data to the graph.
    It automatically ensures that required indexes exist before performing the load
    operation, optimizing performance and maintaining data integrity.

    Args:
        neo4j_session (neo4j.Session): The Neo4j session for database operations.
        node_schema (CartographyNodeSchema): The node schema object that defines
            the structure of the data being loaded and generates the ingestion query.
        dict_list (List[Dict[str, Any]]): The data to load to the graph, represented
            as a list of dictionaries. Each dictionary represents one node to create
            or update.
        batch_size (int): The number of items to process per transaction. Defaults to 10000.
        **kwargs: Additional keyword arguments passed to the Neo4j query, such as
            timestamps, update tags, or other metadata.

    Examples:
        >>> node_schema = CartographyNodeSchema(
        ...     label='AWSUser',
        ...     properties={
        ...         'id': PropertyRef('UserId'),
        ...         'name': PropertyRef('UserName'),
        ...         'email': PropertyRef('Email')
        ...     }
        ... )
        >>> users_data = [
        ...     {'UserId': 'user1', 'UserName': 'Alice', 'Email': 'alice@example.com'},
        ...     {'UserId': 'user2', 'UserName': 'Bob', 'Email': 'bob@example.com'}
        ... ]
        >>> load(session, node_schema, users_data, lastupdated=current_time)

    Note:
        - If ``dict_list`` is empty, the function returns early to save processing time.
        - The function automatically creates necessary indexes before loading data.
        - The ingestion query is generated automatically from the node schema.
        - Data is processed in batches for optimal performance.
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

    # Apply conditional labels if any are defined
    # Pass kwargs to provide sub-resource parameters (e.g., AWS_ID) for scoped queries
    conditional_label_queries = build_conditional_label_queries(node_schema)
    for query in conditional_label_queries:
        run_write_query(neo4j_session, query, **kwargs)


def load_matchlinks(
    neo4j_session: neo4j.Session,
    rel_schema: CartographyRelSchema,
    dict_list: list[dict[str, Any]],
    batch_size: int = 10000,
    **kwargs,
) -> None:
    """
    Create relationships between existing nodes in the graph.

    This is the main entry point for intel modules to write relationships between
    two existing nodes. It ensures proper indexing and executes the relationship
    creation query.

    Args:
        neo4j_session (neo4j.Session): The Neo4j session for database operations.
        rel_schema (CartographyRelSchema): The relationship schema object used to
            generate the query and define the relationship structure.
        dict_list (list[dict[str, Any]]): The data for creating relationships,
            represented as a list of dictionaries. Each dictionary must contain
            the source and target node identifiers.
        batch_size (int): The number of items to process per transaction. Defaults to 10000.
        **kwargs: Additional keyword arguments passed to the Neo4j query.
            Must include ``_sub_resource_label`` and ``_sub_resource_id`` for
            cleanup queries.

    Raises:
        ValueError: If required kwargs ``_sub_resource_label`` or ``_sub_resource_id``
            are not provided. These are needed for cleanup queries.

    Note:
        - If ``dict_list`` is empty, the function returns early to save processing time.
        - The function automatically ensures that required indexes exist for efficient
          relationship creation.
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
