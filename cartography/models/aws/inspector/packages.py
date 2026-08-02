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
    id: PropertyRef = PropertyRef(
        "id",
        description="Uses the format of `name|epoch:version-release.arch` to uniquely identify packages",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The package name"
    )
    version: PropertyRef = PropertyRef(
        "version", extra_index=True, description="Version of the package"
    )
    release: PropertyRef = PropertyRef(
        "release", extra_index=True, description="Release of the package"
    )
    arch: PropertyRef = PropertyRef("arch", description="Architecture for the package")
    epoch: PropertyRef = PropertyRef(
        "epoch", description="Package epoch used for version ordering."
    )
    manager: PropertyRef = PropertyRef(
        "packageManager", description="Related package manager"
    )
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
    """Representation of an AWS [Inspector Finding Package](https://docs.aws.amazon.com/inspector/v2/APIReference/API_Finding.html)"""

    label: str = "AWSInspectorPackage"
    properties: AWSInspectorPackageNodeProperties = AWSInspectorPackageNodeProperties()
    sub_resource_relationship: InspectorPackageToAWSAccountRel = (
        InspectorPackageToAWSAccountRel()
    )
