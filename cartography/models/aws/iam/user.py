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
    id: PropertyRef = PropertyRef(
        "arn", description="Unique identifier for this `AWSUser` node."
    )
    arn: PropertyRef = PropertyRef(
        "arn",
        extra_index=True,
        description="Amazon Resource Name (ARN) of this `AWSUser` node.",
    )

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSUser` node.",
    )

    # Business fields from AWS IAM users
    userid: PropertyRef = PropertyRef(
        "userid",
        extra_index=True,
        description="Identifier of the user linked to this `AWSUser` node.",
    )
    name: PropertyRef = PropertyRef("name", description="Name of this `AWSUser` node.")
    path: PropertyRef = PropertyRef(
        "path", description="IAM path under which the IAM user is organized."
    )
    createdate: PropertyRef = PropertyRef(
        "createdate", description="Timestamp when the IAM user was created."
    )
    createdate_dt: PropertyRef = PropertyRef(
        "createdate_dt",
        description="Creation timestamp for the IAM user normalized as a Neo4j datetime.",
    )
    passwordlastused: PropertyRef = PropertyRef(
        "passwordlastused",
        description="Timestamp when the IAM user's password was last used.",
    )
    passwordlastused_dt: PropertyRef = PropertyRef(
        "passwordlastused_dt",
        description="Last password-use timestamp normalized as a Neo4j datetime.",
    )


@dataclass(frozen=True)
class AWSUserToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSUserToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSUser`."

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
    "Represents an `AWSUser` node in the AWS graph."

    label: str = "AWSUser"
    properties: AWSUserNodeProperties = AWSUserNodeProperties()
    sub_resource_relationship: AWSUserToAWSAccountRel = AWSUserToAWSAccountRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "AWSPrincipal",
            "UserAccount",
        ]  # UserAccount label is used for ontology mapping
    )
