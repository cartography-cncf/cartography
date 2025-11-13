from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AWSUserNodeProperties(CartographyNodeProperties):
    # Required unique identifier
    id: PropertyRef = PropertyRef("arn")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Business fields from AWS IAM users
    userid: PropertyRef = PropertyRef("userid")
    name: PropertyRef = PropertyRef("name")
    path: PropertyRef = PropertyRef("path")
    createdate: PropertyRef = PropertyRef("createdate")
    passwordlastused: PropertyRef = PropertyRef("passwordlastused")


@dataclass(frozen=True)
class AWSUserToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSUserToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSUserToAWSAccountRelProperties = AWSUserToAWSAccountRelProperties()


@dataclass(frozen=True)
class AWSUserSchema(CartographyNodeSchema):
    label: str = "AWSUser"
    properties: AWSUserNodeProperties = AWSUserNodeProperties()
    sub_resource_relationship: AWSUserToAWSAccountRel = AWSUserToAWSAccountRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "AWSPrincipal",
            "UserAccount",
        ]  # UserAccount label is used for ontology mapping
    )
