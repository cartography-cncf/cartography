from dataclasses import dataclass

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
class CrowdstrikeApplicationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="CrowdStrike customer ID and the application's package URL, joined by `|`.",
    )
    normalized_id: PropertyRef = PropertyRef(
        "normalized_id",
        extra_index=True,
        description=(
            "Normalized package ID, `generic|{vendor/}{name}|{version}`, shared with "
            "PackageVersion. Unset when Spotlight reports no separate version."
        ),
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Normalized product name Spotlight reports, such as `.Net Framework`.",
    )
    vendor: PropertyRef = PropertyRef(
        "vendor",
        description="Normalized vendor name Spotlight reports, such as `Microsoft`.",
    )
    version: PropertyRef = PropertyRef(
        "version",
        description="Version that follows the product name in `product_name_version`.",
    )
    product_name_version: PropertyRef = PropertyRef(
        "product_name_version",
        description="Product name and version as Spotlight reports them together.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Package type. Always `generic`, because Spotlight reports no ecosystem.",
    )
    purl: PropertyRef = PropertyRef(
        "purl",
        description="Generic package URL built from the vendor, product name, and version.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CrowdstrikeApplicationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CrowdstrikeApplicationToTenantRel(CartographyRelSchema):
    """The CrowdStrike tenant contains this application as a managed resource."""

    target_node_label: str = "CrowdstrikeTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CrowdstrikeApplicationRelProperties = (
        CrowdstrikeApplicationRelProperties()
    )


@dataclass(frozen=True)
class CrowdstrikeApplicationToHostRel(CartographyRelSchema):
    """A host where Spotlight found this application with an open vulnerability."""

    target_node_label: str = "CrowdstrikeHost"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("host_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED"
    properties: CrowdstrikeApplicationRelProperties = (
        CrowdstrikeApplicationRelProperties()
    )


@dataclass(frozen=True)
class CrowdstrikeApplicationToCVERel(CartographyRelSchema):
    """A CVE that Spotlight reports as open on this application."""

    target_node_label: str = "CrowdstrikeFinding"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cve_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "AFFECTS"
    properties: CrowdstrikeApplicationRelProperties = (
        CrowdstrikeApplicationRelProperties()
    )


@dataclass(frozen=True)
class CrowdstrikeApplicationSchema(CartographyNodeSchema):
    """An application version that Spotlight reports with open vulnerabilities."""

    label: str = "CrowdstrikeApplication"
    properties: CrowdstrikeApplicationNodeProperties = (
        CrowdstrikeApplicationNodeProperties()
    )
    sub_resource_relationship: CrowdstrikeApplicationToTenantRel = (
        CrowdstrikeApplicationToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CrowdstrikeApplicationToHostRel(),
            CrowdstrikeApplicationToCVERel(),
        ],
    )
