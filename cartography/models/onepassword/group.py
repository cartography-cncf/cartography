from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.onepassword.account import OnePasswordAccountToResourceRel
from cartography.models.ontology.labels import USER_GROUP


@dataclass(frozen=True)
class OnePasswordGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="1Password group UUID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description=(
            "Group name, such as `Owners`, `Administrators`, or a custom group name."
        ),
    )


@dataclass(frozen=True)
class OnePasswordGroupSchema(CartographyNodeSchema):
    """A 1Password group. Members inherit the group's vault access."""

    label: str = "OnePasswordGroup"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_GROUP])
    properties: OnePasswordGroupNodeProperties = OnePasswordGroupNodeProperties()
    sub_resource_relationship: OnePasswordAccountToResourceRel = (
        OnePasswordAccountToResourceRel()
    )
