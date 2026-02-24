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
class GCPCloudArmorPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("partial_uri")
    partial_uri: PropertyRef = PropertyRef("partial_uri")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    self_link: PropertyRef = PropertyRef("self_link")
    project_id: PropertyRef = PropertyRef("project_id")
    description: PropertyRef = PropertyRef("description")
    policy_type: PropertyRef = PropertyRef("policy_type")
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")


@dataclass(frozen=True)
class GCPCloudArmorPolicyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPCloudArmorPolicyToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPCloudArmorPolicyToProjectRelProperties = (
        GCPCloudArmorPolicyToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudArmorPolicySchema(CartographyNodeSchema):
    label: str = "GCPCloudArmorPolicy"
    properties: GCPCloudArmorPolicyNodeProperties = GCPCloudArmorPolicyNodeProperties()
    sub_resource_relationship: GCPCloudArmorPolicyToProjectRel = (
        GCPCloudArmorPolicyToProjectRel()
    )
