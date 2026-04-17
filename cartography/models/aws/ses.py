from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SESEmailIdentityNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Arn")
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    identity: PropertyRef = PropertyRef("IdentityName")
    identity_type: PropertyRef = PropertyRef("IdentityType")
    sending_enabled: PropertyRef = PropertyRef("SendingEnabled")
    verification_status: PropertyRef = PropertyRef("VerificationStatus")
    dkim_signing_enabled: PropertyRef = PropertyRef("DkimSigningEnabled")
    dkim_status: PropertyRef = PropertyRef("DkimStatus")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SESEmailIdentityToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SESEmailIdentity)<-[:RESOURCE]-(:AWSAccount)
class SESEmailIdentityToAWSAccountRel(CartographyRelSchema):
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
    label: str = "SESEmailIdentity"
    properties: SESEmailIdentityNodeProperties = SESEmailIdentityNodeProperties()
    sub_resource_relationship: SESEmailIdentityToAWSAccountRel = (
        SESEmailIdentityToAWSAccountRel()
    )
