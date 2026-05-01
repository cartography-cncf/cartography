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
class GCPServiceAccountKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    key_type: PropertyRef = PropertyRef("keyType")
    key_origin: PropertyRef = PropertyRef("keyOrigin")
    key_algorithm: PropertyRef = PropertyRef("keyAlgorithm")
    valid_after_time: PropertyRef = PropertyRef("validAfterTime")
    valid_before_time: PropertyRef = PropertyRef("validBeforeTime")
    disabled: PropertyRef = PropertyRef("disabled")
    service_account_email: PropertyRef = PropertyRef("serviceAccountEmail")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPServiceAccountKeyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPServiceAccountKeyToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("projectId", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPServiceAccountKeyToProjectRelProperties = (
        GCPServiceAccountKeyToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPServiceAccountKeyToServiceAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPServiceAccountKeyToServiceAccountRel(CartographyRelSchema):
    target_node_label: str = "GCPServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("serviceAccountEmail")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_KEY"
    properties: GCPServiceAccountKeyToServiceAccountRelProperties = (
        GCPServiceAccountKeyToServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class GCPServiceAccountKeySchema(CartographyNodeSchema):
    label: str = "GCPServiceAccountKey"
    properties: GCPServiceAccountKeyNodeProperties = (
        GCPServiceAccountKeyNodeProperties()
    )
    sub_resource_relationship: GCPServiceAccountKeyToProjectRel = (
        GCPServiceAccountKeyToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPServiceAccountKeyToServiceAccountRel(),
        ],
    )
