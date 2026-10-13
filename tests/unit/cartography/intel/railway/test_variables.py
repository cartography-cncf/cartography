from cartography.models.railway.variable import RailwayVariableNodeProperties


def test_railway_variable_schema_has_no_value_property():
    # Guard: Railway can return variable values. Cartography must never store them, so a
    # `value` property must never appear on this schema.
    property_names = {
        field.name
        for field in RailwayVariableNodeProperties.__dataclass_fields__.values()
    }
    assert "value" not in property_names
