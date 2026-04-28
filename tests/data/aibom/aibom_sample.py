import tests.data.aws.ecr

# Digest-based URI pointing at the single-platform ECR image created by _seed_single_platform_graph
TEST_DIGEST_BASED_IMAGE_URI = (
    "000000000000.dkr.ecr.us-east-1.amazonaws.com/single-platform-repository"
    f"@{tests.data.aws.ecr.SINGLE_PLATFORM_DIGEST}"
)

TEST_CLUSTER_ID = "arn:aws:eks:us-east-1:000000000000:cluster/test-cluster"
TEST_CLUSTER_NAME = "test-cluster"

# Container whose status_image_sha matches the manifest list digest.
CONTAINER_ON_MANIFEST_LIST = {
    "uid": "container-on-ml",
    "name": "ml-container",
    "image": "000000000000.dkr.ecr.us-east-1.amazonaws.com/multi-arch-repository:v1.0",
    "namespace": "default",
    "pod_id": "pod-ml",
    "image_pull_policy": "Always",
    "status_image_id": "ml-image-id",
    "status_image_sha": tests.data.aws.ecr.MANIFEST_LIST_DIGEST,
    "architecture_normalized": "amd64",
    "status_ready": True,
    "status_started": True,
    "status_state": "running",
    "memory_request": None,
    "cpu_request": None,
    "memory_limit": None,
    "cpu_limit": None,
}

# Container whose status_image_sha matches the single-platform digest.
CONTAINER_ON_SINGLE_PLATFORM = {
    "uid": "container-on-sp",
    "name": "sp-container",
    "image": "000000000000.dkr.ecr.us-east-1.amazonaws.com/single-platform-repository:latest",
    "namespace": "default",
    "pod_id": "pod-sp",
    "image_pull_policy": "Always",
    "status_image_id": "sp-image-id",
    "status_image_sha": tests.data.aws.ecr.SINGLE_PLATFORM_DIGEST,
    "status_ready": True,
    "status_started": True,
    "status_state": "running",
    "memory_request": None,
    "cpu_request": None,
    "memory_limit": None,
    "cpu_limit": None,
}

TEST_IMAGE_URI = (
    "000000000000.dkr.ecr.us-east-1.amazonaws.com/multi-arch-repository:v1.0"
)
TEST_SINGLE_PLATFORM_IMAGE_URI = (
    "000000000000.dkr.ecr.us-east-1.amazonaws.com/single-platform-repository:latest"
)
TEST_UNMATCHED_IMAGE_URI = (
    "000000000000.dkr.ecr.us-east-1.amazonaws.com/unmatched-repository:v1.0"
)
TEST_SOURCE_KEY = (
    "000000000000.dkr.ecr.us-east-1.amazonaws.com/multi-arch-repository@sha256:fake"
)

AIBOM_REPORT = {
    "image_uri": TEST_IMAGE_URI,
    "scan_scope": "/srv/app",
    "scanner": {
        "name": "cisco-aibom",
        "version": "0.4.0",
    },
    "report": {
        "aibom_analysis": {
            "metadata": {
                "analyzer_version": "0.4.0",
                "status": "completed",
            },
            "summary": {
                "total_sources": 1,
                "status": "completed",
                "categories": {
                    "agent": 1,
                    "model": 1,
                    "tool": 1,
                    "memory": 1,
                    "prompt": 1,
                    "other": 1,
                },
            },
            "sources": {
                TEST_SOURCE_KEY: {
                    "summary": {
                        "status": "completed",
                        "source_kind": "container_image",
                    },
                    "workflows": [
                        {
                            "id": "workflow-agent",
                            "function": "app.chat.assistant.build_agent",
                            "file_path": "/srv/app/chat/assistant.py",
                            "line": 12,
                            "distance": 0,
                        },
                        {
                            "id": "workflow-tool",
                            "function": "app.tools.customer.fetch_customer_profile",
                            "file_path": "/srv/app/tools/customer.py",
                            "line": 12,
                            "distance": 1,
                        },
                    ],
                    "relationships": [
                        {
                            "relationship_type": "USES_LLM",
                            "source": {
                                "instance_id": "agent_main",
                                "name": "pydantic_ai.Agent",
                                "category": "agent",
                            },
                            "target": {
                                "instance_id": "model_primary",
                                "name": "openai:gpt-4.1-mini",
                                "category": "model",
                            },
                        },
                        {
                            "relationship_type": "USES_TOOL",
                            "source": {
                                "instance_id": "agent_main",
                                "name": "pydantic_ai.Agent",
                                "category": "agent",
                            },
                            "target": {
                                "instance_id": "tool_customer_lookup",
                                "name": "fetch_customer_profile",
                                "category": "tool",
                            },
                        },
                        {
                            "relationship_type": "USES_MEMORY",
                            "source": {
                                "instance_id": "agent_main",
                                "name": "pydantic_ai.Agent",
                                "category": "agent",
                            },
                            "target": {
                                "instance_id": "memory_buffer",
                                "name": "ConversationBufferMemory",
                                "category": "memory",
                            },
                        },
                        {
                            "relationship_type": "USES_PROMPT",
                            "source": {
                                "instance_id": "agent_main",
                                "name": "pydantic_ai.Agent",
                                "category": "agent",
                            },
                            "target": {
                                "instance_id": "prompt_customer_support",
                                "name": "system_prompt.customer_support",
                                "category": "prompt",
                            },
                        },
                    ],
                    "components": {
                        "agent": [
                            {
                                "name": "pydantic_ai.Agent",
                                "file_path": "/srv/app/chat/assistant.py",
                                "line_number": 34,
                                "category": "agent",
                                "instance_id": "agent_main",
                                "assigned_target": "assistant",
                                "framework": "pydantic_ai",
                                "label": "customer_assistant",
                                "metadata": {
                                    "approval": "human",
                                    "mcp": True,
                                },
                                "workflows": [
                                    {
                                        "id": "workflow-agent",
                                        "function": "app.chat.assistant.build_agent",
                                        "file_path": "/srv/app/chat/assistant.py",
                                        "line": 12,
                                        "distance": 0,
                                    },
                                ],
                            },
                        ],
                        "model": [
                            {
                                "name": "openai:gpt-4.1-mini",
                                "file_path": "/srv/app/chat/assistant.py",
                                "line_number": 35,
                                "category": "model",
                                "instance_id": "model_primary",
                                "model_name": "gpt-4.1-mini",
                                "framework": "openai",
                                "label": "primary_llm",
                                "workflows": [
                                    {
                                        "id": "workflow-agent",
                                        "function": "app.chat.assistant.build_agent",
                                        "file_path": "/srv/app/chat/assistant.py",
                                        "line": 12,
                                        "distance": 0,
                                    },
                                ],
                            },
                        ],
                        "tool": [
                            {
                                "name": "fetch_customer_profile",
                                "file_path": "/srv/app/tools/customer.py",
                                "line_number": 12,
                                "category": "tool",
                                "instance_id": "tool_customer_lookup",
                                "assigned_target": "customer_lookup",
                                "framework": "internal_mcp",
                                "label": "customer_lookup_tool",
                                "metadata": {
                                    "approval": "required",
                                    "transport": "mcp",
                                },
                                "workflows": [
                                    {
                                        "id": "workflow-tool",
                                        "function": "app.tools.customer.fetch_customer_profile",
                                        "file_path": "/srv/app/tools/customer.py",
                                        "line": 12,
                                        "distance": 1,
                                    },
                                ],
                            },
                        ],
                        "memory": [
                            {
                                "name": "ConversationBufferMemory",
                                "file_path": "/srv/app/chat/memory.py",
                                "line_number": 20,
                                "category": "memory",
                                "instance_id": "memory_buffer",
                                "framework": "langchain",
                                "label": "session_memory",
                                "workflows": [
                                    {
                                        "id": "workflow-agent",
                                        "function": "app.chat.assistant.build_agent",
                                        "file_path": "/srv/app/chat/assistant.py",
                                        "line": 12,
                                        "distance": 0,
                                    },
                                ],
                            },
                        ],
                        "prompt": [
                            {
                                "name": "system_prompt.customer_support",
                                "file_path": "/srv/app/chat/prompts.py",
                                "line_number": 7,
                                "category": "prompt",
                                "instance_id": "prompt_customer_support",
                                "framework": "internal",
                                "label": "system_prompt",
                                "workflows": [
                                    {
                                        "id": "workflow-agent",
                                        "function": "app.chat.assistant.build_agent",
                                        "file_path": "/srv/app/chat/assistant.py",
                                        "line": 12,
                                        "distance": 0,
                                    },
                                ],
                            },
                        ],
                        "other": [
                            {
                                "name": "json.loads",
                                "file_path": "/usr/local/lib/python3.12/json/__init__.py",
                                "line_number": 299,
                                "category": "other",
                                "instance_id": "json_loads_299",
                            },
                        ],
                    },
                },
            },
        },
    },
}

AIBOM_DIGEST_BASED_REPORT = {
    "image_uri": TEST_DIGEST_BASED_IMAGE_URI,
    "scan_scope": "/srv/app",
    "scanner": {
        "name": "cisco-aibom",
        "version": "0.4.0",
    },
    "report": {
        "aibom_analysis": {
            "metadata": {
                "analyzer_version": "0.4.0",
                "status": "completed",
            },
            "summary": {
                "total_sources": 1,
                "status": "completed",
                "categories": {
                    "agent": 1,
                    "model": 1,
                },
            },
            "sources": {
                TEST_DIGEST_BASED_IMAGE_URI: {
                    "summary": {
                        "status": "completed",
                        "source_kind": "container_image",
                    },
                    "workflows": [],
                    "relationships": [
                        {
                            "relationship_type": "USES_LLM",
                            "source": {
                                "instance_id": "ont_agent_main",
                                "name": "pydantic_ai.Agent",
                                "category": "agent",
                            },
                            "target": {
                                "instance_id": "ont_model_primary",
                                "name": "openai:gpt-4.1-mini",
                                "category": "model",
                            },
                        },
                    ],
                    "components": {
                        "agent": [
                            {
                                "name": "pydantic_ai.Agent",
                                "file_path": "/srv/app/chat/assistant.py",
                                "line_number": 34,
                                "category": "agent",
                                "instance_id": "ont_agent_main",
                                "assigned_target": "assistant",
                                "framework": "pydantic_ai",
                                "label": "customer_assistant",
                            },
                        ],
                        "model": [
                            {
                                "name": "openai:gpt-4.1-mini",
                                "file_path": "/srv/app/chat/assistant.py",
                                "line_number": 35,
                                "category": "model",
                                "instance_id": "ont_model_primary",
                                "model_name": "gpt-4.1-mini",
                                "framework": "openai",
                                "label": "primary_llm",
                            },
                        ],
                    },
                },
            },
        },
    },
}

AIBOM_INCOMPLETE_REPORT = {
    "image_uri": TEST_IMAGE_URI,
    "scan_scope": "/srv/app",
    "scanner": {
        "name": "cisco-aibom",
        "version": "0.4.0",
    },
    "report": {
        "aibom_analysis": {
            "metadata": {
                "analyzer_version": "0.4.0",
                "status": "failed",
            },
            "sources": {
                TEST_SOURCE_KEY: {
                    "summary": {
                        "status": "failed",
                        "source_kind": "container_image",
                    },
                    "components": {
                        "agent": [
                            {
                                "name": "pydantic_ai.Agent",
                                "file_path": "/srv/app/chat/assistant.py",
                                "line_number": 999,
                                "category": "agent",
                                "instance_id": "failed_agent",
                            },
                        ],
                    },
                },
            },
        },
    },
}

AIBOM_UNMATCHED_REPORT = {
    "image_uri": TEST_UNMATCHED_IMAGE_URI,
    "scan_scope": "/srv/app",
    "scanner": {
        "name": "cisco-aibom",
        "version": "0.4.0",
    },
    "report": {
        "aibom_analysis": {
            "metadata": {
                "analyzer_version": "0.4.0",
                "status": "completed",
            },
            "sources": {
                TEST_SOURCE_KEY: {
                    "summary": {
                        "status": "completed",
                        "source_kind": "container_image",
                    },
                    "components": {
                        "agent": [
                            {
                                "name": "pydantic_ai.Agent",
                                "file_path": "/srv/app/chat/assistant.py",
                                "line_number": 100,
                                "category": "agent",
                                "instance_id": "unmatched_agent",
                            },
                        ],
                    },
                },
            },
        },
    },
}

AIBOM_SINGLE_PLATFORM_REPORT = {
    "image_uri": TEST_SINGLE_PLATFORM_IMAGE_URI,
    "scan_scope": "/srv/app",
    "scanner": {
        "name": "cisco-aibom",
        "version": "0.4.0",
    },
    "report": {
        "aibom_analysis": {
            "metadata": {
                "analyzer_version": "0.4.0",
                "status": "completed",
            },
            "sources": {
                TEST_SOURCE_KEY: {
                    "summary": {
                        "status": "completed",
                        "source_kind": "container_image",
                    },
                    "components": {
                        "agent": [
                            {
                                "name": "pydantic_ai.Agent",
                                "file_path": "/srv/app/chat/assistant.py",
                                "line_number": 250,
                                "category": "agent",
                                "instance_id": "single_platform_agent",
                            },
                        ],
                    },
                },
            },
        },
    },
}
