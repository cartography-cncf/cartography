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
from cartography.models.sysdig.common import SysdigNodeToTenantRel


@dataclass(frozen=True)
class SysdigPackageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    normalized_id: PropertyRef = PropertyRef("normalized_id", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    version: PropertyRef = PropertyRef("version")
    type: PropertyRef = PropertyRef("type")
    purl: PropertyRef = PropertyRef("purl")
    image_digest: PropertyRef = PropertyRef("image_digest", extra_index=True)


@dataclass(frozen=True)
class SysdigPackageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SysdigPackageToOntologyImageRel(CartographyRelSchema):
    target_node_label: str = "Image"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"_ont_digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED"
    properties: SysdigPackageRelProperties = SysdigPackageRelProperties()


@dataclass(frozen=True)
class SysdigPackageSchema(CartographyNodeSchema):
    label: str = "SysdigPackage"
    properties: SysdigPackageNodeProperties = SysdigPackageNodeProperties()
    sub_resource_relationship: CartographyRelSchema = SysdigNodeToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SysdigPackageToOntologyImageRel(),
        ],
    )
