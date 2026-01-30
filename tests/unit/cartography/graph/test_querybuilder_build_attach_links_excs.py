from dataclasses import dataclass

from pytest import raises

from cartography.graph.querybuilder import _build_attach_additional_links_statement
from cartography.graph.querybuilder import _build_attach_sub_resource_statement
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class MyNodeToBillingUnitRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class MyNodeToBillingUnitRel(CartographyRelSchema):
    target_node_label: str = "BillingUnit"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("billing_unit_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BILLING_UNIT"
    # This is intentionally missing "()" at the end. This will raise an exception!
    properties: MyNodeToBillingUnitRelProps = MyNodeToBillingUnitRelProps


@dataclass(frozen=True)
class MyNodeToOtherNodeRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class MyNodeToOtherNodeRel(CartographyRelSchema):
    target_node_label: str = "OtherNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("other_node_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "REL_LABEL_GOES_HERE"
    # This is intentionally missing "()" at the end. This will raise an exception!
    properties: MyNodeToOtherNodeRelProps = MyNodeToOtherNodeRelProps


@dataclass(frozen=True)
class MyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class MyNodeSchema(CartographyNodeSchema):
    label: str = "MyNode"
    properties: MyNodeProperties = MyNodeProperties()
    sub_resource_relationship: CartographyRelSchema = MyNodeToBillingUnitRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [MyNodeToOtherNodeRel()],
    )


def test_build_attach_addl_links_raises_typeerror():
    """
    _build_attach_additional_links_statement calls asdict() on each rel in  node_schema.other_relationships. If the
    module author forgot to put `()` at the end of each RelSchema, Python will treat it as a "type" and not a
    dataclass, so asdict() will fail with a typeerror.
    This test ensures that we raise a helpful error message for this situation, because IDEs don't always catch this
    mistake.
    """
    with raises(TypeError):
        _ = _build_attach_additional_links_statement(MyNodeSchema().other_relationships)


def test_build_attach_sub_resource_stmt_raises_typeerror():
    """
    Same test logic as test_build_attach_addl_links_raises_typeerror above but for _build_attach_sub_resource_statement.
    """
    with raises(TypeError):
        _ = _build_attach_sub_resource_statement(
            MyNodeSchema().sub_resource_relationship,
        )
