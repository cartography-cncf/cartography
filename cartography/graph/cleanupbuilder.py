from dataclasses import asdict
from string import Template
from typing import Dict
from typing import List

from cartography.graph.querybuilder import _asdict_with_validate_relprops
from cartography.graph.querybuilder import _build_match_clause
from cartography.graph.querybuilder import rel_present_on_node_schema
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import TargetNodeMatcher


def build_cleanup_queries(
    node_schema: CartographyNodeSchema, cascade_delete: bool = False
) -> List[str]:
    """
    Generate Neo4j queries to clean up stale nodes and relationships.

    This function creates appropriate cleanup queries based on the node schema's
    configuration, handling different scenarios for scoped and unscoped cleanup
    operations.

    Args:
        node_schema (CartographyNodeSchema): The node schema object defining the
            structure and cleanup behavior for the target nodes.
        cascade_delete (bool): If True, also delete all child nodes that have a
            relationship to stale nodes matching node_schema.sub_resource_relationship.rel_label.
            Defaults to False to preserve existing behavior. Only valid when scoped_cleanup=True.

    Returns:
        List[str]: A list of Neo4j queries to clean up stale nodes and relationships.
            Returns an empty list if the node has no relationships (e.g., SyncMetadata nodes).

    Raises:
        ValueError: If the node schema has a sub resource relationship but
            ``scoped_cleanup`` is False, which creates an inconsistent configuration.

    Note:
        The function handles four distinct cases:

        1. **Standard scoped cleanup**: Node has sub resource + scoped cleanup = True
           → Clean up stale nodes scoped to the sub resource
        2. **Invalid configuration**: Node has sub resource + scoped cleanup = False
           → Raises ValueError (inconsistent state)
        3. **Relationship-only cleanup**: No sub resource + scoped cleanup = True
           → Clean up only stale relationships, preserve nodes
        4. **Unscoped cleanup**: No sub resource + scoped cleanup = False
           → Clean up all stale nodes regardless of scope

        Nodes without relationships (like SyncMetadata) are left for manual management.
    """
    # Validate: cascade_delete only makes sense with scoped cleanup
    if cascade_delete and not node_schema.scoped_cleanup:
        raise ValueError(
            f"Invalid configuration for {node_schema.label}: cascade_delete=True requires scoped_cleanup=True. "
            "Cascade delete is designed for scoped cleanups where parent nodes own children via the "
            "sub_resource_relationship rel_label. "
            "Unscoped cleanups delete all stale nodes globally and typically don't have a parent-child ownership model.",
        )

    # If the node has no relationships, do not delete the node. Leave this behind for the user to manage.
    # Oftentimes these are SyncMetadata nodes.
    if (
        not node_schema.sub_resource_relationship
        and not node_schema.other_relationships
    ):
        return []

    # Case 1 [Standard]: the node has a sub resource and scoped cleanup is true => clean up stale nodes
    # of this type, scoped to the sub resource. Continue on to clean up the other_relationships too.
    if node_schema.sub_resource_relationship and node_schema.scoped_cleanup:
        queries = _build_cleanup_node_and_rel_queries(
            node_schema,
            node_schema.sub_resource_relationship,
            cascade_delete,
        )

    # Case 2: The node has a sub resource but scoped cleanup is false => this does not make sense
    # because if have a sub resource, we are implying that we are doing scoped cleanup.
    elif node_schema.sub_resource_relationship and not node_schema.scoped_cleanup:
        raise ValueError(
            f"This is not expected: {node_schema.label} has a sub_resource_relationship but scoped_cleanup=False."
            "Please check the class definition for this node schema. It doesn't make sense for a node to have a "
            "sub resource relationship and an unscoped cleanup. Doing this will cause all stale nodes of this type "
            "to be deleted regardless of the sub resource they are attached to."
        )

    # Case 3: The node has no sub resource but scoped cleanup is true => do not delete any nodes, but clean up stale relationships.
    # Return early.
    elif not node_schema.sub_resource_relationship and node_schema.scoped_cleanup:
        queries = []
        other_rels = (
            node_schema.other_relationships.rels
            if node_schema.other_relationships
            else []
        )
        for rel in other_rels:
            query = _build_cleanup_rel_query_no_sub_resource(node_schema, rel)
            queries.append(query)
        return queries

    # Case 4: The node has no sub resource and scoped cleanup is false => clean up the stale nodes. Continue on to clean up the other_relationships too.
    else:
        queries = [_build_cleanup_node_query_unscoped(node_schema)]

    if node_schema.other_relationships:
        for rel in node_schema.other_relationships.rels:
            if node_schema.scoped_cleanup:
                # [0] is the delete node query, [1] is the delete relationship query. We only want the latter.
                _, rel_query = _build_cleanup_node_and_rel_queries(
                    node_schema, rel, cascade_delete
                )
                queries.append(rel_query)
            else:
                queries.append(_build_cleanup_rel_queries_unscoped(node_schema, rel))

    return queries


def _build_cleanup_rel_query_no_sub_resource(
    node_schema: CartographyNodeSchema,
    selected_relationship: CartographyRelSchema,
) -> str:
    """
    Generate a cleanup query for relationships when no sub resource is defined.

    This helper function creates a query to delete stale relationships for node schemas
    that don't have a sub resource relationship defined. It's used in scoped cleanup
    scenarios where only relationships need to be cleaned up.

    Args:
        node_schema (CartographyNodeSchema): The node schema to delete relationships for.
            Must not have a sub resource relationship defined.
        selected_relationship (CartographyRelSchema): The specific relationship to delete.

    Returns:
        str: A Neo4j query to delete stale relationships for the given node schema.

    Raises:
        ValueError: If the node schema has a sub resource relationship defined.
            This function is specifically for schemas without sub resource relationships.

    Examples:
        >>> rel_schema = CartographyRelSchema(
        ...     target_node_label='AWSRole',
        ...     direction=LinkDirection.OUTWARD,
        ...     rel_label='HAS_ROLE'
        ... )
        >>> query = _build_cleanup_rel_query_no_sub_resource(node_schema, rel_schema)
        >>> print(query)
        MATCH (n:AWSUser)
        MATCH (n)-[r:HAS_ROLE]->(...)
        WHERE r.lastupdated <> $UPDATE_TAG
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
    """
    if node_schema.sub_resource_relationship:
        raise ValueError(
            f"Expected {node_schema.label} to not exist. "
            "This function is intended for node_schemas without sub_resource_relationships.",
        )
    # Ensure the node is attached to the sub resource and delete the node
    query_template = Template(
        """
        MATCH (n:$node_label)
        $selected_rel_clause
        WHERE r.lastupdated <> $UPDATE_TAG
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
        """,
    )
    return query_template.safe_substitute(
        node_label=node_schema.label,
        selected_rel_clause=_build_selected_rel_clause(selected_relationship),
    )


def _build_match_statement_for_cleanup(node_schema: CartographyNodeSchema) -> str:
    """
    Build a MATCH statement for cleanup queries.

    This helper function generates the appropriate MATCH clause based on whether
    the node schema has a sub resource relationship and scoped cleanup configuration.

    Args:
        node_schema (CartographyNodeSchema): The node schema object to build the
            MATCH statement for.

    Returns:
        str: A Neo4j MATCH statement string appropriate for the cleanup context.

    Examples:
        For simple unscoped cleanup:
        >>> # Returns: "MATCH (n:AWSUser)"

        For scoped cleanup with sub resource:
        >>> # Returns: "MATCH (n:AWSUser)<-[s:RESOURCE]-(sub:AWSAccount{id: $account_id})"

    Note:
        - If no sub resource relationship exists and scoped cleanup is False,
          returns a simple node match.
        - If a sub resource relationship exists, includes the relationship pattern
          with correct direction and matching clauses for scoped cleanup.
    """
    if not node_schema.sub_resource_relationship and not node_schema.scoped_cleanup:
        template = Template("MATCH (n:$node_label)")
        return template.safe_substitute(
            node_label=node_schema.label,
        )

    # if it has a sub resource relationship defined, we need to match on the sub resource to make sure we only delete
    # nodes that are attached to the sub resource.
    template = Template(
        "MATCH (n:$node_label)$sub_resource_link(:$sub_resource_label{$match_sub_res_clause})"
    )
    sub_resource_link = ""
    sub_resource_label = ""
    match_sub_res_clause = ""

    if node_schema.sub_resource_relationship:
        # Draw sub resource rel with correct direction
        if node_schema.sub_resource_relationship.direction == LinkDirection.INWARD:
            sub_resource_link_template = Template("<-[s:$SubResourceRelLabel]-")
        else:
            sub_resource_link_template = Template("-[s:$SubResourceRelLabel]->")
        sub_resource_link = sub_resource_link_template.safe_substitute(
            SubResourceRelLabel=node_schema.sub_resource_relationship.rel_label,
        )
        sub_resource_label = node_schema.sub_resource_relationship.target_node_label
        match_sub_res_clause = _build_match_clause(
            node_schema.sub_resource_relationship.target_node_matcher,
        )
    return template.safe_substitute(
        node_label=node_schema.label,
        sub_resource_link=sub_resource_link,
        sub_resource_label=sub_resource_label,
        match_sub_res_clause=match_sub_res_clause,
    )


def _build_cleanup_node_and_rel_queries(
    node_schema: CartographyNodeSchema,
    selected_relationship: CartographyRelSchema,
    cascade_delete: bool = False,
) -> List[str]:
    """
    Generate cleanup queries for both nodes and relationships.

    This function performs the main string template logic for generating cleanup
    queries for both nodes and their relationships. It creates two queries:
    one for cleaning up stale nodes and another for cleaning up stale relationships.

    Args:
        node_schema (CartographyNodeSchema): The node schema to generate cleanup queries for.
        selected_relationship (CartographyRelSchema): The specific relationship to build
            cleanup queries for. Must be either the node's sub resource relationship
            or one of its other relationships.
        cascade_delete (bool): If True, also delete all child nodes that have a
            relationship to stale nodes matching node_schema.sub_resource_relationship.rel_label.
            Defaults to False.

    Returns:
        List[str]: A list of exactly 2 cleanup queries:
            - [0]: Query to clean up stale nodes attached to the selected relationship
            - [1]: Query to clean up stale relationships

    Raises:
        ValueError: If the node schema doesn't have a sub resource relationship defined,
            or if the selected relationship is not present on the node schema.

    Examples:
        >>> queries = _build_cleanup_node_and_rel_queries(node_schema, sub_resource_rel)
        >>> len(queries)
        2
        >>> print(queries[0])  # Node cleanup query
        MATCH (n:AWSUser)<-[s:RESOURCE]-(sub:AWSAccount{id: $account_id})
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;

        >>> print(queries[1])  # Relationship cleanup query
        MATCH (n:AWSUser)<-[s:RESOURCE]-(sub:AWSAccount{id: $account_id})
        WHERE s.lastupdated <> $UPDATE_TAG
        WITH s LIMIT $LIMIT_SIZE
        DELETE s;

    Note:
        - For sub resource relationships, validates that the target node matcher has
          ``set_in_kwargs=True`` for proper GraphJob integration.
        - For detailed examples, see ``tests.unit.cartography.graph.test_cleanupbuilder``.
    """
    if not node_schema.sub_resource_relationship:
        raise ValueError(
            f"_build_cleanup_node_query() failed: '{node_schema.label}' does not have a sub_resource_relationship "
            "defined, so we cannot generate a query to clean it up. Please verify that the class definition is what "
            "you expect.",
        )
    if not rel_present_on_node_schema(node_schema, selected_relationship):
        raise ValueError(
            f"_build_cleanup_node_query(): Attempted to build cleanup query for node '{node_schema.label}' and "
            f"relationship {selected_relationship.rel_label} but that relationship is not present on the node. Please "
            "verify the node class definition for the relationships that it has.",
        )

    # The cleanup node query must always be before the cleanup rel query
    if cascade_delete:
        # When cascade_delete is enabled, also delete stale children that have relationships from stale nodes
        # matching the sub_resource_relationship rel_label. We check child.lastupdated to avoid deleting children
        # that were re-parented to a new tenant in the current sync.
        cascade_rel_label = node_schema.sub_resource_relationship.rel_label
        # The direction for finding children is OPPOSITE of sub_resource_relationship direction:
        # - INWARD sub_resource means parent points to node, so node points to children (OUTWARD)
        # - OUTWARD sub_resource means node points to parent, so children point to node (INWARD)
        if node_schema.sub_resource_relationship.direction == LinkDirection.INWARD:
            cascade_rel_clause = f"-[:{cascade_rel_label}]->"
        else:
            cascade_rel_clause = f"<-[:{cascade_rel_label}]-"
        # Use a unit subquery to delete many children without collecting them and without
        # risking the parent row being filtered out by OPTIONAL MATCH + WHERE.
        delete_action_clauses = [
            f"""
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        CALL {{
            WITH n
            OPTIONAL MATCH (n){cascade_rel_clause}(child)
            WITH child WHERE child IS NOT NULL AND child.lastupdated <> $UPDATE_TAG
            DETACH DELETE child
        }}
        DETACH DELETE n;
        """,
        ]
    else:
        delete_action_clauses = [
            """
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;
        """,
        ]
    # Now clean up the relationships
    if selected_relationship == node_schema.sub_resource_relationship:
        _validate_target_node_matcher_for_cleanup_job(
            node_schema.sub_resource_relationship.target_node_matcher,
        )
        delete_action_clauses.append(
            """
            WHERE s.lastupdated <> $UPDATE_TAG
            WITH s LIMIT $LIMIT_SIZE
            DELETE s;
            """,
        )
    else:
        delete_action_clauses.append(
            """
            WHERE r.lastupdated <> $UPDATE_TAG
            WITH r LIMIT $LIMIT_SIZE
            DELETE r;
            """,
        )

    # Ensure the node is attached to the sub resource and delete the node
    query_template = Template(
        """
        $match_statement
        $selected_rel_clause
        $delete_action_clause
        """,
    )
    return [
        query_template.safe_substitute(
            match_statement=_build_match_statement_for_cleanup(node_schema),
            selected_rel_clause=(
                ""
                if selected_relationship == node_schema.sub_resource_relationship
                else _build_selected_rel_clause(selected_relationship)
            ),
            delete_action_clause=delete_action_clause,
        )
        for delete_action_clause in delete_action_clauses
    ]


def _build_cleanup_node_query_unscoped(
    node_schema: CartographyNodeSchema,
) -> str:
    """
    Generate an unscoped cleanup query for nodes.

    This function creates a cleanup query for node schemas that allow unscoped cleanup,
    meaning all stale nodes of the given type will be deleted regardless of their
    sub resource associations.

    Args:
        node_schema (CartographyNodeSchema): The node schema object to generate a query for.
            Must have ``scoped_cleanup=False``.

    Returns:
        str: A Neo4j query to clean up all stale nodes for the given node schema.

    Raises:
        ValueError: If the node schema has ``scoped_cleanup=True``. This function is
            specifically for unscoped cleanup scenarios.

    Examples:
        >>> node_schema = CartographyNodeSchema(
        ...     label='GlobalConfig',
        ...     scoped_cleanup=False
        ... )
        >>> query = _build_cleanup_node_query_unscoped(node_schema)
        >>> print(query)
        MATCH (n:GlobalConfig)
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;

    Warning:
        This function creates queries that will delete ALL stale nodes of the given type,
        not just those associated with a specific sub resource. Use with caution.

    Note:
        cascade_delete is not supported for unscoped cleanup because unscoped cleanups
        delete all stale nodes globally and don't have a parent-child ownership model.
    """
    if node_schema.scoped_cleanup:
        raise ValueError(
            f"_build_cleanup_node_query_for_unscoped_cleanup() failed: '{node_schema.label}' does not have "
            "scoped_cleanup=False, so we cannot generate a query to clean it up. Please verify that the class "
            "definition is what you expect.",
        )

    # The cleanup node query must always be before the cleanup rel query
    delete_action_clause = """
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;
    """

    # Ensure the node is attached to the sub resource and delete the node
    query_template = Template(
        """
        $match_statement
        $delete_action_clause
        """,
    )
    return query_template.safe_substitute(
        match_statement=_build_match_statement_for_cleanup(node_schema),
        delete_action_clause=delete_action_clause,
    )


def _build_cleanup_rel_queries_unscoped(
    node_schema: CartographyNodeSchema,
    selected_relationship: CartographyRelSchema,
) -> str:
    """
    Generate an unscoped relationship cleanup query.

    This function creates a cleanup query for relationships when the node schema
    has ``scoped_cleanup=False``, meaning all stale relationships of the given type
    will be deleted regardless of sub resource associations.

    Args:
        node_schema (CartographyNodeSchema): The node schema object to generate a query for.
            Must have ``scoped_cleanup=False``.
        selected_relationship (CartographyRelSchema): The specific relationship to delete.
            Must be present on the node schema.

    Returns:
        str: A Neo4j query to clean up stale relationships for the given node schema.

    Raises:
        ValueError: If the node schema has ``scoped_cleanup=True``, or if the selected
            relationship is not present on the node schema.

    Warning:
        This function creates queries that will delete ALL stale relationships of the
        given type, not just those associated with a specific sub resource.
    """
    if node_schema.scoped_cleanup:
        raise ValueError(
            f"_build_cleanup_node_and_rel_queries_unscoped() failed: '{node_schema.label}' does not have "
            "scoped_cleanup=False, so we cannot generate a query to clean it up. Please verify that the class "
            "definition is what you expect.",
        )
    if not rel_present_on_node_schema(node_schema, selected_relationship):
        raise ValueError(
            f"_build_cleanup_node_query(): Attempted to build cleanup query for node '{node_schema.label}' and "
            f"relationship {selected_relationship.rel_label} but that relationship is not present on the node. Please "
            "verify the node class definition for the relationships that it has.",
        )

    # The cleanup node query must always be before the cleanup rel query
    delete_action_clause = """WHERE r.lastupdated <> $UPDATE_TAG
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
        """

    # Ensure the node is attached to the sub resource and delete the node
    query_template = Template(
        """
        $match_statement
        $selected_rel_clause
        $delete_action_clause
        """,
    )
    return query_template.safe_substitute(
        match_statement=_build_match_statement_for_cleanup(node_schema),
        selected_rel_clause=_build_selected_rel_clause(selected_relationship),
        delete_action_clause=delete_action_clause,
    )


def _build_selected_rel_clause(selected_relationship: CartographyRelSchema) -> str:
    """
    Build a relationship clause with correct directional syntax.

    This function generates the appropriate Neo4j relationship pattern syntax
    based on the relationship's direction configuration.

    Args:
        selected_relationship (CartographyRelSchema): The relationship to build the clause for.

    Returns:
        str: A Neo4j relationship clause string with correct directional arrows.
            Examples:
            - ``MATCH (n)<-[r:SELECTED_REL]-(:TargetNode)`` for INWARD direction
            - ``MATCH (n)-[r:SELECTED_REL]->(:TargetNode)`` for OUTWARD direction

    Examples:
        >>> rel_schema = CartographyRelSchema(
        ...     target_node_label='AWSRole',
        ...     direction=LinkDirection.INWARD,
        ...     rel_label='ASSUMES_ROLE'
        ... )
        >>> clause = _build_selected_rel_clause(rel_schema)
        >>> print(clause)
        MATCH (n)<-[r:ASSUMES_ROLE]-(:AWSRole)

        >>> rel_schema_outward = CartographyRelSchema(
        ...     target_node_label='AWSResource',
        ...     direction=LinkDirection.OUTWARD,
        ...     rel_label='OWNS'
        ... )
        >>> clause = _build_selected_rel_clause(rel_schema_outward)
        >>> print(clause)
        MATCH (n)-[r:OWNS]->(:AWSResource)
    """
    if selected_relationship.direction == LinkDirection.INWARD:
        selected_rel_template = Template("<-[r:$SelectedRelLabel]-")
    else:
        selected_rel_template = Template("-[r:$SelectedRelLabel]->")
    selected_rel = selected_rel_template.safe_substitute(
        SelectedRelLabel=selected_relationship.rel_label,
    )
    selected_rel_clause_template = Template(
        """MATCH (n)$selected_rel(:$other_node_label)""",
    )
    selected_rel_clause = selected_rel_clause_template.safe_substitute(
        selected_rel=selected_rel,
        other_node_label=selected_relationship.target_node_label,
    )
    return selected_rel_clause


def _validate_target_node_matcher_for_cleanup_job(tgm: TargetNodeMatcher):
    """
    Validate PropertyRef configurations for cleanup operations.

    This function ensures that all PropertyRef objects in the given TargetNodeMatcher
    have ``set_in_kwargs=True``, which is required for auto cleanup operations.
    The GraphJob class injects sub resource IDs via query keyword arguments.

    Args:
        tgm (TargetNodeMatcher): The TargetNodeMatcher to validate.

    Raises:
        ValueError: If any PropertyRef in the TargetNodeMatcher has ``set_in_kwargs=False``.
            This is required for proper integration with the GraphJob cleanup system.

    Note:
        This is a private function meant only to be called when cleaning up
        sub resource relationships. It ensures compatibility with the GraphJob
        and GraphStatement classes that handle cleanup operations.

    See Also:
        - ``GraphJob`` class for cleanup job management
        - ``GraphStatement`` class for query execution
    """
    tgm_asdict: Dict[str, PropertyRef] = asdict(tgm)

    for key, prop_ref in tgm_asdict.items():
        if not prop_ref.set_in_kwargs:
            raise ValueError(
                f"TargetNodeMatcher PropertyRefs in the sub_resource_relationship must have set_in_kwargs=True. "
                f"{key} has set_in_kwargs=False, please check by reviewing the full stack trace to know which object"
                f"this message was raised from. Debug information: PropertyRef name = {prop_ref.name}.",
            )


def build_cleanup_query_for_matchlink(rel_schema: CartographyRelSchema) -> str:
    """
    Generate a cleanup query for matchlink relationships.

    This function creates a Neo4j query to clean up stale matchlink relationships
    that are scoped to specific sub resources. It's used to maintain data consistency
    by removing outdated relationship connections.

    Args:
        rel_schema (CartographyRelSchema): The relationship schema object to generate
            a query for. Must have the following requirements:

            - ``source_node_matcher`` and ``source_node_label`` defined
            - ``CartographyRelProperties`` object with ``_sub_resource_label`` and
              ``_sub_resource_id`` defined

    Returns:
        str: A Neo4j query to clean up stale matchlink relationships, scoped to
            the specified sub resource.

    Raises:
        ValueError: If the ``rel_schema`` does not have a ``source_node_matcher`` defined.

    Note:
        - The query includes scoping clauses to ensure only relationships associated
          with the specified sub resource are cleaned up.
        - Relationship direction is automatically determined from the schema configuration.
        - The query uses parameterized values for security and consistency.
    """
    if not rel_schema.source_node_matcher:
        raise ValueError(
            f"No source node matcher found for {rel_schema.rel_label}; returning empty list."
        )

    query_template = Template(
        """
        MATCH (from:$source_node_label)$rel_direction[r:$rel_label]$rel_direction_end(to:$target_node_label)
        WHERE r.lastupdated <> $UPDATE_TAG
            AND r._sub_resource_label = $sub_resource_label
            AND r._sub_resource_id = $sub_resource_id
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
        """
    )

    # Determine which way to point the arrow. INWARD is toward the source, otherwise we go toward the target.
    if rel_schema.direction == LinkDirection.INWARD:
        rel_direction = "<-"
        rel_direction_end = "-"
    else:
        rel_direction = "-"
        rel_direction_end = "->"

    # Small hack: avoid type-checking errors by converting the rel_schema to a dict.
    rel_props_as_dict = _asdict_with_validate_relprops(rel_schema)

    return query_template.safe_substitute(
        source_node_label=rel_schema.source_node_label,
        target_node_label=rel_schema.target_node_label,
        rel_label=rel_schema.rel_label,
        rel_direction=rel_direction,
        rel_direction_end=rel_direction_end,
        sub_resource_label=rel_props_as_dict["_sub_resource_label"],
        sub_resource_id=rel_props_as_dict["_sub_resource_id"],
    )
