from cartography.graph.querybuilder import _build_ontology_field_statement_equal_boolean
from cartography.graph.querybuilder import (
    _build_ontology_field_statement_invert_boolean,
)
from cartography.graph.querybuilder import _build_ontology_field_statement_or_boolean
from cartography.graph.querybuilder import _build_ontology_field_statement_to_boolean
from cartography.models.core.common import PropertyRef
from cartography.models.ontology.mapping.specs import OntologyFieldMapping


def test_build_ontology_field_statement_invert_boolean():
    """
    Test _build_ontology_field_statement_invert_boolean function.
    This function inverts boolean values: "false", "0", "no" => false; anything else => true; null/absent => true
    """
    # Arrange
    mapping_field = OntologyFieldMapping(
        ontology_field="is_active",
        node_field="inactive",
        special_handling="invert_boolean",
    )
    property_ref = PropertyRef("inactive")

    # Act
    result = _build_ontology_field_statement_invert_boolean(mapping_field, property_ref)

    # Assert
    expected = (
        "i._ont_is_active = (NOT(coalesce(toBooleanOrNull(item.inactive), false)))"
    )
    assert result == expected


def test_build_ontology_field_statement_to_boolean():
    """
    Test _build_ontology_field_statement_to_boolean function.
    This function converts values to boolean: "true", "1", "yes" => true; anything else => true; null/absent => false
    """
    # Arrange
    mapping_field = OntologyFieldMapping(
        ontology_field="is_enabled",
        node_field="enabled",
        special_handling="to_boolean",
    )
    property_ref = PropertyRef("enabled")

    # Act
    result = _build_ontology_field_statement_to_boolean(mapping_field, property_ref)

    # Assert
    expected = "i._ont_is_enabled = coalesce(toBooleanOrNull(item.enabled), (item.enabled IS NOT NULL))"
    assert result == expected


def test_build_ontology_field_statement_equal_boolean_with_values():
    """
    Test _build_ontology_field_statement_equal_boolean function with valid values in extra.
    This function compares the field value to a list of expected values.
    """
    # Arrange
    mapping_field = OntologyFieldMapping(
        ontology_field="is_admin",
        node_field="role",
        special_handling="equal_boolean",
        extra={"values": ["admin", "superuser", "root"]},
    )
    property_ref = PropertyRef("role")

    # Act
    result = _build_ontology_field_statement_equal_boolean(mapping_field, property_ref)

    # Assert
    expected = "i._ont_is_admin = (item.role IN ['admin', 'superuser', 'root'])"
    assert result == expected


def test_build_ontology_field_statement_equal_boolean_missing_values():
    """
    Test _build_ontology_field_statement_equal_boolean function when 'values' is missing in extra.
    Should return None and log a warning.
    """
    # Arrange
    mapping_field = OntologyFieldMapping(
        ontology_field="is_admin",
        node_field="role",
        special_handling="equal_boolean",
        extra={},  # Missing 'values'
    )
    property_ref = PropertyRef("role")

    # Act
    result = _build_ontology_field_statement_equal_boolean(mapping_field, property_ref)

    # Assert
    assert result is None


def test_build_ontology_field_statement_equal_boolean_invalid_values_type():
    """
    Test _build_ontology_field_statement_equal_boolean function when 'values' is not a list.
    Should return None and log a warning.
    """
    # Arrange
    mapping_field = OntologyFieldMapping(
        ontology_field="is_admin",
        node_field="role",
        special_handling="equal_boolean",
        extra={"values": "admin"},  # Should be a list, not a string
    )
    property_ref = PropertyRef("role")

    # Act
    result = _build_ontology_field_statement_equal_boolean(mapping_field, property_ref)

    # Assert
    assert result is None


def test_build_ontology_field_statement_or_boolean():
    """
    Test _build_ontology_field_statement_or_boolean function.
    This function combines multiple boolean fields using logical OR.
    """
    # Arrange
    mapping_field = OntologyFieldMapping(
        ontology_field="has_access",
        node_field="direct_access",
        special_handling="or_boolean",
        extra={"fields": ["inherited_access", "group_access"]},
    )
    node_property_map = {
        "direct_access": PropertyRef("direct_access"),
        "inherited_access": PropertyRef("inherited_access"),
        "group_access": PropertyRef("group_access"),
    }

    # Act
    result = _build_ontology_field_statement_or_boolean(
        mapping_field, node_property_map
    )

    # Assert
    expected = (
        "i._ont_has_access = ("
        "coalesce(toBooleanOrNull(item.direct_access), false) OR "
        "coalesce(toBooleanOrNull(item.inherited_access), false) OR "
        "coalesce(toBooleanOrNull(item.group_access), false)"
        ")"
    )
    assert result == expected


def test_build_ontology_field_statement_or_boolean_missing_fields():
    """
    Test _build_ontology_field_statement_or_boolean function when 'fields' is missing in extra.
    Should return None and log a warning.
    """
    # Arrange
    mapping_field = OntologyFieldMapping(
        ontology_field="has_access",
        node_field="direct_access",
        special_handling="or_boolean",
        extra={},  # Missing 'fields'
    )
    node_property_map = {
        "direct_access": PropertyRef("direct_access"),
    }

    # Act
    result = _build_ontology_field_statement_or_boolean(
        mapping_field, node_property_map
    )

    # Assert
    assert result is None


def test_build_ontology_field_statement_or_boolean_invalid_fields_type():
    """
    Test _build_ontology_field_statement_or_boolean function when 'fields' is not a list.
    Should return None and log a warning.
    """
    # Arrange
    mapping_field = OntologyFieldMapping(
        ontology_field="has_access",
        node_field="direct_access",
        special_handling="or_boolean",
        extra={"fields": "inherited_access"},  # Should be a list, not a string
    )
    node_property_map = {
        "direct_access": PropertyRef("direct_access"),
    }

    # Act
    result = _build_ontology_field_statement_or_boolean(
        mapping_field, node_property_map
    )

    # Assert
    assert result is None


def test_build_ontology_field_statement_or_boolean_missing_property_in_map():
    """
    Test _build_ontology_field_statement_or_boolean function when an extra field is not in node_property_map.
    Should skip the missing field and log a warning, but continue with other fields.
    """
    # Arrange
    mapping_field = OntologyFieldMapping(
        ontology_field="has_access",
        node_field="direct_access",
        special_handling="or_boolean",
        extra={"fields": ["inherited_access", "missing_field"]},
    )
    node_property_map = {
        "direct_access": PropertyRef("direct_access"),
        "inherited_access": PropertyRef("inherited_access"),
        # "missing_field" is intentionally not in the map
    }

    # Act
    result = _build_ontology_field_statement_or_boolean(
        mapping_field, node_property_map
    )

    # Assert
    # The result should include direct_access and inherited_access, but skip missing_field
    expected = (
        "i._ont_has_access = ("
        "coalesce(toBooleanOrNull(item.direct_access), false) OR "
        "coalesce(toBooleanOrNull(item.inherited_access), false)"
        ")"
    )
    assert result == expected
