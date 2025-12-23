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
class AWSSSMDocumentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ARN")
    name: PropertyRef = PropertyRef("Name")
    arn: PropertyRef = PropertyRef("ARN")
    owner: PropertyRef = PropertyRef("Owner")
    platform_types: PropertyRef = PropertyRef(
        "PlatformTypes"
    )  # List, needs json.dumps potentially? Or PropertyRef handles list?
    # Neo4j supports list of strings.
    document_version: PropertyRef = PropertyRef("DocumentVersion")
    document_type: PropertyRef = PropertyRef("DocumentType")
    schema_version: PropertyRef = PropertyRef("SchemaVersion")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSMDocumentToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSSMDocumentToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSSMDocumentToAWSAccountRelProperties = (
        AWSSSMDocumentToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSSSMDocumentSchema(CartographyNodeSchema):
    label: str = "AWSSSMDocument"
    properties: AWSSSMDocumentNodeProperties = AWSSSMDocumentNodeProperties()
    sub_resource_relationship: AWSSSMDocumentToAWSAccountRel = (
        AWSSSMDocumentToAWSAccountRel()
    )
