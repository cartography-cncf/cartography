"""
Integration tests for AWS Bedrock intel module.

Focus on high-value tests:
1. Full sync pipeline with all resource types
2. Transform logic for foundationModel union type handling
3. Cross-resource relationships (Agent→Model, Agent→KB, Agent→Guardrail, KB→S3)
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.bedrock.agents
import cartography.intel.aws.bedrock.custom_models
import cartography.intel.aws.bedrock.foundation_models
import cartography.intel.aws.bedrock.guardrails
import cartography.intel.aws.bedrock.knowledge_bases
from tests.data.aws.bedrock import AGENTS
from tests.data.aws.bedrock import CUSTOM_MODELS
from tests.data.aws.bedrock import FOUNDATION_MODELS
from tests.data.aws.bedrock import GUARDRAILS
from tests.data.aws.bedrock import KNOWLEDGE_BASES
from tests.data.aws.bedrock import TEST_ACCOUNT_ID
from tests.data.aws.bedrock import TEST_REGION
from tests.data.aws.bedrock import TEST_UPDATE_TAG
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def create_test_s3_bucket(neo4j_session, bucket_name, update_tag):
    """Create a test S3Bucket node for relationship testing."""
    neo4j_session.run(
        """
        MERGE (bucket:S3Bucket{id: $bucket_id})
        ON CREATE SET bucket.firstseen = timestamp()
        SET bucket.name = $bucket_name,
            bucket.lastupdated = $update_tag
        """,
        bucket_id=bucket_name,
        bucket_name=bucket_name,
        update_tag=update_tag,
    )


class TestBedrockFoundationModelsSync:
    """Tests for foundation model sync."""

    @patch.object(
        cartography.intel.aws.bedrock.foundation_models,
        "get_foundation_models",
        return_value=FOUNDATION_MODELS,
    )
    def test_sync_foundation_models(self, mock_get, neo4j_session):
        """Test that foundation models sync correctly with all properties."""
        # Arrange
        boto3_session = MagicMock()
        create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_ACCOUNT_ID,
        }

        # Act
        cartography.intel.aws.bedrock.foundation_models.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Assert - nodes created with correct properties
        assert check_nodes(
            neo4j_session,
            "AWSBedrockFoundationModel",
            ["id", "model_id", "model_name", "provider_name"],
        ) == {
            (
                "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
                "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "Claude 3.5 Sonnet",
                "Anthropic",
            ),
            (
                "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1",
                "amazon.titan-embed-text-v1",
                "Titan Embeddings G1 - Text",
                "Amazon",
            ),
            (
                "arn:aws:bedrock:us-east-1::foundation-model/meta.llama3-70b-instruct-v1:0",
                "meta.llama3-70b-instruct-v1:0",
                "Llama 3 70B Instruct",
                "Meta",
            ),
        }


class TestBedrockAgentsSync:
    """Tests for agent sync including relationship creation."""

    @patch.object(
        cartography.intel.aws.bedrock.agents,
        "get_agents",
        return_value=AGENTS,
    )
    def test_sync_agents_creates_nodes(self, mock_get, neo4j_session):
        """Test that agents sync correctly with all properties."""
        # Arrange
        boto3_session = MagicMock()
        create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_ACCOUNT_ID,
        }

        # Act
        cartography.intel.aws.bedrock.agents.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Assert - agent node created
        assert check_nodes(
            neo4j_session,
            "AWSBedrockAgent",
            ["id", "agent_id", "agent_name", "agent_status"],
        ) == {
            (
                f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:agent/AGENT123ABC",
                "AGENT123ABC",
                "test-agent",
                "PREPARED",
            ),
        }

    @patch.object(
        cartography.intel.aws.bedrock.agents,
        "get_agents",
        return_value=AGENTS,
    )
    @patch.object(
        cartography.intel.aws.bedrock.foundation_models,
        "get_foundation_models",
        return_value=FOUNDATION_MODELS,
    )
    def test_agent_to_foundation_model_relationship(
        self, mock_fm, mock_agents, neo4j_session
    ):
        """Test that Agent→FoundationModel USES_MODEL relationship is created correctly."""
        # Arrange
        boto3_session = MagicMock()
        create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_ACCOUNT_ID,
        }

        # First sync foundation models (target nodes must exist)
        cartography.intel.aws.bedrock.foundation_models.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Then sync agents
        cartography.intel.aws.bedrock.agents.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Assert - USES_MODEL relationship created
        assert check_rels(
            neo4j_session,
            "AWSBedrockAgent",
            "id",
            "AWSBedrockFoundationModel",
            "id",
            "USES_MODEL",
            rel_direction_right=True,
        ) == {
            (
                f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:agent/AGENT123ABC",
                "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
            ),
        }

    @patch.object(
        cartography.intel.aws.bedrock.agents,
        "get_agents",
        return_value=AGENTS,
    )
    @patch.object(
        cartography.intel.aws.bedrock.knowledge_bases,
        "get_knowledge_bases",
        return_value=KNOWLEDGE_BASES,
    )
    @patch.object(
        cartography.intel.aws.bedrock.foundation_models,
        "get_foundation_models",
        return_value=FOUNDATION_MODELS,
    )
    def test_agent_to_knowledge_base_relationship(
        self, mock_fm, mock_kb, mock_agents, neo4j_session
    ):
        """Test that Agent→KnowledgeBase USES_KNOWLEDGE_BASE relationship is created."""
        # Arrange
        boto3_session = MagicMock()
        create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_ACCOUNT_ID,
        }

        # Sync foundation models first (KB needs embedding model)
        cartography.intel.aws.bedrock.foundation_models.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Sync knowledge bases
        cartography.intel.aws.bedrock.knowledge_bases.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Sync agents
        cartography.intel.aws.bedrock.agents.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Assert - USES_KNOWLEDGE_BASE relationship created
        assert check_rels(
            neo4j_session,
            "AWSBedrockAgent",
            "id",
            "AWSBedrockKnowledgeBase",
            "id",
            "USES_KNOWLEDGE_BASE",
            rel_direction_right=True,
        ) == {
            (
                f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:agent/AGENT123ABC",
                f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:knowledge-base/KB12345ABCD",
            ),
        }

    @patch.object(
        cartography.intel.aws.bedrock.agents,
        "get_agents",
        return_value=AGENTS,
    )
    @patch.object(
        cartography.intel.aws.bedrock.guardrails,
        "get_guardrails",
        return_value=GUARDRAILS,
    )
    @patch.object(
        cartography.intel.aws.bedrock.foundation_models,
        "get_foundation_models",
        return_value=FOUNDATION_MODELS,
    )
    def test_guardrail_to_agent_relationship(
        self, mock_fm, mock_guardrails, mock_agents, neo4j_session
    ):
        """Test that Guardrail→Agent APPLIED_TO relationship is created."""
        # Arrange
        boto3_session = MagicMock()
        create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_ACCOUNT_ID,
        }

        # Sync foundation models first
        cartography.intel.aws.bedrock.foundation_models.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Sync guardrails (target nodes must exist)
        cartography.intel.aws.bedrock.guardrails.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Sync agents
        cartography.intel.aws.bedrock.agents.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Assert - APPLIED_TO relationship created (Guardrail→Agent)
        assert check_rels(
            neo4j_session,
            "AWSBedrockGuardrail",
            "id",
            "AWSBedrockAgent",
            "id",
            "APPLIED_TO",
            rel_direction_right=True,
        ) == {
            (
                f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:guardrail/abc123def456",
                f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:agent/AGENT123ABC",
            ),
        }


class TestBedrockKnowledgeBasesSync:
    """Tests for knowledge base sync including embedding model relationship."""

    @patch.object(
        cartography.intel.aws.bedrock.knowledge_bases,
        "get_knowledge_bases",
        return_value=KNOWLEDGE_BASES,
    )
    @patch.object(
        cartography.intel.aws.bedrock.foundation_models,
        "get_foundation_models",
        return_value=FOUNDATION_MODELS,
    )
    def test_knowledge_base_to_embedding_model_relationship(
        self, mock_fm, mock_kb, neo4j_session
    ):
        """Test that KnowledgeBase→FoundationModel USES_EMBEDDING_MODEL relationship is created."""
        # Arrange
        boto3_session = MagicMock()
        create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_ACCOUNT_ID,
        }

        # Sync foundation models first
        cartography.intel.aws.bedrock.foundation_models.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Sync knowledge bases
        cartography.intel.aws.bedrock.knowledge_bases.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Assert - USES_EMBEDDING_MODEL relationship created
        assert check_rels(
            neo4j_session,
            "AWSBedrockKnowledgeBase",
            "id",
            "AWSBedrockFoundationModel",
            "id",
            "USES_EMBEDDING_MODEL",
            rel_direction_right=True,
        ) == {
            (
                f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:knowledge-base/KB12345ABCD",
                "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1",
            ),
        }


class TestAgentTransformFoundationModelUnionType:
    """
    Tests for the foundationModel field which can be:
    - Bare model ID (e.g., "anthropic.claude-v2")
    - Foundation model ARN
    - Custom model ARN
    - Provisioned throughput ARN
    """

    def test_transform_bare_model_id(self):
        """Test that bare model ID is converted to foundation model ARN."""
        agents = [
            {
                "agentId": "TEST123",
                "agentArn": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:agent/TEST123",
                "foundationModel": "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "knowledgeBaseSummaries": [],
                "actionGroupDetails": [],
            }
        ]

        result = cartography.intel.aws.bedrock.agents.transform_agents(
            agents, TEST_REGION, TEST_ACCOUNT_ID
        )

        assert result[0]["foundation_model_arn"] == (
            f"arn:aws:bedrock:{TEST_REGION}::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"
        )
        assert "custom_model_arn" not in result[0]
        assert "provisioned_model_arn" not in result[0]

    def test_transform_foundation_model_arn(self):
        """Test that foundation model ARN is preserved."""
        fm_arn = f"arn:aws:bedrock:{TEST_REGION}::foundation-model/anthropic.claude-v2"
        agents = [
            {
                "agentId": "TEST123",
                "agentArn": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:agent/TEST123",
                "foundationModel": fm_arn,
                "knowledgeBaseSummaries": [],
                "actionGroupDetails": [],
            }
        ]

        result = cartography.intel.aws.bedrock.agents.transform_agents(
            agents, TEST_REGION, TEST_ACCOUNT_ID
        )

        assert result[0]["foundation_model_arn"] == fm_arn
        assert "custom_model_arn" not in result[0]
        assert "provisioned_model_arn" not in result[0]

    def test_transform_custom_model_arn(self):
        """Test that custom model ARN sets custom_model_arn field."""
        custom_arn = (
            f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:custom-model/my-model"
        )
        agents = [
            {
                "agentId": "TEST123",
                "agentArn": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:agent/TEST123",
                "foundationModel": custom_arn,
                "knowledgeBaseSummaries": [],
                "actionGroupDetails": [],
            }
        ]

        result = cartography.intel.aws.bedrock.agents.transform_agents(
            agents, TEST_REGION, TEST_ACCOUNT_ID
        )

        assert result[0]["custom_model_arn"] == custom_arn
        assert "foundation_model_arn" not in result[0]
        assert "provisioned_model_arn" not in result[0]

    def test_transform_provisioned_model_arn(self):
        """Test that provisioned model ARN sets provisioned_model_arn field."""
        provisioned_arn = (
            f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:provisioned-model/my-pt"
        )
        agents = [
            {
                "agentId": "TEST123",
                "agentArn": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:agent/TEST123",
                "foundationModel": provisioned_arn,
                "knowledgeBaseSummaries": [],
                "actionGroupDetails": [],
            }
        ]

        result = cartography.intel.aws.bedrock.agents.transform_agents(
            agents, TEST_REGION, TEST_ACCOUNT_ID
        )

        assert result[0]["provisioned_model_arn"] == provisioned_arn
        assert "foundation_model_arn" not in result[0]
        assert "custom_model_arn" not in result[0]

    def test_transform_guardrail_id_to_arn(self):
        """Test that guardrail ID is converted to ARN without version suffix."""
        agents = [
            {
                "agentId": "TEST123",
                "agentArn": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:agent/TEST123",
                "foundationModel": "anthropic.claude-v2",
                "guardrailConfiguration": {
                    "guardrailIdentifier": "abc123",
                    "guardrailVersion": "DRAFT",
                },
                "knowledgeBaseSummaries": [],
                "actionGroupDetails": [],
            }
        ]

        result = cartography.intel.aws.bedrock.agents.transform_agents(
            agents, TEST_REGION, TEST_ACCOUNT_ID
        )

        # Version should NOT be included in ARN
        assert result[0]["guardrail_arn"] == (
            f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:guardrail/abc123"
        )

    def test_transform_guardrail_arn_preserved(self):
        """Test that guardrail ARN is preserved when already provided."""
        guardrail_arn = (
            f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:guardrail/xyz789"
        )
        agents = [
            {
                "agentId": "TEST123",
                "agentArn": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:agent/TEST123",
                "foundationModel": "anthropic.claude-v2",
                "guardrailConfiguration": {
                    "guardrailIdentifier": guardrail_arn,
                    "guardrailVersion": "1",
                },
                "knowledgeBaseSummaries": [],
                "actionGroupDetails": [],
            }
        ]

        result = cartography.intel.aws.bedrock.agents.transform_agents(
            agents, TEST_REGION, TEST_ACCOUNT_ID
        )

        assert result[0]["guardrail_arn"] == guardrail_arn


class TestBedrockGuardrailsSync:
    """Tests for guardrail sync."""

    @patch.object(
        cartography.intel.aws.bedrock.guardrails,
        "get_guardrails",
        return_value=GUARDRAILS,
    )
    def test_sync_guardrails(self, mock_get, neo4j_session):
        """Test that guardrails sync correctly with all properties."""
        # Arrange
        boto3_session = MagicMock()
        create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_ACCOUNT_ID,
        }

        # Act
        cartography.intel.aws.bedrock.guardrails.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Assert
        assert check_nodes(
            neo4j_session,
            "AWSBedrockGuardrail",
            ["id", "guardrail_id", "name", "status"],
        ) == {
            (
                f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:guardrail/abc123def456",
                "abc123def456",
                "test-guardrail",
                "READY",
            ),
        }

        # Assert - AWSAccount relationship
        assert check_rels(
            neo4j_session,
            "AWSAccount",
            "id",
            "AWSBedrockGuardrail",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        ) == {
            (
                TEST_ACCOUNT_ID,
                f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:guardrail/abc123def456",
            ),
        }


class TestBedrockS3Relationships:
    """
    Tests for Bedrock → S3 relationships.
    These are high-value cross-module relationship tests.
    """

    @patch.object(
        cartography.intel.aws.bedrock.knowledge_bases,
        "get_knowledge_bases",
        return_value=KNOWLEDGE_BASES,
    )
    def test_knowledge_base_to_s3_bucket_relationship(self, mock_kb, neo4j_session):
        """
        Test that KnowledgeBase→S3Bucket SOURCES_DATA_FROM relationship is created.
        This validates the data source bucket extraction from KB data sources.
        """
        # Arrange
        boto3_session = MagicMock()
        create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_ACCOUNT_ID,
        }

        # Create S3 bucket node (target must exist for relationship)
        bucket_name = f"test-bucket-{TEST_ACCOUNT_ID}"
        create_test_s3_bucket(neo4j_session, bucket_name, TEST_UPDATE_TAG)

        # Act
        cartography.intel.aws.bedrock.knowledge_bases.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Assert - SOURCES_DATA_FROM relationship created
        assert check_rels(
            neo4j_session,
            "AWSBedrockKnowledgeBase",
            "id",
            "S3Bucket",
            "name",
            "SOURCES_DATA_FROM",
            rel_direction_right=True,
        ) == {
            (
                f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:knowledge-base/KB12345ABCD",
                bucket_name,
            ),
        }

    @patch.object(
        cartography.intel.aws.bedrock.custom_models,
        "get_custom_models",
        return_value=CUSTOM_MODELS,
    )
    @patch.object(
        cartography.intel.aws.bedrock.foundation_models,
        "get_foundation_models",
        return_value=FOUNDATION_MODELS,
    )
    def test_custom_model_to_s3_bucket_relationship(
        self, mock_fm, mock_cm, neo4j_session
    ):
        """
        Test that CustomModel→S3Bucket TRAINED_FROM relationship is created.
        This validates the training data bucket extraction from custom model config.
        """
        # Arrange
        boto3_session = MagicMock()
        create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_ACCOUNT_ID,
        }

        # Create S3 bucket node (target must exist for relationship)
        training_bucket_name = f"training-bucket-{TEST_ACCOUNT_ID}"
        create_test_s3_bucket(neo4j_session, training_bucket_name, TEST_UPDATE_TAG)

        # Sync foundation models first (custom model BASED_ON relationship needs them)
        cartography.intel.aws.bedrock.foundation_models.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Act - sync custom models
        cartography.intel.aws.bedrock.custom_models.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Assert - custom model node created
        assert check_nodes(
            neo4j_session,
            "AWSBedrockCustomModel",
            ["id", "model_name", "customization_type"],
        ) == {
            (
                f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:custom-model/test-custom-model",
                "test-custom-model",
                "FINE_TUNING",
            ),
        }

        # Assert - TRAINED_FROM relationship created
        assert check_rels(
            neo4j_session,
            "AWSBedrockCustomModel",
            "id",
            "S3Bucket",
            "name",
            "TRAINED_FROM",
            rel_direction_right=True,
        ) == {
            (
                f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:custom-model/test-custom-model",
                training_bucket_name,
            ),
        }

        # Assert - BASED_ON relationship to foundation model
        assert check_rels(
            neo4j_session,
            "AWSBedrockCustomModel",
            "id",
            "AWSBedrockFoundationModel",
            "id",
            "BASED_ON",
            rel_direction_right=True,
        ) == {
            (
                f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:custom-model/test-custom-model",
                "arn:aws:bedrock:us-east-1::foundation-model/meta.llama3-70b-instruct-v1:0",
            ),
        }
