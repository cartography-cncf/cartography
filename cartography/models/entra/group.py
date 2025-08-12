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
class EntraGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    display_name: PropertyRef = PropertyRef("display_name")
    description: PropertyRef = PropertyRef("description")
    mail: PropertyRef = PropertyRef("mail")
    mail_nickname: PropertyRef = PropertyRef("mail_nickname")
    mail_enabled: PropertyRef = PropertyRef("mail_enabled")
    security_enabled: PropertyRef = PropertyRef("security_enabled")
    group_types: PropertyRef = PropertyRef("group_types")
    visibility: PropertyRef = PropertyRef("visibility")
    is_assignable_to_role: PropertyRef = PropertyRef("is_assignable_to_role")
    created_date_time: PropertyRef = PropertyRef("created_date_time")
    deleted_date_time: PropertyRef = PropertyRef("deleted_date_time")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraGroupToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraGroupToTenantRel(CartographyRelSchema):
    target_node_label: str = "EntraTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EntraGroupToTenantRelProperties = EntraGroupToTenantRelProperties()


@dataclass(frozen=True)
class EntraGroupToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EntraUser)-[:MEMBER_OF]->(:EntraGroup)
class EntraGroupToUserRel(CartographyRelSchema):
    target_node_label: str = "EntraUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("member_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: EntraGroupToUserRelProperties = EntraGroupToUserRelProperties()


@dataclass(frozen=True)
class EntraGroupToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EntraGroup)-[:MEMBER_OF]->(:EntraGroup)
class EntraGroupToGroupRel(CartographyRelSchema):
    target_node_label: str = "EntraGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("member_group_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: EntraGroupToGroupRelProperties = EntraGroupToGroupRelProperties()


@dataclass(frozen=True)
class EntraGroupToOwnerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EntraGroup)<-[:OWNER_OF]-(:EntraUser)
class EntraGroupToOwnerRel(CartographyRelSchema):
    # EntraUsers and Entra service principals can be owners of a group, so we match on the general label
    # Because id is indexed, this should be fast even though EntraIdentity will also include EntraGroups
    target_node_label: str = "EntraIdentity"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNER_OF"
    properties: EntraGroupToOwnerRelProperties = EntraGroupToOwnerRelProperties()


@dataclass(frozen=True)
class EntraGroupSchema(CartographyNodeSchema):
    label: str = "EntraGroup"
    properties: EntraGroupNodeProperties = EntraGroupNodeProperties()
    sub_resource_relationship: EntraGroupToTenantRel = EntraGroupToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EntraGroupToGroupRel(),
            EntraGroupToUserRel(),
            EntraGroupToOwnerRel(),
        ]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "EntraIdentity",
        ]
    )
