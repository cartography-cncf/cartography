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
    id: PropertyRef = PropertyRef("id", description="Entra group ID.")
    display_name: PropertyRef = PropertyRef(
        "display_name", description="Display name of the group."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the group."
    )
    mail: PropertyRef = PropertyRef(
        "mail", description="Primary email address of the group."
    )
    mail_nickname: PropertyRef = PropertyRef(
        "mail_nickname", description="Mail alias of the group."
    )
    mail_enabled: PropertyRef = PropertyRef(
        "mail_enabled", description="Whether the group has mail enabled."
    )
    security_enabled: PropertyRef = PropertyRef(
        "security_enabled", description="Whether the group has security enabled."
    )
    group_types: PropertyRef = PropertyRef(
        "group_types", description="Microsoft Graph group type values."
    )
    visibility: PropertyRef = PropertyRef(
        "visibility", description="Visibility setting of the group."
    )
    is_assignable_to_role: PropertyRef = PropertyRef(
        "is_assignable_to_role",
        description="Whether directory roles can be assigned to the group.",
    )
    created_date_time: PropertyRef = PropertyRef(
        "created_date_time", description="Timestamp when the group was created."
    )
    deleted_date_time: PropertyRef = PropertyRef(
        "deleted_date_time", description="Timestamp when the group was deleted."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the latest Cartography update.",
    )


@dataclass(frozen=True)
class EntraGroupToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraGroupToTenantRel(CartographyRelSchema):
    """Links a Microsoft tenant to one of its Entra groups."""

    target_node_label: str = "AzureTenant"
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
    """Links Entra users to a group they belong to."""

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
    """Links nested Entra groups to their parent group."""

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
    """Links Entra identities to a group they own."""

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
    """A group in Microsoft Entra ID."""

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
            "UserGroup",
        ]
    )
