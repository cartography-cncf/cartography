from dataclasses import asdict, fields
from typing import Any

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import OtherRelationships, TargetNodeMatcher, CartographyRelSchema


def _get_propref_keys_from_node_props(node_props: type[CartographyNodeProperties]) -> list[str]:
    result = []
    for field in fields(node_props):
        prop_ref: PropertyRef = field.default
        if prop_ref and prop_ref.set_in_kwargs is False:
            result.append(
                str(prop_ref).split('.')[1]
            )
    return result


def _get_propref_keys_from_rel(rel: type[CartographyRelSchema]) -> list[str]:
    result = []
    tgm: TargetNodeMatcher = rel.target_node_matcher
    for field in fields(tgm):
        prop_ref: PropertyRef = field.default
        if prop_ref and prop_ref.set_in_kwargs is False:
            result.append(
                str(prop_ref).split('.')[1]
            )
    return result




def generate_fake_data(count: int, node_schema: type[CartographyNodeSchema]) -> list[dict[str, Any]]:
    """
    make me 10 fake node As and 10 fake node Bs
    for the node As, attach the 0th rel on them
    """
    fake_data = []
    node_props = node_schema.properties
    props = _get_propref_keys_from_node_props(node_props)
    props_from_other_rels = []

    other_rels: OtherRelationships = node_schema.other_relationships
    if other_rels:
        for rel in other_rels.rels:
            props.extend(_get_propref_keys_from_rel(rel))


    for i in range(count):
        fake_data.append(
            {prop: str(i) for prop in props}
        )
    return fake_data
