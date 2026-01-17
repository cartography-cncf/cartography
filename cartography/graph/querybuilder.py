import logging
from dataclasses import asdict
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version
from string import Template

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.mapping import (
    get_semantic_label_mapping_from_node_schema,
)
from cartography.models.ontology.mapping.specs import OntologyFieldMapping

logger = logging.getLogger(__name__)


def _build_ontology_field_statement_invert_boolean(
    mapping_field: OntologyFieldMapping,
    property_ref: PropertyRef,
) -> str:
    # toBooleanOrNull will return a boolean or null if it can't be converted
    # coalesce will return the first non-null value, so if toBooleanOrNull returns null,
    # we invert the boolean value of the property_ref existence
    # ex: "false", "0", "no" => false; anything else => true; null/absent => true
    invert_boolean_template = Template(
        "i.$node_property = (NOT(coalesce(toBooleanOrNull($property_ref), false)))"
    )
    return invert_boolean_template.safe_substitute(
        node_property=f"_ont_{mapping_field.ontology_field}",
        property_ref=property_ref,
    )


def _build_ontology_field_statement_to_boolean(
    mapping_field: OntologyFieldMapping,
    property_ref: PropertyRef,
) -> str:
    # toBoleanOrNull will return a boolean or null if it can't be converted
    # coalesce will return the first non-null value, so if toBooleanOrNull returns null,
    # it will return whether the property_ref is not null (i.e., true if property_ref exists)
    # this way, any non-null value is treated as true
    # ex: "true", "1", "yes" => true; anything else => true; null/absent => false
    to_boolean_template = Template(
        "i.$node_property = coalesce(toBooleanOrNull($property_ref), ($property_ref IS NOT NULL))"
    )
    return to_boolean_template.safe_substitute(
        node_property=f"_ont_{mapping_field.ontology_field}",
        property_ref=property_ref,
    )


def _build_ontology_field_statement_equal_boolean(
    mapping_field: OntologyFieldMapping,
    property_ref: PropertyRef,
) -> str | None:
    # we check if the property_ref is in the list of expected boolean values
    equal_boolean_template = Template(
        "i.$node_property = ($property_ref IN $property_values)"
    )
    extra_field_values = mapping_field.extra.get("values")
    if extra_field_values is None:
        # should not occure due to unit test but failing gracefully
        logger.warning(
            "equal_boolean special handling requires 'values' in extra for field %s",
            mapping_field.ontology_field,
        )
        return None
    if not isinstance(extra_field_values, list):
        logger.warning(
            "equal_boolean special handling 'values' in extra for field %s must be a list",
            mapping_field.ontology_field,
        )
        return None
    return equal_boolean_template.substitute(
        node_property=f"_ont_{mapping_field.ontology_field}",
        property_ref=property_ref,
        property_values=extra_field_values,
    )


def _escape_cypher_string(value: str) -> str:
    r"""
    Escape special characters in a string value for use in a Cypher string literal.

    In Cypher, string literals are enclosed in double quotes, and the following characters
    must be escaped with a backslash:
    - Backslash (\) -> \\
    - Double quote (") -> \"

    :param value: The string value to escape
    :return: The escaped string value safe for use in a Cypher string literal
    """
    # Escape backslashes first (must be done before escaping quotes)
    escaped = value.replace("\\", "\\\\")
    # Then escape double quotes
    escaped = escaped.replace('"', '\\"')
    return escaped


def _build_ontology_field_statement_static_value(
    mapping_field: OntologyFieldMapping,
) -> str | None:
    # Sets a static value for the ontology field
    # The value is provided in extra['value']
    static_value_template = Template("i.$node_property = $static_value")
    extra_value = mapping_field.extra.get("value")
    if extra_value is None:
        # should not occur due to unit test but failing gracefully
        logger.warning(
            "static_value special handling requires 'value' in extra for field %s",
            mapping_field.ontology_field,
        )
        return None

    # Format the value appropriately for Cypher
    if isinstance(extra_value, str):
        formatted_value = f'"{_escape_cypher_string(extra_value)}"'
    elif isinstance(extra_value, bool):
        formatted_value = str(extra_value).lower()
    else:
        formatted_value = str(extra_value)

    return static_value_template.substitute(
        node_property=f"_ont_{mapping_field.ontology_field}",
        static_value=formatted_value,
    )


def _build_ontology_field_statement_or_boolean(
    mapping_field: OntologyFieldMapping,
    node_property_map: dict[str, PropertyRef],
) -> str | None:
    # The or_clause is needed to avoid comparing nulls to boolean values
    # See: https://neo4j.com/docs/cypher-manual/current/values-and-types/working-with-null/#cypher-null-logical-operators
    or_clause = Template("coalesce(toBooleanOrNull($property_ref), false)")
    or_boolean_template = Template("i.$node_property = ($property_condition)")
    extra_fields = mapping_field.extra.get("fields")
    if extra_fields is None:
        # should not occure due to unit test but failing gracefully
        logger.warning(
            "or_boolean special handling requires 'fields' in extra for field %s",
            mapping_field.ontology_field,
        )
        return None
    if not isinstance(extra_fields, list):
        # should not occure due to unit test but failing gracefully
        logger.warning(
            "or_boolean special handling 'fields' in extra for field %s must be a list",
            mapping_field.ontology_field,
        )
        return None

    property_conditions = [
        or_clause.substitute(
            property_ref=node_property_map.get(mapping_field.node_field),
        )
    ]
    for extra_field in mapping_field.extra.get("fields", []):
        extra_property_ref = node_property_map.get(extra_field)
        if not extra_property_ref:
            # should not occure due to unit test but failing gracefully
            logger.warning(
                "Extra field '%s' not found in node properties for or_boolean special handling of field %s",
                extra_field,
                mapping_field.ontology_field,
            )
            continue
        property_conditions.append(
            or_clause.substitute(
                property_ref=extra_property_ref,
            )
        )
    full_property_condition = " OR ".join(property_conditions)
    return or_boolean_template.substitute(
        node_property=f"_ont_{mapping_field.ontology_field}",
        property_condition=full_property_condition,
    )


def _build_ontology_field_statement_nor_boolean(
    mapping_field: OntologyFieldMapping,
    node_property_map: dict[str, PropertyRef],
) -> str | None:
    nor_clause = Template("NOT(coalesce(toBooleanOrNull($property_ref), false))")
    nor_boolean_template = Template("i.$node_property = ($property_condition)")
    extra_fields = mapping_field.extra.get("fields")
    if extra_fields is None:
        # should not occure due to unit test but failing gracefully
        logger.warning(
            "nor_boolean special handling requires 'fields' in extra for field %s",
            mapping_field.ontology_field,
        )
        return None
    if not isinstance(extra_fields, list):
        # should not occure due to unit test but failing gracefully
        logger.warning(
            "nor_boolean special handling 'fields' in extra for field %s must be a list",
            mapping_field.ontology_field,
        )
        return None

    property_conditions = [
        nor_clause.substitute(
            property_ref=node_property_map.get(mapping_field.node_field),
        )
    ]
    for extra_field in mapping_field.extra.get("fields", []):
        extra_property_ref = node_property_map.get(extra_field)
        if not extra_property_ref:
            # should not occure due to unit test but failing gracefully
            logger.warning(
                "Extra field '%s' not found in node properties for nor_boolean special handling of field %s",
                extra_field,
                mapping_field.ontology_field,
            )
            continue
        property_conditions.append(
            nor_clause.substitute(
                property_ref=extra_property_ref,
            )
        )
    full_property_condition = " AND ".join(property_conditions)
    return nor_boolean_template.substitute(
        node_property=f"_ont_{mapping_field.ontology_field}",
        property_condition=full_property_condition,
    )


def _build_ontology_node_properties_statement(
    node_schema: CartographyNodeSchema,
    node_property_map: dict[str, PropertyRef],
) -> str:
    # DOC
    # Try to get the mapping for the given node schema
    ontology_mapping = get_semantic_label_mapping_from_node_schema(node_schema)
    if not ontology_mapping:
        return ""

    source = _get_module_from_schema(node_schema).rsplit(":", maxsplit=1)[-1]
    set_clauses = [f"i._ont_source = '{source}'"]
    for mapping_field in ontology_mapping.fields:
        ontology_field_name = f"_ont_{mapping_field.ontology_field}"
        node_propertyref = node_property_map.get(mapping_field.node_field)

        # Handle static_value special handling first - it doesn't require a node_field
        if mapping_field.special_handling == "static_value":
            static_value_statement = _build_ontology_field_statement_static_value(
                mapping_field
            )
            if static_value_statement:
                set_clauses.append(static_value_statement)
            continue

        # Skip validation for special_handling that don't require node_field
        if not node_propertyref:
            # This should not occure due to unit test but failing gracefully
            logger.warning(
                "Field '%s' not found in node properties for node schema %s",
                mapping_field.node_field,
                node_schema.__class__.__name__,
            )
            continue
        if mapping_field.special_handling == "invert_boolean":
            set_clauses.append(
                _build_ontology_field_statement_invert_boolean(
                    mapping_field,
                    node_propertyref,
                )
            )
        elif mapping_field.special_handling == "to_boolean":
            set_clauses.append(
                _build_ontology_field_statement_to_boolean(
                    mapping_field,
                    node_propertyref,
                )
            )
        elif mapping_field.special_handling == "equal_boolean":
            equal_boolean_statement = _build_ontology_field_statement_equal_boolean(
                mapping_field,
                node_propertyref,
            )
            if equal_boolean_statement:
                set_clauses.append(equal_boolean_statement)
        elif mapping_field.special_handling == "or_boolean":
            or_boolean_statement = _build_ontology_field_statement_or_boolean(
                mapping_field, node_property_map
            )
            if or_boolean_statement:
                set_clauses.append(or_boolean_statement)
        elif mapping_field.special_handling == "nor_boolean":
            nor_boolean_statement = _build_ontology_field_statement_nor_boolean(
                mapping_field, node_property_map
            )
            if nor_boolean_statement:
                set_clauses.append(nor_boolean_statement)
        else:
            simple_field_template = Template("i.$node_property = $property_ref")
            set_clauses.append(
                simple_field_template.substitute(
                    node_property=ontology_field_name,
                    property_ref=node_propertyref,
                )
            )
    if len(set_clauses) == 0:
        return ""
    # Add initial newline
    return ",\n" + ",\n".join(set_clauses)


def _build_node_properties_statement(
    node_property_map: dict[str, PropertyRef],
    extra_node_labels: ExtraNodeLabels | None = None,
) -> str:
    """
    Generate a Neo4j clause that sets node properties using the given mapping of attribute names to PropertyRefs.

    As seen in this example,

        node_property_map: dict[str, PropertyRef] = {
            'id': PropertyRef("Id"),
            'node_prop_1': PropertyRef("Prop1"),
            'node_prop_2': PropertyRef("Prop2", set_in_kwargs=True),
        }
        set_clause: str = _build_node_properties_statement(node_property_map)

    the returned set_clause will be
        ```
        i.id = item.Id,
        i.node_prop_1 = item.Prop1,
        i.node_prop_2 = $Prop2
        ```
    where `i` is a reference to the Neo4j node.
    :param node_property_map: Mapping of node attribute names as str to PropertyRef objects
    :param extra_node_labels: Optional ExtraNodeLabels object to set on the node as string
    :return: The resulting Neo4j SET clause to set the given attributes on the node
    """
    ingest_fields_template = Template("i.$node_property = $property_ref")

    set_clause = ",\n".join(
        [
            ingest_fields_template.safe_substitute(
                node_property=node_property,
                property_ref=property_ref,
            )
            for node_property, property_ref in node_property_map.items()
            if node_property
            != "id"  # The `MERGE` clause will have already set `id`; let's not set it again.
        ],
    )

    # Set extra labels on the node if specified
    if extra_node_labels:
        extra_labels = ":".join([label for label in extra_node_labels.labels])
        set_clause += f",\n                i:{extra_labels}"
    return set_clause


def _build_rel_properties_statement(
    rel_var: str,
    rel_property_map: dict[str, PropertyRef] | None = None,
) -> str:
    """
    Generate a Neo4j clause that sets relationship properties using the given mapping of attribute names to
    PropertyRefs.

    In this code example:

        rel_property_map: dict[str, PropertyRef] = {
            'rel_prop_1': PropertyRef("Prop1"),
            'rel_prop_2': PropertyRef("Prop2", static=True),
        }
        set_clause: str = _build_rel_properties_statement('r', rel_property_map)

    the returned set_clause will be:

        r.rel_prop_1 = item.Prop1,
        r.rel_prop_2 = $Prop2

    :param rel_var: The variable name to use for the relationship in the Neo4j query
    :param rel_property_map: Mapping of relationship attribute names as str to PropertyRef objects
    :return: The resulting Neo4j SET clause to set the given attributes on the relationship
    """
    set_clause = ""
    ingest_fields_template = Template("$rel_var.$rel_property = $property_ref")

    if rel_property_map:
        set_clause += ",\n".join(
            [
                ingest_fields_template.safe_substitute(
                    rel_var=rel_var,
                    rel_property=rel_property,
                    property_ref=property_ref,
                )
                for rel_property, property_ref in rel_property_map.items()
            ],
        )
    return set_clause


def _build_match_clause(matcher: TargetNodeMatcher | SourceNodeMatcher) -> str:
    """
    Generate a Neo4j match statement on one or more keys and values for a given node.
    :param matcher: A TargetNodeMatcher or SourceNodeMatcher object
    :return: a Neo4j match clause
    """
    match = Template("$Key: $PropRef")
    matcher_asdict = asdict(matcher)
    return ", ".join(
        match.safe_substitute(Key=key, PropRef=prop_ref)
        for key, prop_ref in matcher_asdict.items()
    )


def _build_where_clause_for_rel_match(
    node_var: str,
    matcher: TargetNodeMatcher,
) -> str:
    """
    Same as _build_match_clause, but puts the matching logic in a WHERE clause.
    This is intended specifically to use for joining with relationships where we need a case-insensitive match.
    :param matcher: A TargetNodeMatcher object
    :return: a Neo4j where clause
    """
    match = Template("$node_var.$key = $prop_ref")
    case_insensitive_match = Template("toLower($node_var.$key) = toLower($prop_ref)")
    fuzzy_and_ignorecase_match = Template(
        "toLower($node_var.$key) CONTAINS toLower($prop_ref)"
    )
    # This assumes that item.$prop_ref points to a list available on the data object
    one_to_many_match = Template("$node_var.$key IN $prop_ref")

    matcher_asdict = asdict(matcher)

    result = []
    for key, prop_ref in matcher_asdict.items():
        if prop_ref.ignore_case:
            prop_line = case_insensitive_match.safe_substitute(
                node_var=node_var,
                key=key,
                prop_ref=prop_ref,
            )
        elif prop_ref.fuzzy_and_ignore_case:
            prop_line = fuzzy_and_ignorecase_match.safe_substitute(
                node_var=node_var, key=key, prop_ref=prop_ref
            )
        elif prop_ref.one_to_many:
            # Allow a single node to be attached to multiple others at once using a list of IDs provided in kwargs
            prop_line = one_to_many_match.safe_substitute(
                node_var=node_var, key=key, prop_ref=prop_ref
            )
        else:
            # Exact match (default; most efficient)
            prop_line = match.safe_substitute(
                node_var=node_var,
                key=key,
                prop_ref=prop_ref,
            )
        result.append(prop_line)
    return " AND\n".join(result)


def _asdict_with_validate_relprops(
    link: CartographyRelSchema,
) -> dict[str, PropertyRef]:
    """
    Give a helpful error message when forgetting to put `()` when instantiating a CartographyRelSchema, as this
    isn't always caught by IDEs.
    """
    try:
        rel_props_as_dict: dict[str, PropertyRef] = asdict(link.properties)
    except TypeError as e:
        if (
            e.args
            and e.args[0]
            and e.args == "asdict() should be called on dataclass instances"
        ):
            logger.error(
                f'TypeError thrown when trying to draw relation "{link.rel_label}" to a "{link.target_node_label}" '
                f"node. Please make sure that you did not forget to write `()` when specifying `properties` in the"
                f"dataclass. "
                f"For example, do `properties: RelProp = RelProp()`; NOT `properties: RelProp = RelProp`.",
            )
        raise
    return rel_props_as_dict


def _build_attach_sub_resource_statement(
    sub_resource_link: CartographyRelSchema | None = None,
) -> str:
    """
    Generates a Neo4j statement to attach a sub resource to a node. A 'sub resource' is a term we made up to describe
    billing units of a given resource. For example,
    - In AWS, the sub resource is an AWSAccount.
    - In Azure, the sub resource is a Subscription.
    - In GCP, the sub resource is a GCPProject.
    - etc.
    This is a private function not meant to be called outside of build_ingest_query().
    :param sub_resource_link: Optional: The CartographyRelSchema object connecting previous node(s) to the sub resource.
    :return: a Neo4j clause that connects previous node(s) to a sub resource, taking into account the labels, attribute
    keys, and directionality. If sub_resource_link is None, return an empty string.
    """
    if not sub_resource_link:
        return ""

    sub_resource_attach_template = Template(
        """
        WITH i, item
        OPTIONAL MATCH (j:$SubResourceLabel{$MatchClause})
        WITH i, item, j WHERE j IS NOT NULL
        $RelMergeClause
        ON CREATE SET r.firstseen = timestamp()
        SET
            r._module_name = "$module_name",
            r._module_version = "$module_version",
            $set_rel_properties_statement
        """,
    )

    if sub_resource_link.direction == LinkDirection.INWARD:
        rel_merge_template = Template("""MERGE (i)<-[r:$SubResourceRelLabel]-(j)""")
    else:
        rel_merge_template = Template("""MERGE (i)-[r:$SubResourceRelLabel]->(j)""")

    rel_merge_clause = rel_merge_template.safe_substitute(
        SubResourceRelLabel=sub_resource_link.rel_label,
    )

    rel_props_as_dict: dict[str, PropertyRef] = _asdict_with_validate_relprops(
        sub_resource_link,
    )

    attach_sub_resource_statement = sub_resource_attach_template.safe_substitute(
        SubResourceLabel=sub_resource_link.target_node_label,
        MatchClause=_build_match_clause(sub_resource_link.target_node_matcher),
        RelMergeClause=rel_merge_clause,
        module_name=_get_module_from_schema(sub_resource_link),
        module_version=_get_cartography_version(),
        SubResourceRelLabel=sub_resource_link.rel_label,
        set_rel_properties_statement=_build_rel_properties_statement(
            "r",
            rel_props_as_dict,
        ),
    )
    return attach_sub_resource_statement


def _build_attach_additional_links_statement(
    additional_relationships: OtherRelationships | None = None,
) -> str:
    """
    Generates a Neo4j statement to attach one or more CartographyRelSchemas to node(s) previously mentioned in the
    query.
    This is a private function not meant to be called outside of build_ingestion_query().
    :param additional_relationships: Optional list of CartographyRelSchema describing what other relationships should
    be created from the previous node(s) in this query.
    :return: A Neo4j clause that connects previous node(s) to the given additional_links., taking into account the
    labels, attribute keys, and directionality. If additional_relationships is None, return an empty string.
    """
    if not additional_relationships:
        return ""

    additional_links_template = Template(
        """
        WITH i, item
        OPTIONAL MATCH ($node_var:$AddlLabel)
        WHERE
            $WhereClause
        WITH i, item, $node_var WHERE $node_var IS NOT NULL
        $RelMerge
        ON CREATE SET $rel_var.firstseen = timestamp()
        SET
            $rel_var._module_name = "$module_name",
            $rel_var._module_version = "$module_version",
            $set_rel_properties_statement
        """,
    )
    links = []
    for num, link in enumerate(additional_relationships.rels):
        node_var = f"n{num}"
        rel_var = f"r{num}"

        if link.direction == LinkDirection.INWARD:
            rel_merge_template = Template(
                """MERGE (i)<-[$rel_var:$AddlRelLabel]-($node_var)""",
            )
        else:
            rel_merge_template = Template(
                """MERGE (i)-[$rel_var:$AddlRelLabel]->($node_var)""",
            )

        rel_merge = rel_merge_template.safe_substitute(
            rel_var=rel_var,
            AddlRelLabel=link.rel_label,
            node_var=node_var,
        )

        rel_props_as_dict = _asdict_with_validate_relprops(link)

        additional_ref = additional_links_template.safe_substitute(
            AddlLabel=link.target_node_label,
            WhereClause=_build_where_clause_for_rel_match(
                node_var,
                link.target_node_matcher,
            ),
            node_var=node_var,
            rel_var=rel_var,
            RelMerge=rel_merge,
            module_name=_get_module_from_schema(link),
            module_version=_get_cartography_version(),
            set_rel_properties_statement=_build_rel_properties_statement(
                rel_var,
                rel_props_as_dict,
            ),
        )
        links.append(additional_ref)

    return "UNION".join(links)


def _build_attach_relationships_statement(
    sub_resource_relationship: CartographyRelSchema | None,
    other_relationships: OtherRelationships | None,
) -> str:
    """
    Use Neo4j subqueries to attach sub resource and/or other relationships.
    Subqueries allow the query to continue to run even if we only have data for some but not all the relationships
    defined by a schema.
    For example, if an EC2Instance has attachments to NetworkInterfaces and AWSAccounts, but our data only includes
    EC2Instance to AWSAccount information, structuring the ingestion query with subqueries allows us to build a query
    that will ignore the null relationships and continue to MERGE the ones that exist.
    """
    if not sub_resource_relationship and not other_relationships:
        return ""

    attach_sub_resource_statement = _build_attach_sub_resource_statement(
        sub_resource_relationship,
    )
    attach_additional_links_statement = _build_attach_additional_links_statement(
        other_relationships,
    )

    statements = []
    statements += (
        [attach_sub_resource_statement] if attach_sub_resource_statement else []
    )
    statements += (
        [attach_additional_links_statement] if attach_additional_links_statement else []
    )

    attach_relationships_statement = "UNION".join(stmt for stmt in statements)

    query_template = Template(
        """
        WITH i, item
        CALL {
            $attach_relationships_statement
        }
        """,
    )
    return query_template.safe_substitute(
        attach_relationships_statement=attach_relationships_statement,
    )


def rel_present_on_node_schema(
    node_schema: CartographyNodeSchema,
    rel_schema: CartographyRelSchema,
) -> bool:
    """
    Answers the question: is the given rel_schema is present on the given node_schema?
    """
    sub_res_rel, other_rels = filter_selected_relationships(node_schema, {rel_schema})
    if sub_res_rel or other_rels:
        return True
    return False


def filter_selected_relationships(
    node_schema: CartographyNodeSchema,
    selected_relationships: set[CartographyRelSchema],
) -> tuple[CartographyRelSchema | None, OtherRelationships | None]:
    """
    Ensures that selected relationships specified to build_ingestion_query() are actually present on
    node_schema.sub_resource_relationship and node_schema.other_relationships.
    :param node_schema: The node schema object to filter relationships against
    :param selected_relationships: The set of relationships to check if they exist in the node schema. If empty set,
    this means that no relationships have been selected. None is not an accepted value here.
    :return: a tuple of the shape (sub resource rel [if present in selected_relationships], an OtherRelationships object
    containing all values of node_schema.other_relationships that are present in selected_relationships)
    """
    # The empty set means no relationships are selected
    if selected_relationships == set():
        return None, None

    # Collect the node's sub resource rel and OtherRelationships together in one set for easy comparison
    all_rels_on_node = {node_schema.sub_resource_relationship}
    if node_schema.other_relationships:
        for rel in node_schema.other_relationships.rels:
            all_rels_on_node.add(rel)

    # Ensure that the selected_relationships are actually present on the node_schema.
    for selected_rel in selected_relationships:
        if selected_rel not in all_rels_on_node:
            raise ValueError(
                f"filter_selected_relationships() failed: CartographyRelSchema {selected_rel.__class__.__name__} is "
                f"not defined on CartographyNodeSchema type {node_schema.__class__.__name__}. Please verify the "
                f"value of `selected_relationships` passed to `build_ingestion_query()`.",
            )

    sub_resource_rel = node_schema.sub_resource_relationship
    if sub_resource_rel not in selected_relationships:
        sub_resource_rel = None

    # By this point, everything in selected_relationships is validated to be present in node_schema
    filtered_other_rels = OtherRelationships(
        [rel for rel in selected_relationships if rel != sub_resource_rel],
    )

    return sub_resource_rel, filtered_other_rels


def build_ingestion_query(
    node_schema: CartographyNodeSchema,
    selected_relationships: set[CartographyRelSchema] | None = None,
) -> str:
    """
    Generates a Neo4j query from the given CartographyNodeSchema to ingest the specified nodes and relationships so that
    cartography module authors don't need to handwrite their own queries.
    :param node_schema: The CartographyNodeSchema object to build a Neo4j query from.
    :param selected_relationships: If specified, generates a query that attaches only the relationships in this optional
    set of CartographyRelSchema. The RelSchema specified here _must_ be present in node_schema.sub_resource_relationship
    or node_schema.other_relationships.
    If selected_relationships is None (default), then we create a query using all RelSchema specified in
    node_schema.sub_resource_relationship + node_schema.other_relationships.
    If selected_relationships is the empty set, we create a query with no relationship attachments at all.
    :return: An optimized Neo4j query that can be used to ingest nodes and relationships.
    Important notes:
    - The resulting query uses the UNWIND + MERGE pattern (see
      https://neo4j.com/docs/cypher-manual/current/clauses/unwind/#unwind-creating-nodes-from-a-list-parameter) to batch
      load the data for speed.
    - The query assumes that a list of dicts will be passed to it through parameter $DictList.
    - The query sets `firstseen` attributes on all the nodes and relationships that it creates.
    - The query is intended to be supplied as input to cartography.core.client.tx.load_graph_data().
    """
    query_template = Template(
        """
        UNWIND $DictList AS item
            MERGE (i:$node_label{id: $dict_id_field})
            ON CREATE SET i.firstseen = timestamp()
            SET
                i._module_name = "$module_name",
                i._module_version = "$module_version",
                $set_node_properties_statement
                $set_ontology_node_properties_statement
            $attach_relationships_statement
        """,
    )

    node_props: CartographyNodeProperties = node_schema.properties
    node_props_as_dict: dict[str, PropertyRef] = asdict(node_props)

    # Handle selected relationships
    sub_resource_rel: CartographyRelSchema | None = (
        node_schema.sub_resource_relationship
    )
    other_rels: OtherRelationships | None = node_schema.other_relationships
    if selected_relationships or selected_relationships == set():
        sub_resource_rel, other_rels = filter_selected_relationships(
            node_schema,
            selected_relationships,
        )

    ingest_query = query_template.safe_substitute(
        node_label=node_schema.label,
        dict_id_field=node_props.id,
        module_name=_get_module_from_schema(node_schema),
        module_version=_get_cartography_version(),
        set_node_properties_statement=_build_node_properties_statement(
            node_props_as_dict,
            node_schema.extra_node_labels,
        ),
        set_ontology_node_properties_statement=_build_ontology_node_properties_statement(
            node_schema,
            node_props_as_dict,
        ),
        attach_relationships_statement=_build_attach_relationships_statement(
            sub_resource_rel,
            other_rels,
        ),
    )
    return ingest_query


def build_create_index_queries(node_schema: CartographyNodeSchema) -> list[str]:
    """
    Generate queries to create indexes for the given CartographyNodeSchema and all node types attached to it via its
    relationships.
    :param node_schema: The Cartography node_schema object
    :return: A list of queries of the form `CREATE INDEX IF NOT EXISTS FOR (n:$TargetNodeLabel) ON (n.$TargetAttribute)`
    """
    index_template = Template(
        "CREATE INDEX IF NOT EXISTS FOR (n:$TargetNodeLabel) ON (n.$TargetAttribute);",
    )

    # First ensure an index exists for the node_schema and all extra labels on the `id` and `lastupdated` fields
    result = [
        index_template.safe_substitute(
            TargetNodeLabel=node_schema.label,
            TargetAttribute="id",
        ),
        index_template.safe_substitute(
            TargetNodeLabel=node_schema.label,
            TargetAttribute="lastupdated",
        ),
    ]
    if node_schema.extra_node_labels:
        result.extend(
            [
                index_template.safe_substitute(
                    TargetNodeLabel=label,
                    TargetAttribute="id",  # Precondition: 'id' is defined on all cartography node_schema objects.
                )
                for label in node_schema.extra_node_labels.labels
            ],
        )

    # Next, for all relationships possible out of this node, ensure that indexes exist for all target nodes' properties
    # as specified in their TargetNodeMatchers.
    rel_schemas = []
    if node_schema.sub_resource_relationship:
        rel_schemas.extend([node_schema.sub_resource_relationship])
    if node_schema.other_relationships:
        rel_schemas.extend(node_schema.other_relationships.rels)
    for rs in rel_schemas:
        for target_key in asdict(rs.target_node_matcher).keys():
            result.append(
                index_template.safe_substitute(
                    TargetNodeLabel=rs.target_node_label,
                    TargetAttribute=target_key,
                ),
            )

    # Now, include extra indexes defined by the module author on the node schema's property refs.
    node_props_as_dict: dict[str, PropertyRef] = asdict(node_schema.properties)
    result.extend(
        [
            index_template.safe_substitute(
                TargetNodeLabel=node_schema.label,
                TargetAttribute=prop_name,
            )
            for prop_name, prop_ref in node_props_as_dict.items()
            if prop_ref.extra_index
        ],
    )
    return result


def build_create_index_queries_for_matchlink(
    rel_schema: CartographyRelSchema,
) -> list[str]:
    """
    Generate queries to create indexes for the given CartographyRelSchema and all node types attached to it via its
    relationships.
    :param rel_schema: The CartographyRelSchema object
    :return: A list of queries of the form `CREATE INDEX IF NOT EXISTS FOR (n:$TargetNodeLabel) ON (n.$TargetAttribute)`
    """
    if not rel_schema.source_node_matcher:
        logger.warning(
            f"No source node matcher found for {rel_schema.rel_label}; returning empty list."
            "Please note that build_create_index_queries_for_matchlink() is only used for load_matchlinks() where we match on "
            "and connect existing nodes in the graph."
        )
        return []

    index_template = Template(
        "CREATE INDEX IF NOT EXISTS FOR (n:$NodeLabel) ON (n.$NodeAttribute);",
    )

    result = []
    for source_key in asdict(rel_schema.source_node_matcher).keys():
        result.append(
            index_template.safe_substitute(
                NodeLabel=rel_schema.source_node_label,
                NodeAttribute=source_key,
            ),
        )
    for target_key in asdict(rel_schema.target_node_matcher).keys():
        result.append(
            index_template.safe_substitute(
                NodeLabel=rel_schema.target_node_label,
                NodeAttribute=target_key,
            ),
        )

    # Create a composite index for the relationship between the source and target nodes.
    # https://neo4j.com/docs/cypher-manual/4.3/indexes-for-search-performance/#administration-indexes-create-a-composite-index-for-relationships
    rel_index_template = Template(
        "CREATE INDEX IF NOT EXISTS FOR ()$rel_direction[r:$RelLabel]$rel_direction_end() "
        "ON (r.lastupdated, r._sub_resource_label, r._sub_resource_id);",
    )
    if rel_schema.direction == LinkDirection.INWARD:
        result.append(
            rel_index_template.safe_substitute(
                RelLabel=rel_schema.rel_label,
                rel_direction="<-",
                rel_direction_end="-",
            )
        )
    else:
        result.append(
            rel_index_template.safe_substitute(
                RelLabel=rel_schema.rel_label,
                rel_direction="-",
                rel_direction_end="->",
            )
        )
    return result


def build_matchlink_query(rel_schema: CartographyRelSchema) -> str:
    """
    Generate a Neo4j query to link two existing nodes when given a CartographyRelSchema object.
    This is only used for load_matchlinks().
    :param rel_schema: The CartographyRelSchema object to generate a query. This CartographyRelSchema object
    - Must have a source_node_matcher and source_node_label defined
    - Must have a CartographyRelProperties object where _sub_resource_label and _sub_resource_id are defined
    :return: A Neo4j query that can be used to link two existing nodes.
    """
    if not rel_schema.source_node_matcher or not rel_schema.source_node_label:
        raise ValueError(
            f"No source node matcher or source node label found for {rel_schema.rel_label}. "
            "MatchLink relationships require a source_node_matcher and source_node_label to be defined."
        )

    rel_props_as_dict = _asdict_with_validate_relprops(rel_schema)

    # These are needed for the cleanup query
    if "_sub_resource_label" not in rel_props_as_dict:
        raise ValueError(
            f"Expected _sub_resource_label to be defined on {rel_schema.properties.__class__.__name__}"
            "Please include `_sub_resource_label: PropertyRef = PropertyRef('_sub_resource_label', set_in_kwargs=True)`"
        )
    if "_sub_resource_id" not in rel_props_as_dict:
        raise ValueError(
            f"Expected _sub_resource_id to be defined on {rel_schema.properties.__class__.__name__}"
            "Please include `_sub_resource_id: PropertyRef = PropertyRef('_sub_resource_id', set_in_kwargs=True)`"
        )

    matchlink_query_template = Template(
        """
        UNWIND $DictList as item
            $source_match
            $target_match
            MERGE $rel
            ON CREATE SET r.firstseen = timestamp()
            SET
                r._module_name = "$module_name",
                r._module_version = "$module_version",
                $set_rel_properties_statement;
        """
    )

    source_match = Template(
        "MATCH (from:$source_node_label{$match_clause})"
    ).safe_substitute(
        source_node_label=rel_schema.source_node_label,
        match_clause=_build_match_clause(rel_schema.source_node_matcher),
    )

    target_match = Template(
        "MATCH (to:$target_node_label{$match_clause})"
    ).safe_substitute(
        target_node_label=rel_schema.target_node_label,
        match_clause=_build_match_clause(rel_schema.target_node_matcher),
    )

    if rel_schema.direction == LinkDirection.INWARD:
        rel = f"(from)<-[r:{rel_schema.rel_label}]-(to)"
    else:
        rel = f"(from)-[r:{rel_schema.rel_label}]->(to)"

    return matchlink_query_template.safe_substitute(
        source_match=source_match,
        target_match=target_match,
        rel=rel,
        module_name=_get_module_from_schema(rel_schema),
        module_version=_get_cartography_version(),
        set_rel_properties_statement=_build_rel_properties_statement(
            "r",
            rel_props_as_dict,
        ),
    )


def _get_cartography_version() -> str:
    """
    Get the current version of the cartography package.

    This function attempts to retrieve the version of the installed cartography package
    using importlib.metadata. If the package is not found (typically in development
    or testing environments), it returns 'dev' as a fallback.

    Returns:
        The version string of the cartography package, or 'dev' if not found
    """
    try:
        return version("cartography")
    except PackageNotFoundError:
        # This can occured if the cartography package is not installed in the environment, typically in development or testing environments.
        logger.warning("cartography package not found. Returning 'dev' version.")
        # Fallback to reading the VERSION file if the package is not found
        return "dev"


def _get_module_from_schema(
    schema,  #: "CartographyNodeSchema" | "CartographyRelSchema",
) -> str:
    """
    Extract the module name from a Cartography schema object.

    This function extracts and formats the module name from a CartographyNodeSchema
    or CartographyRelSchema object. It expects schemas to be part of the official
    cartography.models package hierarchy and returns a formatted string indicating
    the specific cartography module.

    Args:
        schema: A CartographyNodeSchema or CartographyRelSchema object

    Returns:
        A formatted module name string in the format 'cartography:<module_name>'
        or 'unknown:<full_module_path>' if the schema is not from cartography.models
    """
    # If the entity schema does not belong to the cartography.models package,
    # we log a warning and return the full module path.
    if not schema.__module__.startswith("cartography.models."):
        logger.warning(
            "The schema %s does not start with 'cartography.models.'. "
            "This may indicate that the schema is not part of the official cartography models.",
            schema.__module__,
        )
        return f"unknown:{schema.__module__}"
    # Otherwise, we return the module path as a string.
    parts = schema.__module__.split(".")
    return f"cartography:{parts[2]}"
