from dataclasses import asdict
from string import Template
from typing import Dict
from typing import List

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
    Note that auto-cleanups for a node with no relationships is not currently supported.
    Algorithm:
    1. First delete all stale nodes attached to the node_schema's sub resource
    2. Delete all stale node to sub resource relationships
        - We don't expect this to be very common (never for AWS resources, at least), but in case it is possible for an
          asset to change sub resources, we want to handle it properly.
    3. For all relationships defined on the node schema, delete all stale ones.
    :param node_schema: The given CartographyNodeSchema
    :return: A list of Neo4j queries to clean up nodes and relationships.
    """
    if not node_schema.sub_resource_relationship:
        raise ValueError(
            "Auto-creating a cleanup job for a node_schema without a sub resource relationship is not supported. "
            f'Please check the class definition of "{node_schema.__class__.__name__}".',
        )

    result = _build_cleanup_node_and_rel_queries(node_schema, node_schema.sub_resource_relationship)
    if node_schema.other_relationships:
        for rel in node_schema.other_relationships.rels:
            # [0] is the delete node query, [1] is the delete relationship query. We only want the latter.
            _, rel_query = _build_cleanup_node_and_rel_queries(node_schema, rel)
            result.append(rel_query)

    return result


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

    # Draw sub resource rel with correct direction
    if node_schema.sub_resource_relationship.direction == LinkDirection.INWARD:
        sub_resource_link_template = Template("<-[s:$SubResourceRelLabel]-")
    else:
        sub_resource_link_template = Template("-[s:$SubResourceRelLabel]->")
    sub_resource_link = sub_resource_link_template.safe_substitute(
        SubResourceRelLabel=node_schema.sub_resource_relationship.rel_label,
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
        _validate_target_node_matcher_for_cleanup_job(node_schema.sub_resource_relationship.target_node_matcher)
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
        MATCH (n:$node_label)$sub_resource_link(:$sub_resource_label{$match_sub_res_clause})
        $selected_rel_clause
        $delete_action_clause
        """,
    )
    return [
        query_template.safe_substitute(
            node_label=node_schema.label,
            sub_resource_link=sub_resource_link,
            sub_resource_label=node_schema.sub_resource_relationship.target_node_label,
            match_sub_res_clause=_build_match_clause(node_schema.sub_resource_relationship.target_node_matcher),
            selected_rel_clause=(
                "" if selected_relationship == node_schema.sub_resource_relationship
                else _build_selected_rel_clause(selected_relationship)
            ),
            delete_action_clause=delete_action_clause,
        ) for delete_action_clause in delete_action_clauses
    ]


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
    selected_rel = selected_rel_template.safe_substitute(SelectedRelLabel=selected_relationship.rel_label)
    selected_rel_clause_template = Template("""MATCH (n)$selected_rel(:$other_node_label)""")
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
