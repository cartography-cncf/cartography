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


def build_cleanup_queries(node_schema: CartographyNodeSchema) -> List[str]:
    """
    Generates queries to clean up stale nodes and relationships from the given CartographyNodeSchema.
    Properly handles cases where a node schema has a scoped cleanup or not.
    Note that auto-cleanups for a node with no relationships is not currently supported.
    :param node_schema: The given CartographyNodeSchema
    :return: A list of Neo4j queries to clean up nodes and relationships.
    """
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
                _, rel_query = _build_cleanup_node_and_rel_queries(node_schema, rel)
                queries.append(rel_query)
            else:
                queries.append(_build_cleanup_rel_queries_unscoped(node_schema, rel))

    return queries


def _build_cleanup_rel_query_no_sub_resource(
    node_schema: CartographyNodeSchema,
    selected_relationship: CartographyRelSchema,
) -> str:
    """
    Helper function to delete stale relationships for node_schemas that have no sub resource relationship defined.
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
    Helper function to build a MATCH statement for a given node schema for cleanup.
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
) -> List[str]:
    """
    Private function that performs the main string template logic for generating cleanup node and relationship queries.
    :param node_schema: The given CartographyNodeSchema to generate cleanup queries for.
    :param selected_relationship: Determines what relationship on the node_schema to build cleanup queries for.
    selected_relationship must be in the set {node_schema.sub_resource_relationship} + node_schema.other_relationships.
    :return: A list of 2 cleanup queries. The first one cleans up stale nodes attached to the given
    selected_relationships, and the second one cleans up stale selected_relationships. For example outputs, see
    tests.unit.cartography.graph.test_cleanupbuilder.
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
    Generates a cleanup query for a node_schema to allow unscoped cleanup.
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
    Generates relationship cleanup query for a node_schema with scoped_cleanup=False.
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
    Draw selected relationship with correct direction. Returns a string that looks like either
    MATCH (n)<-[r:$SelectedRelLabel]-(:$other_node_label) or
    MATCH (n)-[r:$SelectedRelLabel]->(:$other_node_label)
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
    Raises ValueError if a single PropertyRef in the given TargetNodeMatcher does not have set_in_kwargs=True.
    Auto cleanups require the sub resource target node matcher to have set_in_kwargs=True because the GraphJob
    class injects the sub resource id via a query kwarg parameter. See GraphJob and GraphStatement classes.
    This is a private function meant only to be called when we clean up the sub resource relationship.
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
    Generates a cleanup query for a matchlink relationship.
    :param rel_schema: The CartographyRelSchema object to generate a query. This CartographyRelSchema object
    - Must have a source_node_matcher and source_node_label defined
    - Must have a CartographyRelProperties object where _sub_resource_label and _sub_resource_id are defined
    :return: A Neo4j query used to clean up stale matchlink relationships.
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
