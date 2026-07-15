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
class KMSGrantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "GrantId", description="The unique identifier of the key grant"
    )
    grant_id: PropertyRef = PropertyRef(
        "GrantId",
        extra_index=True,
        description="The grant identifier (indexed for performance)",
    )
    name: PropertyRef = PropertyRef("Name", description="The name of the key grant")
    grantee_principal: PropertyRef = PropertyRef(
        "GranteePrincipal", description="The principal associated with the key grant"
    )
    creation_date: PropertyRef = PropertyRef(
        "CreationDate", description="Epoch timestamp when the grant was created"
    )
    key_id: PropertyRef = PropertyRef(
        "KeyId", description="The key identifier that the grant applies to"
    )
    issuing_account: PropertyRef = PropertyRef(
        "IssuingAccount", description="The AWS account that issued the grant"
    )
    operations: PropertyRef = PropertyRef(
        "Operations", description="List of operations that the grant allows"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of when the node was last updated by Cartography",
    )


@dataclass(frozen=True)
class KMSGrantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KMSGrantToKMSKeyRel(CartographyRelSchema):
    "Represents a `APPLIED_ON` relationship from `AWSKMSGrant` to `AWSKMSKey`."

    target_node_label: str = "AWSKMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("KeyId")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIED_ON"
    properties: KMSGrantRelProperties = KMSGrantRelProperties()


@dataclass(frozen=True)
class KMSGrantToAWSAccountRel(CartographyRelSchema):
    """
    Relationship between AWSKMSGrant and AWS Account
    """

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KMSGrantRelProperties = KMSGrantRelProperties()


@dataclass(frozen=True)
class KMSGrantSchema(CartographyNodeSchema):
    "Represents an `AWSKMSGrant` node in the AWS graph."

    label: str = "AWSKMSGrant"
    # DEPRECATED: legacy KMSGrant node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["KMSGrant"])
    properties: KMSGrantNodeProperties = KMSGrantNodeProperties()
    sub_resource_relationship: KMSGrantToAWSAccountRel = KMSGrantToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [KMSGrantToKMSKeyRel()]
    )
