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
class SecretsManagerSecretVersionNodeProperties(CartographyNodeProperties):
    """
    Properties for AWS Secrets Manager Secret Version
    """

    # Align property names with the actual keys in the data
    id: PropertyRef = PropertyRef("ARN", description="The ARN of the secret version.")
    arn: PropertyRef = PropertyRef(
        "ARN", extra_index=True, description="The ARN of the secret version."
    )
    secret_id: PropertyRef = PropertyRef(
        "SecretId", description="The ARN of the secret that this version belongs to."
    )
    version_id: PropertyRef = PropertyRef(
        "VersionId", description="The unique identifier of this version of the secret."
    )
    version_stages: PropertyRef = PropertyRef(
        "VersionStages",
        description="A list of staging labels that are currently attached to this version of the secret.",
    )
    created_date: PropertyRef = PropertyRef(
        "CreatedDate",
        description="The date and time that this version of the secret was created.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the secret version exists.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    # Make KMS and tags properties without required=False parameter
    kms_key_ids: PropertyRef = PropertyRef(
        "kms_key_ids",
        description="A list of IDs of the AWS KMS keys used to encrypt the secret version.",
    )
    tags: PropertyRef = PropertyRef(
        "Tags", description="A list of tags attached to this secret version."
    )


@dataclass(frozen=True)
class SecretsManagerSecretVersionRelProperties(CartographyRelProperties):
    """
    Properties for relationships between Secret Version and other nodes
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SecretsManagerSecretVersionToAWSAccountRel(CartographyRelSchema):
    """
    Relationship between Secret Version and AWS Account
    """

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SecretsManagerSecretVersionRelProperties = (
        SecretsManagerSecretVersionRelProperties()
    )


@dataclass(frozen=True)
class SecretsManagerSecretVersionToSecretRel(CartographyRelSchema):
    """
    Relationship between Secret Version and its parent Secret
    """

    target_node_label: str = "AWSSecretsManagerSecret"
    # Use only one matcher for the id field
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SecretId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "VERSION_OF"
    properties: SecretsManagerSecretVersionRelProperties = (
        SecretsManagerSecretVersionRelProperties()
    )


@dataclass(frozen=True)
class SecretsManagerSecretVersionToKMSKeyRel(CartographyRelSchema):
    """
    Relationship between Secret Version and its KMS key
    Only created when kms_key_ids is present
    """

    target_node_label: str = "AWSKMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("kms_key_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENCRYPTED_BY"
    properties: SecretsManagerSecretVersionRelProperties = (
        SecretsManagerSecretVersionRelProperties()
    )


@dataclass(frozen=True)
class SecretsManagerSecretVersionSchema(CartographyNodeSchema):
    """
    Schema for AWS Secrets Manager Secret Version
    """

    label: str = "AWSSecretsManagerSecretVersion"
    # DEPRECATED: legacy SecretsManagerSecretVersion node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["SecretsManagerSecretVersion"]
    )
    properties: SecretsManagerSecretVersionNodeProperties = (
        SecretsManagerSecretVersionNodeProperties()
    )
    sub_resource_relationship: SecretsManagerSecretVersionToAWSAccountRel = (
        SecretsManagerSecretVersionToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SecretsManagerSecretVersionToSecretRel(),
            SecretsManagerSecretVersionToKMSKeyRel(),
        ],
    )
