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
    id: PropertyRef = PropertyRef(
        "arn", description="Unique identifier for this `AWSRole` node."
    )
    arn: PropertyRef = PropertyRef(
        "arn",
        extra_index=True,
        description="Amazon Resource Name (ARN) of this `AWSRole` node.",
    )

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSRole` node.",
    )

    # Business fields from AWS IAM roles
    roleid: PropertyRef = PropertyRef(
        "roleid",
        extra_index=True,
        description="Identifier of the roleid linked to this `AWSRole` node.",
    )
    name: PropertyRef = PropertyRef("name", description="Name of this `AWSRole` node.")
    path: PropertyRef = PropertyRef(
        "path", description="IAM path under which the IAM role is organized."
    )
    createdate: PropertyRef = PropertyRef(
        "createdate", description="Timestamp when the IAM role was created."
    )
    createdate_dt: PropertyRef = PropertyRef(
        "createdate_dt",
        description="Creation timestamp for the IAM role normalized as a Neo4j datetime.",
    )


@dataclass(frozen=True)
class AWSRoleToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSRoleToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSRole`."

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
    "Represents an `AWSRole` node in the AWS graph."

    label: str = "AWSRole"
    properties: AWSRoleNodeProperties = AWSRoleNodeProperties()
    sub_resource_relationship: AWSRoleToAWSAccountRel = AWSRoleToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSRoleToAWSPrincipalTrustRel(),
        ]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["AWSPrincipal", "PermissionRole"]
    )
