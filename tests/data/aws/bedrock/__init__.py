# Test data for AWS Bedrock intel module
# Data shapes based on real AWS API responses with redacted account IDs

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789

# Foundation Models - from list_foundation_models API
# These are public models so model IDs are not sensitive
FOUNDATION_MODELS = [
    {
        "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
        "modelId": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "modelName": "Claude 3.5 Sonnet",
        "providerName": "Anthropic",
        "inputModalities": ["TEXT", "IMAGE"],
        "outputModalities": ["TEXT"],
        "responseStreamingSupported": True,
        "customizationsSupported": [],
        "inferenceTypesSupported": ["ON_DEMAND"],
        "modelLifecycle": {"status": "ACTIVE"},
    },
    {
        "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1",
        "modelId": "amazon.titan-embed-text-v1",
        "modelName": "Titan Embeddings G1 - Text",
        "providerName": "Amazon",
        "inputModalities": ["TEXT"],
        "outputModalities": ["EMBEDDING"],
        "responseStreamingSupported": False,
        "customizationsSupported": [],
        "inferenceTypesSupported": ["ON_DEMAND"],
        "modelLifecycle": {"status": "ACTIVE"},
    },
    {
        "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/meta.llama3-70b-instruct-v1:0",
        "modelId": "meta.llama3-70b-instruct-v1:0",
        "modelName": "Llama 3 70B Instruct",
        "providerName": "Meta",
        "inputModalities": ["TEXT"],
        "outputModalities": ["TEXT"],
        "responseStreamingSupported": True,
        "customizationsSupported": ["FINE_TUNING"],
        "inferenceTypesSupported": ["ON_DEMAND"],
        "modelLifecycle": {"status": "ACTIVE"},
    },
]

# Guardrails - from get_guardrail API
GUARDRAILS = [
    {
        "name": "test-guardrail",
        "guardrailId": "abc123def456",
        "guardrailArn": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:guardrail/abc123def456",
        "version": "DRAFT",
        "status": "READY",
        "createdAt": "2025-01-01T00:00:00.000000+00:00",
        "updatedAt": "2025-01-01T00:00:00.000000+00:00",
        "blockedInputMessaging": "Sorry, the model cannot answer this question.",
        "blockedOutputsMessaging": "Sorry, the model cannot answer this question.",
    },
]

# Knowledge Bases - from get_knowledge_base API
KNOWLEDGE_BASES = [
    {
        "knowledgeBaseId": "KB12345ABCD",
        "name": "test-knowledge-base",
        "knowledgeBaseArn": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:knowledge-base/KB12345ABCD",
        "roleArn": f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/service-role/AmazonBedrockExecutionRoleForKnowledgeBase_test",
        "knowledgeBaseConfiguration": {
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": f"arn:aws:bedrock:{TEST_REGION}::foundation-model/amazon.titan-embed-text-v1",
                "embeddingModelConfiguration": {
                    "bedrockEmbeddingModelConfiguration": {
                        "embeddingDataType": "FLOAT32"
                    }
                },
            },
        },
        "storageConfiguration": {
            "type": "OPENSEARCH_SERVERLESS",
            "opensearchServerlessConfiguration": {
                "collectionArn": f"arn:aws:aoss:{TEST_REGION}:{TEST_ACCOUNT_ID}:collection/test123",
                "vectorIndexName": "bedrock-knowledge-base-default-index",
                "fieldMapping": {
                    "vectorField": "bedrock-knowledge-base-default-vector",
                    "textField": "AMAZON_BEDROCK_TEXT",
                    "metadataField": "AMAZON_BEDROCK_METADATA",
                },
            },
        },
        "status": "ACTIVE",
        "createdAt": "2025-01-01T00:00:00.000000+00:00",
        "updatedAt": "2025-01-01T00:00:00.000000+00:00",
        # Added by get_data_source calls in intel module
        "dataSourceDetails": [
            {
                "knowledgeBaseId": "KB12345ABCD",
                "dataSourceId": "DS12345ABCD",
                "name": "test-data-source",
                "status": "AVAILABLE",
                "dataSourceConfiguration": {
                    "type": "S3",
                    "s3Configuration": {
                        "bucketArn": f"arn:aws:s3:::test-bucket-{TEST_ACCOUNT_ID}"
                    },
                },
                "createdAt": "2025-01-01T00:00:00.000000+00:00",
                "updatedAt": "2025-01-01T00:00:00.000000+00:00",
            }
        ],
    },
]

# Agents - from get_agent API with associated knowledge bases and action groups
AGENTS = [
    {
        "agentId": "AGENT123ABC",
        "agentName": "test-agent",
        "agentArn": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:agent/AGENT123ABC",
        "instruction": "You are a helpful assistant for testing purposes.",
        "agentStatus": "PREPARED",
        "foundationModel": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "idleSessionTTLInSeconds": 600,
        "agentResourceRoleArn": f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/service-role/AmazonBedrockExecutionRoleForAgents_test",
        "createdAt": "2025-01-01T00:00:00.000000+00:00",
        "updatedAt": "2025-01-01T00:00:00.000000+00:00",
        "preparedAt": "2025-01-01T00:00:00.000000+00:00",
        "guardrailConfiguration": {
            "guardrailIdentifier": "abc123def456",
            "guardrailVersion": "DRAFT",
        },
        # Added by list_agent_knowledge_bases call
        "knowledgeBaseSummaries": [
            {
                "knowledgeBaseId": "KB12345ABCD",
                "description": "Test knowledge base for agent",
                "knowledgeBaseState": "ENABLED",
                "updatedAt": "2025-01-01T00:00:00.000000+00:00",
            }
        ],
        # Added by list_agent_action_groups and get_agent_action_group calls
        "actionGroupDetails": [],
    },
]

# Agent with Lambda action group
AGENTS_WITH_LAMBDA = [
    {
        "agentId": "AGENT456DEF",
        "agentName": "test-agent-with-lambda",
        "agentArn": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:agent/AGENT456DEF",
        "instruction": "You are a helpful assistant that can call Lambda functions.",
        "agentStatus": "PREPARED",
        "foundationModel": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "idleSessionTTLInSeconds": 600,
        "agentResourceRoleArn": f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/service-role/AmazonBedrockExecutionRoleForAgents_lambda",
        "createdAt": "2025-01-01T00:00:00.000000+00:00",
        "updatedAt": "2025-01-01T00:00:00.000000+00:00",
        "preparedAt": "2025-01-01T00:00:00.000000+00:00",
        "knowledgeBaseSummaries": [],
        "actionGroupDetails": [
            {
                "actionGroupId": "AG123ABC",
                "actionGroupName": "test-action-group",
                "actionGroupState": "ENABLED",
                "actionGroupExecutor": {
                    "lambda": f"arn:aws:lambda:{TEST_REGION}:{TEST_ACCOUNT_ID}:function:test-function"
                },
            }
        ],
    },
]

# Agent using custom model ARN
AGENTS_WITH_CUSTOM_MODEL = [
    {
        "agentId": "AGENT789GHI",
        "agentName": "test-agent-custom-model",
        "agentArn": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:agent/AGENT789GHI",
        "instruction": "You are a helpful assistant using a custom model.",
        "agentStatus": "PREPARED",
        "foundationModel": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:custom-model/test-custom-model",
        "idleSessionTTLInSeconds": 600,
        "agentResourceRoleArn": f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/service-role/AmazonBedrockExecutionRoleForAgents_custom",
        "createdAt": "2025-01-01T00:00:00.000000+00:00",
        "updatedAt": "2025-01-01T00:00:00.000000+00:00",
        "preparedAt": "2025-01-01T00:00:00.000000+00:00",
        "knowledgeBaseSummaries": [],
        "actionGroupDetails": [],
    },
]

# Agent using provisioned throughput ARN
AGENTS_WITH_PROVISIONED_THROUGHPUT = [
    {
        "agentId": "AGENTABCJKL",
        "agentName": "test-agent-provisioned",
        "agentArn": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:agent/AGENTABCJKL",
        "instruction": "You are a helpful assistant using provisioned throughput.",
        "agentStatus": "PREPARED",
        "foundationModel": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:provisioned-model/test-provisioned",
        "idleSessionTTLInSeconds": 600,
        "agentResourceRoleArn": f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/service-role/AmazonBedrockExecutionRoleForAgents_prov",
        "createdAt": "2025-01-01T00:00:00.000000+00:00",
        "updatedAt": "2025-01-01T00:00:00.000000+00:00",
        "preparedAt": "2025-01-01T00:00:00.000000+00:00",
        "knowledgeBaseSummaries": [],
        "actionGroupDetails": [],
    },
]

# Custom Models - from get_custom_model API
CUSTOM_MODELS = [
    {
        "modelArn": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:custom-model/test-custom-model",
        "modelName": "test-custom-model",
        "jobName": "test-fine-tuning-job",
        "jobArn": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:model-customization-job/test-job",
        "baseModelArn": "arn:aws:bedrock:us-east-1::foundation-model/meta.llama3-70b-instruct-v1:0",
        "customizationType": "FINE_TUNING",
        "modelKmsKeyArn": None,
        "hyperParameters": {
            "epochCount": "3",
            "batchSize": "1",
            "learningRate": "0.00001",
        },
        "trainingDataConfig": {
            "s3Uri": f"s3://training-bucket-{TEST_ACCOUNT_ID}/data/train.jsonl"
        },
        "outputDataConfig": {"s3Uri": f"s3://output-bucket-{TEST_ACCOUNT_ID}/output/"},
        "trainingMetrics": {"trainingLoss": 0.5},
        "modelStatus": "Active",
        "creationTime": "2025-01-01T00:00:00.000000+00:00",
    },
]

# Provisioned Model Throughputs - from get_provisioned_model_throughput API
PROVISIONED_THROUGHPUTS = [
    {
        "provisionedModelName": "test-provisioned-throughput",
        "provisionedModelArn": f"arn:aws:bedrock:{TEST_REGION}:{TEST_ACCOUNT_ID}:provisioned-model/test-provisioned",
        "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
        "desiredModelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
        "foundationModelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
        "modelUnits": 1,
        "desiredModelUnits": 1,
        "status": "InService",
        "commitmentDuration": "OneMonth",
        "commitmentExpirationTime": "2025-02-01T00:00:00.000000+00:00",
        "creationTime": "2025-01-01T00:00:00.000000+00:00",
        "lastModifiedTime": "2025-01-01T00:00:00.000000+00:00",
    },
]
