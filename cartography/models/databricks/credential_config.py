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
class DatabricksCredentialConfigNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Account-scoped Databricks credential configuration ID.",
    )
    credentials_id: PropertyRef = PropertyRef(
        "credentials_id",
        extra_index=True,
        description="Databricks credential configuration ID.",
    )
    credentials_name: PropertyRef = PropertyRef(
        "credentials_name",
        extra_index=True,
        description="Credential configuration name.",
    )
    aws_role_arn: PropertyRef = PropertyRef(
        "aws_role_arn",
        extra_index=True,
        description="ARN of the cross-account AWS IAM role.",
    )
    aws_account_id: PropertyRef = PropertyRef(
        "aws_account_id",
        extra_index=True,
        description="ID of the AWS account that owns the IAM role.",
    )
    created_time: PropertyRef = PropertyRef(
        "created_time",
        description="Timestamp when the credential configuration was created.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksCredentialConfigToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksCredentialConfig)
class DatabricksCredentialConfigToAccountRel(CartographyRelSchema):
    """A Databricks account owns an account-level resource."""

    target_node_label: str = "DatabricksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksCredentialConfigToAccountRelProperties = (
        DatabricksCredentialConfigToAccountRelProperties()
    )


@dataclass(frozen=True)
class DatabricksCredentialConfigToAWSPrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksCredentialConfig)-[:ASSUMES_ROLE]->(:AWSPrincipal)
class DatabricksCredentialConfigToAWSPrincipalRel(CartographyRelSchema):
    """A Databricks credential configuration assumes an AWS IAM role."""

    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("aws_role_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMES_ROLE"
    properties: DatabricksCredentialConfigToAWSPrincipalRelProperties = (
        DatabricksCredentialConfigToAWSPrincipalRelProperties()
    )


@dataclass(frozen=True)
class DatabricksCredentialConfigToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksCredentialConfig)-[:IN_ACCOUNT]->(:AWSAccount)
class DatabricksCredentialConfigToAWSAccountRel(CartographyRelSchema):
    """A Databricks credential configuration uses a role in an AWS account."""

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("aws_account_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN_ACCOUNT"
    properties: DatabricksCredentialConfigToAWSAccountRelProperties = (
        DatabricksCredentialConfigToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class DatabricksCredentialConfigSchema(CartographyNodeSchema):
    """A Databricks account credential configuration for an AWS IAM role."""

    label: str = "DatabricksCredentialConfig"
    properties: DatabricksCredentialConfigNodeProperties = (
        DatabricksCredentialConfigNodeProperties()
    )
    sub_resource_relationship: DatabricksCredentialConfigToAccountRel = (
        DatabricksCredentialConfigToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatabricksCredentialConfigToAWSPrincipalRel(),
            DatabricksCredentialConfigToAWSAccountRel(),
        ],
    )
