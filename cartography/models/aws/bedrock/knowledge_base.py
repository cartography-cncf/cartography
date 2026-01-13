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

    id: PropertyRef = PropertyRef("knowledgeBaseArn")
    arn: PropertyRef = PropertyRef("knowledgeBaseArn", extra_index=True)
    knowledge_base_id: PropertyRef = PropertyRef("knowledgeBaseId", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    role_arn: PropertyRef = PropertyRef("roleArn")
    knowledge_base_configuration_type: PropertyRef = PropertyRef(
        "knowledgeBaseConfiguration.type"
    )
    storage_configuration_type: PropertyRef = PropertyRef("storageConfiguration.type")
    status: PropertyRef = PropertyRef("status")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockKnowledgeBaseToAWSAccountRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockKnowledgeBase and AWSAccount.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockKnowledgeBaseToAWSAccount(CartographyRelSchema):
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
    Properties for the relationship between AWSBedrockKnowledgeBase and S3Bucket.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockKnowledgeBaseToS3Bucket(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockKnowledgeBase to S3Bucket.
    """

    target_node_label: str = "S3Bucket"
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
class AWSBedrockKnowledgeBaseToFoundationModel(CartographyRelSchema):
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
    sub_resource_relationship: AWSBedrockKnowledgeBaseToAWSAccount = (
        AWSBedrockKnowledgeBaseToAWSAccount()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSBedrockKnowledgeBaseToS3Bucket(),
            AWSBedrockKnowledgeBaseToFoundationModel(),
            # TODO: Add AWSBedrockKnowledgeBaseToOpenSearchServerless() when OpenSearch nodes are available
        ],
    )
