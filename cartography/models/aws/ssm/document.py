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
class SSMDocumentNodeProperties(CartographyNodeProperties):

    arn: PropertyRef = PropertyRef(
        "Arn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the document.",
    )
    id: PropertyRef = PropertyRef("Arn", description="The AWS document ARN.")
    name: PropertyRef = PropertyRef("Name", description="The document name.")
    document_type: PropertyRef = PropertyRef(
        "DocumentType",
        description="The document type, such as Command, Automation, or Session.",
    )
    document_format: PropertyRef = PropertyRef(
        "DocumentFormat",
        description="The document format: JSON, YAML, or TEXT.",
    )
    owner: PropertyRef = PropertyRef(
        "Owner",
        description="The AWS account that owns the document.",
    )
    platform_types: PropertyRef = PropertyRef(
        "PlatformTypes",
        description="Operating system platforms the document supports.",
    )
    created_date: PropertyRef = PropertyRef(
        "CreatedDate",
        description="Date the document was created.",
    )
    schema_version: PropertyRef = PropertyRef(
        "SchemaVersion",
        description="The schema version of the document.",
    )
    version: PropertyRef = PropertyRef(
        "DocumentVersion",
        description="Document version returned by ListDocuments.",
    )
    shared_account_ids: PropertyRef = PropertyRef(
        "SharedAccountIds",
        description=(
            "Account IDs the document is shared with. The value `all` means the "
            "document is shared publicly. `null` means sharing could not be retrieved."
        ),
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The region of the document.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SSMDocumentToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SSMDocumentToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SSMDocumentToAWSAccountRelProperties = (
        SSMDocumentToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class SSMDocumentSchema(CartographyNodeSchema):
    """Self-owned AWS Systems Manager document from [`list_documents`](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm/client/list_documents.html) filtered to `Owner=Self`."""

    label: str = "AWSSSMDocument"
    properties: SSMDocumentNodeProperties = SSMDocumentNodeProperties()
    sub_resource_relationship: SSMDocumentToAWSAccountRel = SSMDocumentToAWSAccountRel()
