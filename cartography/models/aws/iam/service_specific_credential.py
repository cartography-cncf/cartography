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
class AWSServiceSpecificCredentialNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "servicespecificcredentialid",
        description="The ID of the service-specific credential.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    servicename: PropertyRef = PropertyRef(
        "servicename",
        extra_index=True,
        description="The service the credential works with, such as `bedrock.amazonaws.com` or `codecommit.amazonaws.com`.",
    )
    serviceusername: PropertyRef = PropertyRef(
        "serviceusername",
        description="The user name that you sign in to the service with. Not set for Bedrock API keys.",
    )
    servicecredentialalias: PropertyRef = PropertyRef(
        "servicecredentialalias",
        description="For Bedrock API keys, the public part of the key. Not set for other services.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="The status of the credential: `Active`, `Inactive`, or `Expired`.",
    )
    createdate: PropertyRef = PropertyRef(
        "createdate",
        description="When the credential was created.",
    )
    expirationdate: PropertyRef = PropertyRef(
        "expirationdate",
        description="When the credential expires. Not set if the credential doesn't expire.",
    )


@dataclass(frozen=True)
class AWSServiceSpecificCredentialToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSServiceSpecificCredentialToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSServiceSpecificCredentialToAWSAccountRelProperties = (
        AWSServiceSpecificCredentialToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSServiceSpecificCredentialToAWSUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSServiceSpecificCredentialToAWSUserRel(CartographyRelSchema):
    target_node_label: str = "AWSUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("user_arn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "SERVICE_SPECIFIC_CREDENTIAL"
    properties: AWSServiceSpecificCredentialToAWSUserRelProperties = (
        AWSServiceSpecificCredentialToAWSUserRelProperties()
    )


@dataclass(frozen=True)
class AWSServiceSpecificCredentialSchema(CartographyNodeSchema):
    """
    Representation of an AWS IAM [service-specific credential](https://docs.aws.amazon.com/IAM/latest/APIReference/API_ServiceSpecificCredentialMetadata.html).

    These are long-lived credentials that an IAM user has for one service, such as
    Bedrock API keys, CodeCommit Git credentials, and Amazon Keyspaces passwords.
    """

    label: str = "AWSServiceSpecificCredential"
    properties: AWSServiceSpecificCredentialNodeProperties = (
        AWSServiceSpecificCredentialNodeProperties()
    )
    sub_resource_relationship: AWSServiceSpecificCredentialToAWSAccountRel = (
        AWSServiceSpecificCredentialToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [AWSServiceSpecificCredentialToAWSUserRel()],
    )
