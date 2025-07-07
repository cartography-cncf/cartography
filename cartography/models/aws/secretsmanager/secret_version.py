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
class SecretsManagerSecretVersionNodeProperties(CartographyNodeProperties):
    """
    Properties for AWS Secrets Manager Secret Version
    """

    # Align property names with the actual keys in the data
    id: PropertyRef = PropertyRef("ARN")
    arn: PropertyRef = PropertyRef("ARN", extra_index=True)
    secret_id: PropertyRef = PropertyRef("SecretId")
    version_id: PropertyRef = PropertyRef("VersionId")
    version_stages: PropertyRef = PropertyRef("VersionStages")
    created_date: PropertyRef = PropertyRef("CreatedDate")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # Make KMS and tags properties without required=False parameter
    kms_key_id: PropertyRef = PropertyRef("KmsKeyId")
    tags: PropertyRef = PropertyRef("Tags")


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

    target_node_label: str = "SecretsManagerSecret"
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
    Only created when KmsKeyId is present
    """

    target_node_label: str = "AWSKMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("KmsKeyId")},
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

    label: str = "SecretsManagerSecretVersion"
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
