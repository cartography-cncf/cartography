from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import IMAGE


@dataclass(frozen=True)
class UnikraftImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "url", description="Unikraft image identifier, e.g. `my-image:latest`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    url: PropertyRef = PropertyRef(
        "url", extra_index=True, description="Image identifier."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Image creation timestamp."
    )
    initrd_or_rom: PropertyRef = PropertyRef(
        "initrd_or_rom", description="Whether the image boots as an initrd or ROM."
    )
    size_in_bytes: PropertyRef = PropertyRef(
        "size_in_bytes", description="Image size in bytes."
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags associated with the image."
    )
    metro: PropertyRef = PropertyRef(
        "METRO",
        set_in_kwargs=True,
        description="Unikraft metro this image was observed in.",
    )
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID", set_in_kwargs=True, description="Unikraft account UUID."
    )


@dataclass(frozen=True)
class UnikraftImageToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnikraftAccount)-[:RESOURCE]->(:UnikraftImage)
class UnikraftImageToAccountRel(CartographyRelSchema):
    """Connects `UnikraftAccount` to `UnikraftImage` through `RESOURCE`."""

    target_node_label: str = "UnikraftAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnikraftImageToAccountRelProperties = (
        UnikraftImageToAccountRelProperties()
    )


@dataclass(frozen=True)
class UnikraftImageSchema(CartographyNodeSchema):
    """Represents a Unikraft image available to an account."""

    label: str = "UnikraftImage"
    properties: UnikraftImageNodeProperties = UnikraftImageNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([IMAGE])
    sub_resource_relationship: UnikraftImageToAccountRel = UnikraftImageToAccountRel()
