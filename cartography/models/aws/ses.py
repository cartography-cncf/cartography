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
class SESEmailIdentityNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "Arn", description="The ARN of the SES email identity"
    )
    arn: PropertyRef = PropertyRef(
        "Arn", extra_index=True, description="The ARN of the SES email identity"
    )
    identity: PropertyRef = PropertyRef(
        "IdentityName",
        description="The name of the email identity (domain or email address)",
    )
    identity_type: PropertyRef = PropertyRef(
        "IdentityType",
        description="The type of the identity, either `EMAIL_ADDRESS` or `DOMAIN`",
    )
    sending_enabled: PropertyRef = PropertyRef(
        "SendingEnabled",
        description="Whether email sending is enabled for this identity",
    )
    verification_status: PropertyRef = PropertyRef(
        "VerificationStatus",
        description="The verification status of the identity (e.g., `SUCCESS`, `PENDING`, `FAILED`)",
    )
    dkim_signing_enabled: PropertyRef = PropertyRef(
        "DkimSigningEnabled",
        description="Whether DKIM signing is enabled for this identity",
    )
    dkim_status: PropertyRef = PropertyRef(
        "DkimStatus",
        description="The DKIM authentication status (e.g., `SUCCESS`, `PENDING`, `FAILED`)",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the SES email identity exists",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class SESEmailIdentityToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSSESEmailIdentity)<-[:RESOURCE]-(:AWSAccount)
class SESEmailIdentityToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSESEmailIdentity`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SESEmailIdentityToAWSAccountRelProperties = (
        SESEmailIdentityToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class SESEmailIdentitySchema(CartographyNodeSchema):
    "Represents an `AWSSESEmailIdentity` node in the AWS graph."

    label: str = "AWSSESEmailIdentity"
    # DEPRECATED: legacy SESEmailIdentity node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SESEmailIdentity"])
    properties: SESEmailIdentityNodeProperties = SESEmailIdentityNodeProperties()
    sub_resource_relationship: SESEmailIdentityToAWSAccountRel = (
        SESEmailIdentityToAWSAccountRel()
    )
