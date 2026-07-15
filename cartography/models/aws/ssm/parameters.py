from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SSMParameterNodeProperties(CartographyNodeProperties):

    arn: PropertyRef = PropertyRef(
        "ARN",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the parameter.",
    )
    id: PropertyRef = PropertyRef("ARN", description="The AWS parameter ARN.")
    name: PropertyRef = PropertyRef("Name", description="The parameter name.")
    value: PropertyRef = PropertyRef(
        "Value",
        description="The parameter value for AWS-managed public parameters fetched with `GetParametersByPath`. Private parameters discovered with `DescribeParameters` have no value.",
    )
    description: PropertyRef = PropertyRef(
        "Description", description="Description of the parameter actions."
    )
    type: PropertyRef = PropertyRef(
        "Type",
        description="The type of parameter. Valid parameter types include String, StringList, and SecureString.",
    )
    keyid: PropertyRef = PropertyRef(
        "KeyId",
        description="The alias or ARN of the Key Management Service (KMS) key used to encrypt the parameter. Applies to SecureString parameters only.",
    )
    kms_key_id_short: PropertyRef = PropertyRef(
        "KMSKeyIdShort",
        description="The shortened KMS Key ID used to encrypt the parameter.",
    )
    version: PropertyRef = PropertyRef("Version", description="The parameter version.")
    lastmodifieddate: PropertyRef = PropertyRef(
        "LastModifiedDate",
        description="Date the parameter was last changed or updated (stored as epoch time).",
    )
    tier: PropertyRef = PropertyRef("Tier", description="The parameter tier.")
    lastmodifieduser: PropertyRef = PropertyRef(
        "LastModifiedUser",
        description="Amazon Resource Name (ARN) of the AWS user who last changed the parameter.",
    )
    datatype: PropertyRef = PropertyRef(
        "DataType",
        description="The data type of the parameter, such as text or aws:ec2:image.",
    )
    allowedpattern: PropertyRef = PropertyRef(
        "AllowedPattern",
        description="A regular expression that defines the constraints on the parameter value.",
    )
    policies_json: PropertyRef = PropertyRef(
        "PoliciesJson",
        description="A JSON string representation of the list of policies associated with the parameter.",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the parameter."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class SSMParameterToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SSMParameterToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSSMParameter`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SSMParameterToAWSAccountRelProperties = (
        SSMParameterToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class SSMParameterToKMSKeyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SSMParameterToKMSKeyRel(CartographyRelSchema):
    "Represents a `ENCRYPTED_BY` relationship from `AWSSSMParameter` to `AWSKMSKey`."

    target_node_label: str = "AWSKMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("KMSKeyIdShort"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENCRYPTED_BY"
    properties: SSMParameterToKMSKeyRelProperties = SSMParameterToKMSKeyRelProperties()


@dataclass(frozen=True)
class SSMParameterSchema(CartographyNodeSchema):
    "Represents an `AWSSSMParameter` node in the AWS graph."

    label: str = "AWSSSMParameter"
    properties: SSMParameterNodeProperties = SSMParameterNodeProperties()
    # Only SecureString parameters are secrets (String/StringList are plaintext config).
    # DEPRECATED: legacy SSMParameter node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "SSMParameter",
            ConditionalNodeLabel(
                label="Secret",
                conditions={"type": "SecureString"},
            ),
        ],
    )
    sub_resource_relationship: SSMParameterToAWSAccountRel = (
        SSMParameterToAWSAccountRel()
    )

    other_relationships: OtherRelationships = OtherRelationships(
        [
            SSMParameterToKMSKeyRel(),
        ],
    )


@dataclass(frozen=True)
class PublicSSMParameterSchema(CartographyNodeSchema):
    "Represents an `AWSPublicSSMParameter` node in the AWS graph."

    label: str = "AWSPublicSSMParameter"
    properties: SSMParameterNodeProperties = SSMParameterNodeProperties()
    # AWS-managed public parameters are shared regional data, not account resources.
    sub_resource_relationship: None = None
    scoped_cleanup: bool = False
    # DEPRECATED: legacy PublicSSMParameter node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["PublicSSMParameter", "SSMParameter"]
    )
