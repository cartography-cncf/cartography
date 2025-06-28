from dataclasses import dataclass
from datetime import datetime
import math

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeSchema, CartographyNodeProperties
from cartography.models.core.relationships import CartographyRelSchema, OtherRelationships, CartographyRelProperties, TargetNodeMatcher, LinkDirection, make_target_node_matcher
from cartography.graph.sanitizer import _node_schema_to_property_refs, _auto_format_field, data_dict_cleanup


@dataclass(frozen=True)
class FakeToParentRelProperties(CartographyRelProperties):
    rel_property: PropertyRef = PropertyRef("rel_property", auto_format=str)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FakeToParentRel(CartographyRelSchema):
    rel_label: str = "FAKE_TO_PARENT"
    target_node_label: str = "FakeParentNode"
    target_node_matcher: dict[str, PropertyRef] = make_target_node_matcher(
        {"id": PropertyRef("PARENT_ID", set_in_kwargs=True)}
    )
    properties: FakeToParentRelProperties = FakeToParentRelProperties()
    direction: LinkDirection = LinkDirection.INWARD


@dataclass(frozen=True)
class FakeToOtherRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FakeToOtherRel(CartographyRelSchema):
    rel_label: str = "FAKE_TO_OTHER"
    target_node_label: str = "FakeOtherNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("others_id", one_to_many=True)}
    )
    properties: FakeToOtherRelProperties = FakeToOtherRelProperties()
    direction: LinkDirection = LinkDirection.OUTWARD


@dataclass(frozen=True)
class FakeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", auto_format=str)
    number: PropertyRef = PropertyRef("nested.number", auto_format=int)
    float_value: PropertyRef = PropertyRef("multi_nested.deep.float", auto_format=float)
    dict_value: PropertyRef = PropertyRef("dict_value", auto_format=dict)
    list_value: PropertyRef = PropertyRef("list_value", auto_format=list)
    lastseen: PropertyRef = PropertyRef("lastseen", auto_format=datetime)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

@dataclass(frozen=True)
class FakeNodeSchema(CartographyNodeSchema):
    label: str = "FakeNode"
    properties: FakeProperties = FakeProperties()
    sub_resource_relationship: FakeToParentRel = FakeToParentRel()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[FakeToOtherRel()]
    )


def test_node_schema_to_property_refs():
    """ This test cover the extraction of all needed field in the data dict from the NodeSchema."""
    # Create a node schema instance
    node_schema = FakeNodeSchema()

    # Get the property refs
    property_refs = _node_schema_to_property_refs(node_schema)

    # Check if the properties are correctly extracted
    assert isinstance(property_refs, dict)
    assert list(property_refs.keys()) == [
        'id',
        'lastupdated',
        'name',
        'nested.number',
        'multi_nested.deep.float',
        'dict_value',
        'list_value',
        'lastseen',
        'rel_property',
        'PARENT_ID',
        'others_id',
    ]


def test_auto_format_propertyref():
    """ This test cover the auto_format functionality of PropertyRef."""
    # Test without auto_format flag
    no_format = PropertyRef('fake')
    assert _auto_format_field(no_format, 42) == 42
    # Check with auto_format flag set to str
    str_format = PropertyRef('fake', auto_format=str)
    assert _auto_format_field(str_format, None) is None
    assert _auto_format_field(str_format, 'foo') == 'foo'
    assert _auto_format_field(str_format, 42) == '42'
    assert _auto_format_field(str_format, '') is None
    # Check with auto_format flag set to int
    int_format = PropertyRef('fake', auto_format=int)
    assert _auto_format_field(int_format, 42) == 42
    assert _auto_format_field(int_format, "42") == 42
    assert _auto_format_field(int_format, "foo") == "foo" # Should failsafe as string
    # Check with auto_format flag set to float
    float_format = PropertyRef('fake', auto_format=float)
    assert math.isclose(_auto_format_field(float_format, 42.42), 42.42)
    assert math.isclose(_auto_format_field(float_format, "42.42"), 42.42)
    assert _auto_format_field(float_format, "foo") == "foo" # Should failsafe as string
    # Check with auto_format flag set to dict
    dict_format = PropertyRef('fake', auto_format=dict)
    assert _auto_format_field(dict_format, {'foo': 'bar'}) == {'foo': 'bar'}
    assert _auto_format_field(dict_format, {}) is None
    # Check with auto_format flag set to list
    list_format = PropertyRef('fake', auto_format=list)
    assert _auto_format_field(list_format, ['foo']) == ['foo']
    assert _auto_format_field(list_format, []) is None
    # Check with auto_format flag set to datetime
    datetime_format = PropertyRef('fake', auto_format=datetime)
    now = datetime.now()
    assert _auto_format_field(datetime_format, now) == now
    assert _auto_format_field(datetime_format, now.isoformat()) == now
    assert _auto_format_field(datetime_format, 'foo') == 'foo' # Should failsafe as string
    assert _auto_format_field(datetime_format, now.timestamp()) == now


def test_data_dict_cleanup():
    """ This test cover the data_dict_cleanup function."""
    # Create a node schema instance
    node_schema = FakeNodeSchema()

    # Create a test data dict
    test_data = {
        "nested": {
            "number": "42",
            "junk": "qux"
        },
        "name": "keep this",
        "junk": "not that",
        "multi_nested": {
            "deep": {
                "float": "42.42",
                "junk": "do not keep that",
                "not": "that neither"
            },
        },
        "dict_value": {
            "keep": "this",
            "and": "this"
        },
    }
    expected_cleaned_data = {
        "nested": {
            "number": 42
        },
        "name": "keep this",
        "multi_nested": {
            "deep": {
                "float": 42.42
            }
        },
        "dict_value": {
            "keep": "this",
            "and": "this"
        },
    }

    # Clean the data dict
    cleaned_data = data_dict_cleanup(node_schema, test_data)

    # Check if the cleaned data contains only the expected keys
    assert cleaned_data == expected_cleaned_data
