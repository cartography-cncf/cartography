from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_ACCOUNT_ACCESS_KEY
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
from cartography.models.ontology.labels import API_KEY


@dataclass(frozen=True)
class AccountAccessKeyNodeProperties(CartographyNodeProperties):
    # Required unique identifier
    id: PropertyRef = PropertyRef(
        "accesskeyid", description="The access key ID (same as accesskeyid)"
    )
    accesskeyid: PropertyRef = PropertyRef(
        "accesskeyid", extra_index=True, description="The ID for this access key"
    )

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Business fields from AWS IAM access keys
    createdate: PropertyRef = PropertyRef(
        "createdate", description="Date when access key was created"
    )
    createdate_dt: PropertyRef = PropertyRef(
        "createdate_dt",
        description="Access-key creation timestamp normalized as a Neo4j datetime.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Active: valid for API calls.  Inactive: not valid for API calls",
    )
    lastuseddate: PropertyRef = PropertyRef(
        "lastuseddate", description="Date when the key was last used"
    )
    lastuseddate_dt: PropertyRef = PropertyRef(
        "lastuseddate_dt",
        description="Most recent access-key use timestamp normalized as a Neo4j datetime.",
    )
    lastusedservice: PropertyRef = PropertyRef(
        "lastusedservice",
        description="The service that was last used with the access key",
    )
    lastusedregion: PropertyRef = PropertyRef(
        "lastusedregion", description="The region where the access key was last used"
    )


@dataclass(frozen=True)
class AccountAccessKeyToAWSUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:APIKey)-[:OWNED_BY]->(:UserAccount)
# edge (AccountAccessKeyToAWSUserOwnedByRel). Kept for backward compatibility,
# will be removed in v1.0.0.
# (:AWSUser)-[:AWS_ACCESS_KEY]->(:AWSAccountAccessKey)
class AccountAccessKeyToAWSUserRel(CartographyRelSchema):
    target_node_label: str = "AWSUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "arn": PropertyRef("user_arn"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "AWS_ACCESS_KEY"
    properties: AccountAccessKeyToAWSUserRelProperties = (
        AccountAccessKeyToAWSUserRelProperties()
    )


@dataclass(frozen=True)
class AccountAccessKeyToAWSUserOwnedByRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:APIKey)-[:OWNED_BY]->(:UserAccount)
class AccountAccessKeyToAWSUserOwnedByRel(CartographyRelSchema):
    target_node_label: str = "AWSUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "arn": PropertyRef("user_arn"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: AccountAccessKeyToAWSUserOwnedByRelProperties = (
        AccountAccessKeyToAWSUserOwnedByRelProperties()
    )


@dataclass(frozen=True)
class AccountAccessKeyToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AccountAccessKeyToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AccountAccessKeyToAWSAccountRelProperties = (
        AccountAccessKeyToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AccountAccessKeySchema(CartographyNodeSchema):
    """Representation of an AWS [Access Key](https://docs.aws.amazon.com/IAM/latest/APIReference/API_AccessKey.html)."""

    label: str = "AWSAccountAccessKey"
    # DEPRECATED: legacy AccountAccessKey node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [LEGACY_ACCOUNT_ACCESS_KEY, API_KEY]
    )
    properties: AccountAccessKeyNodeProperties = AccountAccessKeyNodeProperties()
    sub_resource_relationship: AccountAccessKeyToAWSAccountRel = (
        AccountAccessKeyToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AccountAccessKeyToAWSUserRel(),
            AccountAccessKeyToAWSUserOwnedByRel(),
        ]
    )
