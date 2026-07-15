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
class AWSSSOGroupProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "GroupId", description="Unique identifier for the SSO group"
    )
    display_name: PropertyRef = PropertyRef(
        "DisplayName", description="The display name of the SSO group"
    )
    description: PropertyRef = PropertyRef(
        "Description", description="The description of the SSO group"
    )
    identity_store_id: PropertyRef = PropertyRef(
        "IdentityStoreId", description="The identity store ID of the SSO group"
    )
    external_id: PropertyRef = PropertyRef(
        "ExternalId", extra_index=True, description="The external ID of the SSO group"
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The AWS region"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSSSOGroupToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSOGroupToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSSOGroup`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSSOGroupToAWSAccountRelProperties = (
        AWSSSOGroupToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSSSOGroupToPermissionSetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:UserGroup)-[:HAS_ROLE]->(:PermissionRole)
# edge (AWSSSOGroupToPermissionSetHasRoleRel). Kept for backward compatibility,
# will be removed in v1.0.0.
class AWSSSOGroupToPermissionSetRel(CartographyRelSchema):
    "Represents a `HAS_PERMISSION_SET` relationship from `AWSSSOGroup` to `AWSPermissionSet`."

    target_node_label: str = "AWSPermissionSet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("AssignedPermissionSets", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION_SET"
    properties: AWSSSOGroupToPermissionSetRelProperties = (
        AWSSSOGroupToPermissionSetRelProperties()
    )


@dataclass(frozen=True)
class AWSSSOGroupToPermissionSetHasRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:UserGroup)-[:HAS_ROLE]->(:PermissionRole)
class AWSSSOGroupToPermissionSetHasRoleRel(CartographyRelSchema):
    "Represents a `HAS_ROLE` relationship from `AWSSSOGroup` to `AWSPermissionSet`."

    target_node_label: str = "AWSPermissionSet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("AssignedPermissionSets", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: AWSSSOGroupToPermissionSetHasRoleRelProperties = (
        AWSSSOGroupToPermissionSetHasRoleRelProperties()
    )


@dataclass(frozen=True)
class AWSSSOGroupSchema(CartographyNodeSchema):
    "Represents an `AWSSSOGroup` node in the AWS graph."

    label: str = "AWSSSOGroup"
    properties: AWSSSOGroupProperties = AWSSSOGroupProperties()
    sub_resource_relationship: AWSSSOGroupToAWSAccountRel = AWSSSOGroupToAWSAccountRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserGroup"])
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSSSOGroupToPermissionSetRel(),
            AWSSSOGroupToPermissionSetHasRoleRel(),
        ]
    )
