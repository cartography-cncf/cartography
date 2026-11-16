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
class SweetAWSAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Sweet tenant ID and AWS account ID joined with `:`.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Sweet AWS account connection was last synced.",
    )
    account_id: PropertyRef = PropertyRef(
        "account_id",
        extra_index=True,
        description="AWS account ID that is connected to Sweet.",
    )
    role_arn: PropertyRef = PropertyRef(
        "role_arn",
        extra_index=True,
        description="ARN of the cross-account IAM role that Sweet assumes in the account.",
    )
    regions: PropertyRef = PropertyRef(
        "regions",
        description="AWS regions that Sweet monitors in the account.",
    )
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description="Whether the connection is enabled in Sweet.",
    )


@dataclass(frozen=True)
class SweetAWSOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Sweet tenant ID and management account ID joined with `:`.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Sweet AWS organization connection was last synced.",
    )
    management_account_id: PropertyRef = PropertyRef(
        "management_account_id",
        extra_index=True,
        description="AWS account ID of the organization's management account.",
    )
    role_arn: PropertyRef = PropertyRef(
        "role_arn",
        extra_index=True,
        description="ARN of the cross-account IAM role that Sweet assumes in the management account.",
    )
    regions: PropertyRef = PropertyRef(
        "regions",
        description="AWS regions that Sweet monitors across the organization.",
    )
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description="Whether the connection is enabled in Sweet.",
    )


@dataclass(frozen=True)
class SweetAWSConnectionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SweetTenantToAWSAccountRel(CartographyRelSchema):
    """Links a Sweet tenant to an AWS account connection it owns."""

    target_node_label: str = "SweetTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SWEET_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SweetAWSConnectionRelProperties = SweetAWSConnectionRelProperties()


@dataclass(frozen=True)
class SweetAWSAccountToAWSAccountRel(CartographyRelSchema):
    """Links a Sweet AWS account connection to the AWS account it monitors."""

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MONITORS"
    properties: SweetAWSConnectionRelProperties = SweetAWSConnectionRelProperties()


@dataclass(frozen=True)
class SweetAWSAccountSchema(CartographyNodeSchema):
    """An AWS account that is connected to Sweet on its own, outside an organization connection."""

    label: str = "SweetAWSAccount"
    properties: SweetAWSAccountNodeProperties = SweetAWSAccountNodeProperties()
    sub_resource_relationship: SweetTenantToAWSAccountRel = SweetTenantToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [SweetAWSAccountToAWSAccountRel()],
    )


@dataclass(frozen=True)
class SweetTenantToAWSOrganizationRel(CartographyRelSchema):
    """Links a Sweet tenant to an AWS organization connection it owns."""

    target_node_label: str = "SweetTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SWEET_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SweetAWSConnectionRelProperties = SweetAWSConnectionRelProperties()


@dataclass(frozen=True)
class SweetAWSOrganizationToManagementAccountRel(CartographyRelSchema):
    """Links a Sweet AWS organization connection to the organization's management account."""

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("management_account_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MONITORS"
    properties: SweetAWSConnectionRelProperties = SweetAWSConnectionRelProperties()


@dataclass(frozen=True)
class SweetAWSOrganizationSchema(CartographyNodeSchema):
    """An AWS organization that is connected to Sweet through its management account."""

    label: str = "SweetAWSOrganization"
    properties: SweetAWSOrganizationNodeProperties = (
        SweetAWSOrganizationNodeProperties()
    )
    sub_resource_relationship: SweetTenantToAWSOrganizationRel = (
        SweetTenantToAWSOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SweetAWSOrganizationToManagementAccountRel()],
    )
