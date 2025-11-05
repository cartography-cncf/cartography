import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union
from typing import Iterable

import backoff
import neo4j

from cartography.graph.querybuilder import build_create_index_queries
from cartography.graph.querybuilder import build_create_index_queries_for_matchlink
from cartography.graph.querybuilder import build_ingestion_query
from cartography.graph.querybuilder import build_matchlink_query
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import LinkDirection
from cartography.util import backoff_handler
from cartography.util import batch
from cartography.sinks import file_export as file_export_sink
from dataclasses import asdict

logger = logging.getLogger(__name__)


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
    """
    neo4j_session.run(query)


def run_write_query(
    neo4j_session: neo4j.Session, query: str, **parameters: Any
) -> None:
    """Execute a write query inside a managed transaction."""

    def _run_query_tx(tx: neo4j.Transaction) -> None:
        tx.run(query, **parameters).consume()

    neo4j_session.execute_write(_run_query_tx)


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

        neo4j_session.write_transaction(
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
    tx.run(query, kwargs)


def load_graph_data(
    neo4j_session: neo4j.Session,
    query: str,
    dict_list: List[Dict[str, Any]],
    batch_size: int = 10000,
    **kwargs,
) -> None:
    """
    Writes data to the graph.
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
        neo4j_session.write_transaction(
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
    # Tee export if enabled
    if file_export_sink.is_enabled():
        _export_node_batch(node_schema, dict_list, **kwargs)

    # Optionally skip Neo4j writes for export-only runs
    if file_export_sink.is_enabled() and file_export_sink.get_no_neo4j_write():
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

    # Tee export if enabled
    if file_export_sink.is_enabled():
        _export_matchlinks_batch(rel_schema, dict_list, **kwargs)

    # Optionally skip Neo4j writes for export-only runs
    if file_export_sink.is_enabled() and file_export_sink.get_no_neo4j_write():
        return

    ensure_indexes_for_matchlinks(neo4j_session, rel_schema)
    matchlink_query = build_matchlink_query(rel_schema)
    logger.debug(f"Matchlink query: {matchlink_query}")
    load_graph_data(
        neo4j_session, matchlink_query, dict_list, batch_size=batch_size, **kwargs
    )


def _resolve_prop_value(prop: PropertyRef, item: Dict[str, Any], kwargs: Dict[str, Any]) -> Any:
    return kwargs.get(prop.name) if prop.set_in_kwargs else item.get(prop.name)


def _labels_from_schema(node_schema: CartographyNodeSchema) -> List[str]:
    labels = [node_schema.label]
    extra: Optional[ExtraNodeLabels] = node_schema.extra_node_labels
    if extra:
        labels.extend(extra.labels)
    return labels


def _export_node_batch(
    node_schema: CartographyNodeSchema,
    dict_list: List[Dict[str, Any]],
    **kwargs,
) -> None:
    """Serialize nodes and their direct relationships (sub-resource + other_relationships)."""
    sink = file_export_sink.get_sink()
    if not sink:
        return

    # Prepare relationship helpers
    sub_rel = node_schema.sub_resource_relationship
    other_rels = node_schema.other_relationships.rels if node_schema.other_relationships else []

    for item in dict_list:
        # Node basics
        # Resolve node id and lastupdated
        node_props: Dict[str, PropertyRef] = {}
        try:
            # asdict() on dataclass instance -> mapping of prop_name -> PropertyRef
            node_props = asdict(node_schema.properties)
        except Exception:
            node_props = {}

        node_id_ref: PropertyRef = node_schema.properties.id  # type: ignore[attr-defined]
        node_uid = _resolve_prop_value(node_id_ref, item, kwargs)
        update_tag = _resolve_prop_value(node_schema.properties.lastupdated, item, kwargs)  # type: ignore[attr-defined]

        # Build exported props excluding id/lastupdated
        props: Dict[str, Any] = {}
        for pname, pref in node_props.items():
            if pname in ("id", "lastupdated"):
                continue
            props[pname] = _resolve_prop_value(pref, item, kwargs)

        # Sub-resource scoping info
        sub_label: Optional[str] = None
        sub_id: Optional[Any] = None
        if sub_rel is not None:
            sub_label = sub_rel.target_node_label
            matcher_dict: Dict[str, PropertyRef] = asdict(sub_rel.target_node_matcher)  # type: ignore
            # Expect single-key matcher; use 'id' when present
            if len(matcher_dict) == 1 and "id" in matcher_dict:
                sub_id = _resolve_prop_value(matcher_dict["id"], item, kwargs)

        # Write vertex
        sink.write_vertex(
            uid=node_uid,
            labels=_labels_from_schema(node_schema),
            props=props,
            update_tag=update_tag,
            sub_resource_label=sub_label,
            sub_resource_id=sub_id,
        )

        # Export edges for sub-resource
        if sub_rel is not None and sub_label is not None and sub_id is not None and node_uid is not None:
            if sub_rel.direction == LinkDirection.INWARD:
                sink.write_edge(
                    from_uid=sub_id,
                    to_uid=node_uid,
                    rel_type=sub_rel.rel_label,
                    update_tag=update_tag,
                    sub_resource_label=sub_label,
                    sub_resource_id=sub_id,
                )
            else:
                sink.write_edge(
                    from_uid=node_uid,
                    to_uid=sub_id,
                    rel_type=sub_rel.rel_label,
                    update_tag=update_tag,
                    sub_resource_label=sub_label,
                    sub_resource_id=sub_id,
                )

        # Export edges for other relationships
        for rel in other_rels:
            matcher_dict: Dict[str, PropertyRef] = asdict(rel.target_node_matcher)  # type: ignore
            # Single-key match is the common case
            if len(matcher_dict) == 1:
                key, pref = next(iter(matcher_dict.items()))
                val = _resolve_prop_value(pref, item, kwargs)
                if val is None:
                    continue
                # Handle one_to_many
                values: Iterable[Any]
                if pref.one_to_many and isinstance(val, list):
                    values = val
                else:
                    values = [val]

                for v in values:
                    # Prefer direct uid linkage when key == 'id'; otherwise export a matcher fallback
                    from_uid = node_uid
                    to_uid = v if key == "id" else None
                    from_match = None
                    to_match = None
                    if key != "id":
                        to_match = {key: v}

                    if rel.direction == LinkDirection.INWARD:
                        sink.write_edge(
                            from_uid=to_uid,
                            to_uid=from_uid,
                            rel_type=rel.rel_label,
                            update_tag=update_tag,
                            to_match=to_match if to_uid is None else None,
                        )
                    else:
                        sink.write_edge(
                            from_uid=from_uid,
                            to_uid=to_uid,
                            rel_type=rel.rel_label,
                            update_tag=update_tag,
                            to_match=to_match if to_uid is None else None,
                        )
            else:
                # Composite matcher; export as best-effort matcher description
                match_payload: Dict[str, Any] = {
                    k: _resolve_prop_value(p, item, kwargs) for k, p in matcher_dict.items()
                }
                if rel.direction == LinkDirection.INWARD:
                    sink.write_edge(
                        to_uid=node_uid,
                        rel_type=rel.rel_label,
                        update_tag=update_tag,
                        from_match=match_payload,
                    )
                else:
                    sink.write_edge(
                        from_uid=node_uid,
                        rel_type=rel.rel_label,
                        update_tag=update_tag,
                        to_match=match_payload,
                    )


def _export_matchlinks_batch(
    rel_schema: CartographyRelSchema,
    dict_list: List[Dict[str, Any]],
    **kwargs,
) -> None:
    sink = file_export_sink.get_sink()
    if not sink:
        return

    source_matcher: Dict[str, PropertyRef] = asdict(rel_schema.source_node_matcher) if rel_schema.source_node_matcher else {}
    target_matcher: Dict[str, PropertyRef] = asdict(rel_schema.target_node_matcher)

    sub_label = kwargs.get("_sub_resource_label")
    sub_id = kwargs.get("_sub_resource_id")

    for item in dict_list:
        # Compute update tag if present
        update_tag = kwargs.get("lastupdated")

        # Resolve matchers
        def _resolve_matcher(m: Dict[str, PropertyRef]) -> Dict[str, Any]:
            return {k: _resolve_prop_value(p, item, kwargs) for k, p in m.items()}

        src_vals = _resolve_matcher(source_matcher) if source_matcher else {}
        tgt_vals = _resolve_matcher(target_matcher)

        # Prefer uid linkage when matching on single 'id'
        from_uid = src_vals.get("id") if len(source_matcher) == 1 and "id" in source_matcher else None
        to_uid = tgt_vals.get("id") if len(target_matcher) == 1 and "id" in target_matcher else None

        if rel_schema.direction == LinkDirection.INWARD:
            sink.write_edge(
                from_uid=to_uid,
                to_uid=from_uid,
                rel_type=rel_schema.rel_label,
                update_tag=update_tag,
                from_match=None if to_uid is not None else tgt_vals,
                to_match=None if from_uid is not None else src_vals,
                sub_resource_label=sub_label,
                sub_resource_id=sub_id,
            )
        else:
            sink.write_edge(
                from_uid=from_uid,
                to_uid=to_uid,
                rel_type=rel_schema.rel_label,
                update_tag=update_tag,
                from_match=None if from_uid is not None else src_vals,
                to_match=None if to_uid is not None else tgt_vals,
                sub_resource_label=sub_label,
                sub_resource_id=sub_id,
            )
