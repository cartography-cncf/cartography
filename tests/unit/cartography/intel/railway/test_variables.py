from cartography.models.railway.variable import RailwayVariableNodeProperties


def test_railway_variable_schema_has_no_value_property():
    # Guard: Railway can return variable values. Cartography must never store them: no
    # property may be named `value` (the attribute name is the stored property name),
    # and no property may be read from the `value` field under another name.
    fields = RailwayVariableNodeProperties.__dataclass_fields__.values()
    property_names = {field.name for field in fields}
    source_fields = {field.default.name for field in fields}
    assert "value" not in property_names
    assert "value" not in source_fields
