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
class AWSRoleNodeProperties(CartographyNodeProperties):
    # Required unique identifier
    id: PropertyRef = PropertyRef("arn")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Business fields from AWS IAM roles
    roleid: PropertyRef = PropertyRef("roleid")
    name: PropertyRef = PropertyRef("name")
    path: PropertyRef = PropertyRef("path")
    createdate: PropertyRef = PropertyRef("createdate")


@dataclass(frozen=True)
class AWSRoleToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSRoleToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSRoleToAWSAccountRelProperties = AWSRoleToAWSAccountRelProperties()


@dataclass(frozen=True)
class AWSRoleToAWSPrincipalTrustRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSRoleToAWSPrincipalTrustRel(CartographyRelSchema):
    """
    Trust relationship with principals of type "AWS".
    """

    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "arn": PropertyRef("trusted_aws_principals", one_to_many=True),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TRUSTS_AWS_PRINCIPAL"
    properties: AWSRoleToAWSPrincipalTrustRelProperties = (
        AWSRoleToAWSPrincipalTrustRelProperties()
    )


@dataclass(frozen=True)
class AWSRoleSchema(CartographyNodeSchema):
    label: str = "AWSRole"
    properties: AWSRoleNodeProperties = AWSRoleNodeProperties()
    sub_resource_relationship: AWSRoleToAWSAccountRel = AWSRoleToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSRoleToAWSPrincipalTrustRel(),
        ]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AWSPrincipal"])
