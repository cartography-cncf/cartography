from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SentraDataClassNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Sentra data class ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Sentra data class was last seen.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Data class name, for example `Social Security Number`.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Data class description.",
    )
    category: PropertyRef = PropertyRef(
        "category",
        extra_index=True,
        description="Data class category, for example `Personal`, `Financial`, or `Credentials`.",
    )
    class_type: PropertyRef = PropertyRef(
        "class_type",
        description="Detection level: `FINDING_LEVEL` or `ASSET_LEVEL`.",
    )
    source: PropertyRef = PropertyRef(
        "source",
        description="Class origin: `SENTRA` for predefined classes or `MANUAL` for custom classes.",
    )
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description="Whether Sentra scans for this data class.",
    )
    experimental: PropertyRef = PropertyRef(
        "experimental",
        description="Whether the data class is experimental.",
    )
    is_ai: PropertyRef = PropertyRef(
        "is_ai",
        description="Whether the data class targets AI and ML data.",
    )
    sensitivity_weight: PropertyRef = PropertyRef(
        "sensitivity_weight",
        description="Sensitivity weight of the data class. Higher values mean more sensitive data.",
    )
    findings_count: PropertyRef = PropertyRef(
        "findings_count",
        description="Number of findings that Sentra detected for this data class.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Timestamp when the data class was created.",
    )


@dataclass(frozen=True)
class SentraDataClassToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SentraDataClassToTenantRel(CartographyRelSchema):
    """The Sentra organization that defines the data class."""

    target_node_label: str = "SentraTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SentraDataClassToTenantRelProperties = (
        SentraDataClassToTenantRelProperties()
    )


@dataclass(frozen=True)
class SentraDataClassSchema(CartographyNodeSchema):
    """A Sentra data class: a kind of sensitive data that Sentra classifies, such as email addresses or API keys."""

    label: str = "SentraDataClass"
    properties: SentraDataClassNodeProperties = SentraDataClassNodeProperties()
    sub_resource_relationship: SentraDataClassToTenantRel = SentraDataClassToTenantRel()
