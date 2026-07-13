from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SalesforceGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    name: PropertyRef = PropertyRef("Name")
    developer_name: PropertyRef = PropertyRef("DeveloperName", extra_index=True)
    type: PropertyRef = PropertyRef("Type")
    related_id: PropertyRef = PropertyRef("RelatedId")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SalesforceGroupToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SalesforceGroup)<-[:RESOURCE]-(:SalesforceOrganization)
class SalesforceGroupToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "SalesforceOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SalesforceGroupToOrganizationRelProperties = (
        SalesforceGroupToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class SalesforceGroupToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SalesforceGroup)<-[:MEMBER_OF]-(:SalesforceUser)
class SalesforceGroupToUserRel(CartographyRelSchema):
    target_node_label: str = "SalesforceUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_member_user_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: SalesforceGroupToUserRelProperties = (
        SalesforceGroupToUserRelProperties()
    )


@dataclass(frozen=True)
class SalesforceGroupToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Nested group membership: (:SalesforceGroup)<-[:MEMBER_OF]-(:SalesforceGroup)
class SalesforceGroupToGroupRel(CartographyRelSchema):
    target_node_label: str = "SalesforceGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_member_group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: SalesforceGroupToGroupRelProperties = (
        SalesforceGroupToGroupRelProperties()
    )


@dataclass(frozen=True)
class SalesforceGroupSchema(CartographyNodeSchema):
    label: str = "SalesforceGroup"
    # UserGroup label is used for ontology mapping
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserGroup"])
    properties: SalesforceGroupNodeProperties = SalesforceGroupNodeProperties()
    sub_resource_relationship: SalesforceGroupToOrganizationRel = (
        SalesforceGroupToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SalesforceGroupToUserRel(),
            SalesforceGroupToGroupRel(),
        ]
    )
