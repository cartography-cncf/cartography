from dataclasses import dataclass

from cartography.models.aws.extra_labels import AWS_PRINCIPAL
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import PERMISSION_ROLE


@dataclass(frozen=True)
class AWSRoleNodeProperties(CartographyNodeProperties):
    # Required unique identifier
    id: PropertyRef = PropertyRef("arn")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Business fields from AWS IAM roles
    roleid: PropertyRef = PropertyRef("roleid", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    path: PropertyRef = PropertyRef("path")
    createdate: PropertyRef = PropertyRef("createdate")
    createdate_dt: PropertyRef = PropertyRef("createdate_dt")


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
class AWSRoleSchema(CartographyNodeSchema):
    # The TRUSTS_AWS_PRINCIPAL relationship is deliberately not declared here. It is
    # loaded as a MatchLink instead (cartography.models.aws.iam.role_trust) so that each
    # (role, principal) edge can carry its own trust-condition properties.
    label: str = "AWSRole"
    properties: AWSRoleNodeProperties = AWSRoleNodeProperties()
    sub_resource_relationship: AWSRoleToAWSAccountRel = AWSRoleToAWSAccountRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [AWS_PRINCIPAL, PERMISSION_ROLE]
    )
