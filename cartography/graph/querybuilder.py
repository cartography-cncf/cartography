import logging
from dataclasses import asdict
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version
from string import Template

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
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

    This function creates a SET clause for Neo4j queries that assigns values from the data item
    to node properties, excluding the 'id' field which is handled by the MERGE clause.
    It also handles setting extra node labels if provided.

    Args:
        node_property_map (Dict[str, PropertyRef]): Mapping of node attribute names as str to PropertyRef objects.
        extra_node_labels (Optional[ExtraNodeLabels], optional): ExtraNodeLabels object to set on the node as string.
            Defaults to None.

    Returns:
        str: The resulting Neo4j SET clause to set the given attributes on the node.

    Examples:
        >>> node_property_map = {
        ...     'id': PropertyRef("Id"),
        ...     'node_prop_1': PropertyRef("Prop1"),
        ...     'node_prop_2': PropertyRef("Prop2", set_in_kwargs=True),
        ... }
        >>> set_clause = _build_node_properties_statement(node_property_map)
        >>> # Returns:
        >>> # i.node_prop_1 = item.Prop1,
        >>> # i.node_prop_2 = $Prop2
        >>> # (note: 'id' is excluded as it's handled by MERGE)

        >>> # With extra labels
        >>> extra_labels = ExtraNodeLabels(['Resource', 'CloudAsset'])
        >>> set_clause = _build_node_properties_statement(node_property_map, extra_labels)
        >>> # Returns the property assignments plus:
        >>> # i:Resource:CloudAsset

    Note:
        The 'id' field is intentionally excluded from the SET clause as it's already
        handled by the MERGE clause in the query pattern. The variable 'i' refers
        to the Neo4j node being processed.
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

    # Set extra labels on the node if specified (excluding conditional labels)
    if extra_node_labels:
        # Filter out ConditionalNodeLabel objects - only include string labels
        string_labels = [
            label for label in extra_node_labels.labels if isinstance(label, str)
        ]
        if string_labels:
            extra_labels = ":".join(string_labels)
            set_clause += f",\n                i:{extra_labels}"
    return set_clause


def _build_rel_properties_statement(
    rel_var: str,
    rel_property_map: dict[str, PropertyRef] | None = None,
) -> str:
    """
    Generate a Neo4j clause that sets relationship properties using the given mapping of attribute names to PropertyRefs.

    This function creates a SET clause for Neo4j relationships, mapping relationship
    properties from the data item to the relationship variable.

    Args:
        rel_var (str): The variable name to use for the relationship in the Neo4j query.
        rel_property_map (Optional[Dict[str, PropertyRef]], optional): Mapping of relationship
            attribute names as str to PropertyRef objects. Defaults to None.

    Returns:
        str: The resulting Neo4j SET clause to set the given attributes on the relationship.
            Returns empty string if rel_property_map is None or empty.

    Examples:
        >>> rel_property_map = {
        ...     'rel_prop_1': PropertyRef("Prop1"),
        ...     'rel_prop_2': PropertyRef("Prop2", set_in_kwargs=True),
        ... }
        >>> set_clause = _build_rel_properties_statement('r', rel_property_map)
        >>> # Returns:
        >>> # r.rel_prop_1 = item.Prop1,
        >>> # r.rel_prop_2 = $Prop2

        >>> # With empty property map
        >>> set_clause = _build_rel_properties_statement('r', None)
        >>> # Returns: ""

    Note:
        The rel_var parameter should match the relationship variable used in the
        Neo4j MERGE or MATCH clause.
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

    This function creates a property matching clause for Neo4j queries, typically used
    within MATCH statements to identify nodes based on their properties.

    Args:
        matcher (TargetNodeMatcher | SourceNodeMatcher): A matcher object containing
            the property keys and PropertyRef values to match against.

    Returns:
        str: A Neo4j match clause in the format "key1: value1, key2: value2, ...".

    Examples:
        >>> matcher = TargetNodeMatcher(
        ...     id=PropertyRef('target_id'),
        ...     name=PropertyRef('target_name')
        ... )
        >>> clause = _build_match_clause(matcher)
        >>> # Returns: "id: item.target_id, name: item.target_name"

        >>> # Used in a MATCH statement
        >>> # MATCH (n:Node{id: item.target_id, name: item.target_name})

    Note:
        The returned clause is designed to be used within curly braces in Neo4j
        MATCH statements for property-based node matching.
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
    Generate a Neo4j WHERE clause for relationship matching with advanced matching options.

    This function creates WHERE clauses for Neo4j queries, specifically designed for
    relationship matching scenarios where case-insensitive, fuzzy, or one-to-many
    matching is required.

    Args:
        node_var (str): The variable name to use for the node in the Neo4j query.
        matcher (TargetNodeMatcher): A TargetNodeMatcher object containing properties
            with matching configuration (ignore_case, fuzzy_and_ignore_case, one_to_many).

    Returns:
        str: A Neo4j WHERE clause with appropriate matching logic joined by AND operators.

    Examples:
        >>> matcher = TargetNodeMatcher(
        ...     name=PropertyRef('name', ignore_case=True),
        ...     tags=PropertyRef('tag_list', one_to_many=True)
        ... )
        >>> where_clause = _build_where_clause_for_rel_match('n', matcher)
        >>> # Returns:
        >>> # toLower(n.name) = toLower(item.name) AND
        >>> # n.tags IN item.tag_list

        >>> # With fuzzy matching
        >>> matcher = TargetNodeMatcher(
        ...     description=PropertyRef('desc', fuzzy_and_ignore_case=True)
        ... )
        >>> where_clause = _build_where_clause_for_rel_match('n', matcher)
        >>> # Returns: toLower(n.description) CONTAINS toLower(item.desc)

    Note:
        This function is specifically intended for relationship joining where
        case-insensitive or fuzzy matching is needed, unlike _build_match_clause
        which only supports exact matching.
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
    Convert CartographyRelSchema properties to dict with validation and helpful error messages.

    This function converts a CartographyRelSchema's properties to a dictionary while
    providing helpful error messages when common instantiation mistakes are made,
    such as forgetting to add parentheses when instantiating dataclass properties.

    Args:
        link (CartographyRelSchema): The CartographyRelSchema object to convert to a dict.

    Returns:
        Dict[str, PropertyRef]: A dictionary of relationship properties as str keys
            mapped to PropertyRef values.

    Raises:
        TypeError: If the link's properties are not a dataclass instance, which indicates
            that the user forgot to instantiate the properties dataclass with `()`.

    Examples:
        >>> # Correct usage
        >>> class MyRelProps:
        ...     prop1: PropertyRef = PropertyRef('prop1')
        ...     prop2: PropertyRef = PropertyRef('prop2')
        >>>
        >>> rel_schema = CartographyRelSchema(
        ...     target_node_label='Target',
        ...     properties=MyRelProps(),  # Note the ()
        ...     ...
        ... )
        >>> props_dict = _asdict_with_validate_relprops(rel_schema)
        >>> # Returns: {'prop1': PropertyRef('prop1'), 'prop2': PropertyRef('prop2')}

        >>> # Incorrect usage (missing parentheses)
        >>> rel_schema = CartographyRelSchema(
        ...     target_node_label='Target',
        ...     properties=MyRelProps,  # Missing ()
        ...     ...
        ... )
        >>> props_dict = _asdict_with_validate_relprops(rel_schema)
        >>> # Raises TypeError with helpful message

    Note:
        This validation is particularly useful because IDEs don't always catch
        the missing parentheses error when instantiating dataclass properties.
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
                'TypeError thrown when trying to draw relation "%s" to a "%s" '
                "node. Please make sure that you did not forget to write `()` when specifying `properties` in the"
                "dataclass. "
                "For example, do `properties: RelProp = RelProp()`; NOT `properties: RelProp = RelProp`.",
                link.rel_label,
                link.target_node_label,
            )
        raise
    return rel_props_as_dict


def _build_attach_sub_resource_statement(
    sub_resource_link: CartographyRelSchema | None = None,
) -> str:
    """
    Generate a Neo4j statement to attach a sub resource to a node.

    A 'sub resource' is a cartography term for billing units of a given resource.
    This function creates the Neo4j clause to connect nodes to their sub resources,
    handling the relationship direction and properties appropriately.

    Args:
        sub_resource_link (Optional[CartographyRelSchema], optional): The CartographyRelSchema
            object connecting previous node(s) to the sub resource. Defaults to None.

    Returns:
        str: A Neo4j clause that connects previous node(s) to a sub resource, taking into
            account the labels, attribute keys, and directionality. Returns empty string
            if sub_resource_link is None.

    Examples:
        Sub resource examples by cloud provider:
        - AWS: AWSAccount
        - Azure: Subscription
        - GCP: GCPProject

        >>> # AWS example
        >>> sub_resource_link = CartographyRelSchema(
        ...     target_node_label='AWSAccount',
        ...     target_node_matcher=TargetNodeMatcher(id=PropertyRef('account_id')),
        ...     direction=LinkDirection.INWARD,
        ...     rel_label='RESOURCE',
        ...     properties=SubResourceRel()
        ... )
        >>> statement = _build_attach_sub_resource_statement(sub_resource_link)
        >>> # Returns Neo4j clause for connecting to AWS account

        >>> # No sub resource
        >>> statement = _build_attach_sub_resource_statement(None)
        >>> # Returns: ""

    Note:
        This is a private function not meant to be called outside of build_ingest_query().
        The generated statement includes proper firstseen timestamp handling and
        relationship property setting.
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
    Generate a Neo4j statement to attach multiple additional relationships to nodes.

    This function creates Neo4j clauses to connect nodes with additional relationships
    beyond the sub resource relationship. It handles multiple relationship types,
    directions, and properties in a single statement.

    Args:
        additional_relationships (Optional[OtherRelationships], optional): List of
            CartographyRelSchema objects describing additional relationships to create
            from the previous node(s) in the query. Defaults to None.

    Returns:
        str: A Neo4j clause that connects previous node(s) to the additional relationships,
            taking into account labels, attribute keys, and directionality. Returns empty
            string if additional_relationships is None.

    Examples:
        >>> # Multiple additional relationships
        >>> additional_rels = OtherRelationships([
        ...     CartographyRelSchema(
        ...         target_node_label='Role',
        ...         target_node_matcher=TargetNodeMatcher(name=PropertyRef('role_name')),
        ...         direction=LinkDirection.OUTWARD,
        ...         rel_label='HAS_ROLE',
        ...         properties=RoleRel()
        ...     ),
        ...     CartographyRelSchema(
        ...         target_node_label='Group',
        ...         target_node_matcher=TargetNodeMatcher(id=PropertyRef('group_id')),
        ...         direction=LinkDirection.INWARD,
        ...         rel_label='MEMBER_OF',
        ...         properties=GroupRel()
        ...     )
        ... ])
        >>> statement = _build_attach_additional_links_statement(additional_rels)
        >>> # Returns Neo4j UNION clause connecting to both Role and Group nodes

        >>> # No additional relationships
        >>> statement = _build_attach_additional_links_statement(None)
        >>> # Returns: ""

    Note:
        This is a private function not meant to be called outside of build_ingestion_query().
        The generated statement uses UNION to combine multiple relationship attachments
        and includes proper firstseen timestamp handling.
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
    Generate Neo4j subqueries to attach sub resource and/or other relationships.

    This function uses Neo4j subqueries to attach relationships, allowing the query
    to continue running even if only partial relationship data is available. This
    approach enables graceful handling of missing relationship data.

    Args:
        sub_resource_relationship (Optional[CartographyRelSchema]): CartographyRelSchema
            that describes the sub resource relationship to attach.
        other_relationships (Optional[OtherRelationships]): OtherRelationships object
            that describes the additional relationships to attach.

    Returns:
        str: A Neo4j clause that attaches the sub resource and/or other relationships
            to the previous node(s) in the query. Returns empty string if both
            parameters are None.

    Examples:
        >>> # With both sub resource and other relationships
        >>> sub_resource_rel = CartographyRelSchema(...)
        >>> other_rels = OtherRelationships([...])
        >>> statement = _build_attach_relationships_statement(sub_resource_rel, other_rels)
        >>> # Returns:
        >>> # WITH i, item
        >>> # CALL {
        >>> #     [sub resource attachment] UNION [other relationships attachment]
        >>> # }

        >>> # With only sub resource
        >>> statement = _build_attach_relationships_statement(sub_resource_rel, None)
        >>> # Returns subquery with only sub resource attachment

        >>> # No relationships
        >>> statement = _build_attach_relationships_statement(None, None)
        >>> # Returns: ""

    Note:
        Subqueries allow the ingestion query to continue even if we only have data
        for some relationships. For example, if an EC2Instance has attachments to
        NetworkInterfaces and AWSAccounts, but data only includes EC2Instance to
        AWSAccount information, the query will ignore null relationships and continue
        to MERGE the existing ones.
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
    Check if a relationship schema is present on a node schema.

    This function determines whether a given relationship schema is defined
    on the provided node schema, checking both sub resource relationships
    and other relationships.

    Args:
        node_schema (CartographyNodeSchema): The node schema to check for the relationship.
        rel_schema (CartographyRelSchema): The relationship schema to look for.

    Returns:
        bool: True if the relationship schema is present on the node schema, False otherwise.

    Examples:
        >>> node_schema = CartographyNodeSchema(
        ...     label='AWSUser',
        ...     sub_resource_relationship=account_rel,
        ...     other_relationships=OtherRelationships([role_rel, group_rel])
        ... )
        >>> rel_present_on_node_schema(node_schema, account_rel)
        True
        >>> rel_present_on_node_schema(node_schema, role_rel)
        True
        >>> rel_present_on_node_schema(node_schema, unknown_rel)
        False

    Note:
        This function is commonly used for validation in cleanup operations and
        query building to ensure that only valid relationships are processed.
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
    Filter and validate selected relationships against a node schema.

    This function ensures that selected relationships specified to build_ingestion_query()
    are actually present on the node schema. It validates the relationships exist and
    separates them into sub resource and other relationship categories.

    Args:
        node_schema (CartographyNodeSchema): The node schema object to filter relationships against.
        selected_relationships (Set[CartographyRelSchema]): The set of relationships to check
            if they exist in the node schema. If empty set, this means no relationships have
            been selected. None is not an accepted value.

    Returns:
        Tuple[Optional[CartographyRelSchema], Optional[OtherRelationships]]: A tuple containing:
            - Sub resource relationship (if present in selected_relationships)
            - OtherRelationships object containing all other relationships from
              selected_relationships that are present in the node schema

    Raises:
        ValueError: If any selected relationship is not defined on the node schema.

    Examples:
        >>> node_schema = CartographyNodeSchema(
        ...     label='EC2Instance',
        ...     sub_resource_relationship=account_rel,
        ...     other_relationships=OtherRelationships([vpc_rel, subnet_rel])
        ... )
        >>>
        >>> # Select subset of relationships
        >>> selected = {account_rel, vpc_rel}
        >>> sub_rel, other_rels = filter_selected_relationships(node_schema, selected)
        >>> # Returns: (account_rel, OtherRelationships([vpc_rel]))

        >>> # Empty set means no relationships selected
        >>> sub_rel, other_rels = filter_selected_relationships(node_schema, set())
        >>> # Returns: (None, None)

        >>> # Invalid relationship raises error
        >>> invalid_selected = {unknown_rel}
        >>> filter_selected_relationships(node_schema, invalid_selected)
        >>> # Raises: ValueError

    Note:
        This function is used internally by build_ingestion_query() to validate
        and filter the selected_relationships parameter.
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
    Generate a Neo4j query from a CartographyNodeSchema to ingest nodes and relationships.

    This function creates an optimized Neo4j query that cartography module authors can use
    instead of handwriting their own queries. It handles node creation, property setting,
    and relationship attachment in a single optimized query.

    Args:
        node_schema (CartographyNodeSchema): The CartographyNodeSchema object to build a Neo4j query from.
        selected_relationships (Optional[Set[CartographyRelSchema]], optional): If specified, generates
            a query that attaches only the relationships in this set. The RelSchema specified must be
            present in node_schema.sub_resource_relationship or node_schema.other_relationships.
            Defaults to None (uses all relationships). If empty set, creates query with no relationships.

    Returns:
        str: An optimized Neo4j query that can be used to ingest nodes and relationships.

    Examples:
        >>> # Basic node schema with relationships
        >>> node_schema = CartographyNodeSchema(
        ...     label='EC2Instance',
        ...     properties=EC2InstanceProperties(),
        ...     sub_resource_relationship=account_rel,
        ...     other_relationships=OtherRelationships([vpc_rel, subnet_rel])
        ... )
        >>> query = build_ingestion_query(node_schema)
        >>> # Returns complete ingestion query with all relationships

        >>> # Query with selected relationships only
        >>> selected_rels = {account_rel, vpc_rel}
        >>> query = build_ingestion_query(node_schema, selected_rels)
        >>> # Returns query with only account and VPC relationships

        >>> # Query with no relationships
        >>> query = build_ingestion_query(node_schema, set())
        >>> # Returns query that only creates nodes, no relationships

    Note:
        - The resulting query uses the UNWIND + MERGE pattern for batch loading data efficiently
        - The query assumes a list of dicts will be passed via parameter $DictList
        - The query sets `firstseen` attributes on all created nodes and relationships
        - The query is intended for use with cartography.core.client.tx.load_graph_data()
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


def build_conditional_label_queries(
    node_schema: CartographyNodeSchema,
) -> list[str]:
    """
    Generate Neo4j queries to apply conditional labels to nodes.

    Conditional labels are labels that are only applied to nodes matching specific conditions.
    This function generates one query per ConditionalNodeLabel defined in the node schema's
    extra_node_labels.

    Args:
        node_schema (CartographyNodeSchema): The CartographyNodeSchema object containing
            conditional labels in its extra_node_labels property.

    Returns:
        list[str]: A list of Neo4j queries, one per conditional label. Each query matches
            nodes of the schema's primary label that satisfy the conditions, and applies
            the conditional label.

    Examples:
        >>> # Given a schema with a conditional label
        >>> node_schema = CartographyNodeSchema(
        ...     label='AWSResource',
        ...     extra_node_labels=ExtraNodeLabels([
        ...         'Resource',
        ...         ConditionalNodeLabel(label='Critical', conditions={'severity': 'high'}),
        ...     ])
        ... )
        >>> queries = build_conditional_label_queries(node_schema)
        >>> # Returns:
        >>> # ['MATCH (n:AWSResource) WHERE n.severity = "high" SET n:Critical']

    Note:
        - Only ConditionalNodeLabel objects are processed; string labels are ignored
        - Returns an empty list if no conditional labels are defined
        - Values are escaped for Cypher string literals
    """
    if not node_schema.extra_node_labels:
        return []

    # Extract only ConditionalNodeLabel objects
    conditional_labels = [
        label
        for label in node_schema.extra_node_labels.labels
        if isinstance(label, ConditionalNodeLabel)
    ]

    if not conditional_labels:
        return []

    queries = []
    sub_rel = node_schema.sub_resource_relationship

    # Build the sub-resource matching clause if a sub_resource_relationship exists
    # This scopes the queries to the current tenant to avoid affecting other tenants' nodes
    if sub_rel:
        # Build the relationship pattern based on direction
        if sub_rel.direction == LinkDirection.INWARD:
            # (node)<-[:REL]-(sub_resource)
            rel_pattern = f"<-[:{sub_rel.rel_label}]-"
        else:
            # (node)-[:REL]->(sub_resource)
            rel_pattern = f"-[:{sub_rel.rel_label}]->"

        # Build the match clause for the sub-resource node
        sub_match_clause = _build_match_clause(sub_rel.target_node_matcher)

        # Scoped templates that filter by sub-resource
        remove_template = Template(
            """
            MATCH (n:$node_label:$conditional_label)$rel_pattern(sub:$sub_label{$sub_match_clause})
            REMOVE n:$conditional_label
            """,
        )

        set_template = Template(
            """
            MATCH (n:$node_label)$rel_pattern(sub:$sub_label{$sub_match_clause})
            WHERE $where_clause
            SET n:$conditional_label
            """,
        )
    else:
        # Unscoped templates for global resources without a tenant relationship
        remove_template = Template(
            """
            MATCH (n:$node_label:$conditional_label)
            REMOVE n:$conditional_label
            """,
        )

        set_template = Template(
            """
            MATCH (n:$node_label)
            WHERE $where_clause
            SET n:$conditional_label
            """,
        )

    for cond_label in conditional_labels:
        # Skip conditional labels with empty conditions - they would apply to all nodes,
        # which should be done with a regular string label instead
        if not cond_label.conditions:
            logger.warning(
                "ConditionalNodeLabel '%s' on node schema '%s' has empty conditions. "
                "Skipping. Use a string label instead to apply a label to all nodes.",
                cond_label.label,
                node_schema.label,
            )
            continue

        # Build WHERE clause from conditions
        where_parts = []
        for field_name, field_value in cond_label.conditions.items():
            # Escape the value for Cypher string literal
            escaped_value = _escape_cypher_string(str(field_value))
            where_parts.append(f'n.{field_name} = "{escaped_value}"')

        where_clause = " AND ".join(where_parts)

        if sub_rel:
            # Scoped queries
            remove_query = remove_template.safe_substitute(
                node_label=node_schema.label,
                conditional_label=cond_label.label,
                rel_pattern=rel_pattern,
                sub_label=sub_rel.target_node_label,
                sub_match_clause=sub_match_clause,
            )
            set_query = set_template.safe_substitute(
                node_label=node_schema.label,
                where_clause=where_clause,
                conditional_label=cond_label.label,
                rel_pattern=rel_pattern,
                sub_label=sub_rel.target_node_label,
                sub_match_clause=sub_match_clause,
            )
        else:
            # Unscoped queries
            remove_query = remove_template.safe_substitute(
                node_label=node_schema.label,
                conditional_label=cond_label.label,
            )
            set_query = set_template.safe_substitute(
                node_label=node_schema.label,
                where_clause=where_clause,
                conditional_label=cond_label.label,
            )

        queries.append(remove_query)
        queries.append(set_query)

    return queries


def build_create_index_queries(node_schema: CartographyNodeSchema) -> list[str]:
    """
    Generate queries to create indexes for the given CartographyNodeSchema and all node types attached to it via its
    relationships.

    This function creates Neo4j CREATE INDEX queries for optimal query performance.
    It handles indexes for the main node schema, its relationships, and any extra
    labels or properties that require indexing.

    Args:
        node_schema (CartographyNodeSchema): The Cartography node schema object to create indexes for.

    Returns:
        List[str]: A list of CREATE INDEX queries of the form
                   `CREATE INDEX IF NOT EXISTS FOR (n:$TargetNodeLabel) ON (n.$TargetAttribute)`

    Examples:
        >>> node_schema = CartographyNodeSchema(
        ...     label='AWSUser',
        ...     properties=Properties(
        ...         id=PropertyRef('id'),
        ...         arn=PropertyRef('arn', extra_index=True),
        ...         name=PropertyRef('name')
        ...     ),
        ...     sub_resource_relationship=account_rel,
        ...     other_relationships=OtherRelationships([role_rel])
        ... )
        >>> queries = build_create_index_queries(node_schema)
        >>> # Returns indexes for:
        >>> # - AWSUser.id and AWSUser.lastupdated (standard indexes)
        >>> # - AWSUser.arn (extra index due to extra_index=True)
        >>> # - Target node properties from relationships
        >>> # - Extra node labels if present

    Note:
        This function automatically creates indexes for 'id' and 'lastupdated' fields
        on all node types, plus any properties marked with extra_index=True.
        It also indexes target node properties from all relationships.
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
        for label in node_schema.extra_node_labels.labels:
            if isinstance(label, str):
                # Simple string label - create index on id
                result.append(
                    index_template.safe_substitute(
                        TargetNodeLabel=label,
                        TargetAttribute="id",  # Precondition: 'id' is defined on all cartography node_schema objects.
                    ),
                )
            elif isinstance(label, ConditionalNodeLabel):
                # Conditional label - create index on the conditional label's id
                result.append(
                    index_template.safe_substitute(
                        TargetNodeLabel=label.label,
                        TargetAttribute="id",
                    ),
                )
                # Also create indexes on the condition fields for the primary node label
                # to speed up the WHERE clause in the conditional label query
                for condition_field in label.conditions.keys():
                    result.append(
                        index_template.safe_substitute(
                            TargetNodeLabel=node_schema.label,
                            TargetAttribute=condition_field,
                        ),
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
    Generate queries to create indexes for the given CartographyRelSchema and all node types attached to it.

    This function creates Neo4j CREATE INDEX queries specifically for matchlink operations,
    which are used to connect existing nodes in the graph. It creates indexes for both
    source and target node properties, plus composite relationship indexes.

    Args:
        rel_schema (CartographyRelSchema): The CartographyRelSchema object to create indexes for.

    Returns:
        List[str]: A list of CREATE INDEX queries for source nodes, target nodes, and relationships.
                   Returns empty list if source_node_matcher is not defined.

    Examples:
        >>> rel_schema = CartographyRelSchema(
        ...     source_node_label='User',
        ...     source_node_matcher=SourceNodeMatcher(id=PropertyRef('user_id')),
        ...     target_node_label='Role',
        ...     target_node_matcher=TargetNodeMatcher(name=PropertyRef('role_name')),
        ...     rel_label='HAS_ROLE',
        ...     direction=LinkDirection.OUTWARD
        ... )
        >>> queries = build_create_index_queries_for_matchlink(rel_schema)
        >>> # Returns:
        >>> # - CREATE INDEX FOR (n:User) ON (n.id)
        >>> # - CREATE INDEX FOR (n:Role) ON (n.name)
        >>> # - CREATE INDEX FOR ()-[r:HAS_ROLE]->() ON (r.lastupdated, r._sub_resource_label, r._sub_resource_id)

        >>> # Missing source node matcher
        >>> incomplete_rel = CartographyRelSchema(target_node_label='Role', ...)
        >>> queries = build_create_index_queries_for_matchlink(incomplete_rel)
        >>> # Returns: [] (empty list with warning logged)

    Note:
        This function is only used for load_matchlinks() where we match and connect
        existing nodes in the graph. It requires source_node_matcher to be defined
        and creates composite indexes for relationship performance.
    """
    if not rel_schema.source_node_matcher:
        logger.warning(
            "No source node matcher found for %s; returning empty list. "
            "Please note that build_create_index_queries_for_matchlink() is only used for load_matchlinks() where we match on "
            "and connect existing nodes in the graph.",
            rel_schema.rel_label,
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

    This function creates a Neo4j query specifically for connecting existing nodes in the graph
    based on their properties. It is designed for use with load_matchlinks() operations.

    Args:
        rel_schema (CartographyRelSchema): The CartographyRelSchema object to generate a query for.
            This object must have:
            - source_node_matcher and source_node_label defined
            - CartographyRelProperties with _sub_resource_label and _sub_resource_id defined

    Returns:
        str: A Neo4j query that can be used to link two existing nodes.

    Raises:
        ValueError: If the rel_schema does not have a source_node_matcher or source_node_label defined,
            or if the rel_schema properties do not have _sub_resource_label or _sub_resource_id defined.

    Examples:
        >>> rel_schema = CartographyRelSchema(
        ...     source_node_label='User',
        ...     source_node_matcher=SourceNodeMatcher(id=PropertyRef('user_id')),
        ...     target_node_label='Role',
        ...     target_node_matcher=TargetNodeMatcher(name=PropertyRef('role_name')),
        ...     rel_label='HAS_ROLE',
        ...     direction=LinkDirection.OUTWARD,
        ...     properties=UserRoleRel(
        ...         _sub_resource_label=PropertyRef('_sub_resource_label', set_in_kwargs=True),
        ...         _sub_resource_id=PropertyRef('_sub_resource_id', set_in_kwargs=True)
        ...     )
        ... )
        >>> query = build_matchlink_query(rel_schema)
        >>> # Returns:
        >>> # UNWIND $DictList as item
        >>> #     MATCH (from:User{id: item.user_id})
        >>> #     MATCH (to:Role{name: item.role_name})
        >>> #     MERGE (from)-[r:HAS_ROLE]->(to)
        >>> #     ON CREATE SET r.firstseen = timestamp()
        >>> #     SET r._sub_resource_label = $_sub_resource_label, ...

    Note:
        This function is only used for load_matchlinks() operations where we need to
        connect existing nodes. The _sub_resource_label and _sub_resource_id properties
        are required for the cleanup query functionality.
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
            f"Expected _sub_resource_label to be defined on {rel_schema.properties.__class__.__name__}. "
            "Please include `_sub_resource_label: PropertyRef = PropertyRef('_sub_resource_label', set_in_kwargs=True)`"
        )
    if "_sub_resource_id" not in rel_props_as_dict:
        raise ValueError(
            f"Expected _sub_resource_id to be defined on {rel_schema.properties.__class__.__name__}. "
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
