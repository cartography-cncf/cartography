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
class DatabricksEncryptionKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Account-scoped Databricks customer-managed key ID.",
    )
    customer_managed_key_id: PropertyRef = PropertyRef(
        "customer_managed_key_id",
        extra_index=True,
        description="Databricks customer-managed key ID.",
    )
    use_cases: PropertyRef = PropertyRef(
        "use_cases",
        description="Databricks use cases protected by the key.",
    )
    aws_key_arn: PropertyRef = PropertyRef(
        "aws_key_arn",
        extra_index=True,
        description="ARN of the AWS KMS key.",
    )
    aws_key_alias: PropertyRef = PropertyRef(
        "aws_key_alias",
        description="Alias of the AWS KMS key.",
    )
    gcp_kms_key_name: PropertyRef = PropertyRef(
        "gcp_kms_key_name",
        extra_index=True,
        description="Full resource name of the Google Cloud KMS key.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksEncryptionKeyToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksEncryptionKey)
class DatabricksEncryptionKeyToAccountRel(CartographyRelSchema):
    """A Databricks account owns an account-level resource."""

    target_node_label: str = "DatabricksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksEncryptionKeyToAccountRelProperties = (
        DatabricksEncryptionKeyToAccountRelProperties()
    )


@dataclass(frozen=True)
class DatabricksEncryptionKeyToKMSKeyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksEncryptionKey)-[:REFERENCES_KEY]->(:AWSKMSKey)
class DatabricksEncryptionKeyToKMSKeyRel(CartographyRelSchema):
    """A Databricks encryption key references an AWS KMS key."""

    target_node_label: str = "AWSKMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("aws_key_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REFERENCES_KEY"
    properties: DatabricksEncryptionKeyToKMSKeyRelProperties = (
        DatabricksEncryptionKeyToKMSKeyRelProperties()
    )


@dataclass(frozen=True)
class DatabricksEncryptionKeyToGCPCryptoKeyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksEncryptionKey)-[:REFERENCES_KEY]->(:GCPCryptoKey)
class DatabricksEncryptionKeyToGCPCryptoKeyRel(CartographyRelSchema):
    """A Databricks encryption key references a Google Cloud KMS key."""

    target_node_label: str = "GCPCryptoKey"
    # GCPCryptoKey.id is the full KMS resource name (projects/.../cryptoKeys/...),
    # which is what Databricks reports in gcp_key_info.kms_key_id; the node's
    # `name` is only the short trailing segment, so match on id.
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gcp_kms_key_name")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REFERENCES_KEY"
    properties: DatabricksEncryptionKeyToGCPCryptoKeyRelProperties = (
        DatabricksEncryptionKeyToGCPCryptoKeyRelProperties()
    )


@dataclass(frozen=True)
class DatabricksEncryptionKeySchema(CartographyNodeSchema):
    """A Databricks account customer-managed encryption key."""

    label: str = "DatabricksEncryptionKey"
    properties: DatabricksEncryptionKeyNodeProperties = (
        DatabricksEncryptionKeyNodeProperties()
    )
    sub_resource_relationship: DatabricksEncryptionKeyToAccountRel = (
        DatabricksEncryptionKeyToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatabricksEncryptionKeyToKMSKeyRel(),
            DatabricksEncryptionKeyToGCPCryptoKeyRel(),
        ],
    )
