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
class AWSInspectorPackageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    version: PropertyRef = PropertyRef("version", extra_index=True)
    release: PropertyRef = PropertyRef("release", extra_index=True)
    arch: PropertyRef = PropertyRef("arch")
    epoch: PropertyRef = PropertyRef("epoch")
    manager: PropertyRef = PropertyRef("packageManager")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorPackageToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorPackageToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: InspectorPackageToAWSAccountRelRelProperties = (
        InspectorPackageToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class AWSInspectorPackageSchema(CartographyNodeSchema):
    label: str = "AWSInspectorPackage"
    properties: AWSInspectorPackageNodeProperties = AWSInspectorPackageNodeProperties()
    sub_resource_relationship: InspectorPackageToAWSAccountRel = (
        InspectorPackageToAWSAccountRel()
    )
