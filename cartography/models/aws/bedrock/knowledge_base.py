"""
Knowledge Bases provide RAG (Retrieval Augmented Generation) capabilities by:
    - Sourcing documents from S3
    - Converting them to vector embeddings
    - Storing vectors in a vector database (OpenSearch, Aurora, Pinecone, etc.)
    - Enabling semantic search for agents and applications
"""

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
class AWSBedrockKnowledgeBaseNodeProperties(CartographyNodeProperties):
    """
    Properties for AWS Bedrock Knowledge Base nodes.

    Based on AWS Bedrock list_knowledge_bases and get_knowledge_base API responses.
    """

    id: PropertyRef = PropertyRef(
        "knowledgeBaseArn", description="The ARN of the knowledge base"
    )
    arn: PropertyRef = PropertyRef(
        "knowledgeBaseArn",
        extra_index=True,
        description="The ARN of the knowledge base",
    )
    knowledge_base_id: PropertyRef = PropertyRef(
        "knowledgeBaseId",
        extra_index=True,
        description="The unique identifier of the knowledge base",
    )
    name: PropertyRef = PropertyRef(
        "name", description="The name of the knowledge base"
    )
    description: PropertyRef = PropertyRef(
        "description", description="The description of the knowledge base"
    )
    role_arn: PropertyRef = PropertyRef(
        "roleArn", description="The ARN of the IAM role that the knowledge base uses"
    )
    knowledge_base_configuration_type: PropertyRef = PropertyRef(
        "knowledgeBaseConfiguration.type",
        description="Type of retrieval configuration used by the knowledge base.",
    )
    storage_configuration_type: PropertyRef = PropertyRef(
        "storageConfiguration.type",
        description="Type of vector storage used by the knowledge base.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description='The status of the knowledge base (e.g., "CREATING", "ACTIVE", "DELETING")',
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="The timestamp when the knowledge base was created"
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt",
        description="The timestamp when the knowledge base was last updated",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the knowledge base exists",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSBedrockKnowledgeBaseToAWSAccountRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockKnowledgeBase and AWSAccount.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockKnowledgeBaseToAWSAccountRel(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockKnowledgeBase to AWSAccount.
    """

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSBedrockKnowledgeBaseToAWSAccountRelProperties = (
        AWSBedrockKnowledgeBaseToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockKnowledgeBaseToS3BucketRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockKnowledgeBase and AWSS3Bucket.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockKnowledgeBaseToS3BucketRel(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockKnowledgeBase to AWSS3Bucket.
    """

    target_node_label: str = "AWSS3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("data_source_bucket_names", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SOURCES_DATA_FROM"
    properties: AWSBedrockKnowledgeBaseToS3BucketRelProperties = (
        AWSBedrockKnowledgeBaseToS3BucketRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockKnowledgeBaseToFoundationModelRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockKnowledgeBase and AWSBedrockFoundationModel.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockKnowledgeBaseToFoundationModelRel(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockKnowledgeBase to AWSBedrockFoundationModel.
    """

    target_node_label: str = "AWSBedrockFoundationModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("embeddingModelArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_EMBEDDING_MODEL"
    properties: AWSBedrockKnowledgeBaseToFoundationModelRelProperties = (
        AWSBedrockKnowledgeBaseToFoundationModelRelProperties()
    )


# TODO: Add relationship to vector store when OpenSearch Serverless node type is implemented
# Would require a new module to ingest OpenSearch Serverless collections


@dataclass(frozen=True)
class AWSBedrockKnowledgeBaseSchema(CartographyNodeSchema):
    """
    Schema for AWS Bedrock Knowledge Base nodes.
    """

    label: str = "AWSBedrockKnowledgeBase"
    properties: AWSBedrockKnowledgeBaseNodeProperties = (
        AWSBedrockKnowledgeBaseNodeProperties()
    )
    sub_resource_relationship: AWSBedrockKnowledgeBaseToAWSAccountRel = (
        AWSBedrockKnowledgeBaseToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSBedrockKnowledgeBaseToS3BucketRel(),
            AWSBedrockKnowledgeBaseToFoundationModelRel(),
            # TODO: Add AWSBedrockKnowledgeBaseToOpenSearchServerless() when OpenSearch nodes are available
        ],
    )
