TEST_IMAGE_URI = (
    "000000000000.dkr.ecr.us-east-1.amazonaws.com/multi-arch-repository:v1.0"
)
TEST_SINGLE_PLATFORM_IMAGE_URI = (
    "000000000000.dkr.ecr.us-east-1.amazonaws.com/single-platform-repository:latest"
)
TEST_UNMATCHED_IMAGE_URI = (
    "000000000000.dkr.ecr.us-east-1.amazonaws.com/unmatched-repository:v1.0"
)
TEST_LOCAL_SOURCE_KEY = "/tmp/aibom-sample/app"

AIBOM_REPORT = {
    "image_uri": TEST_IMAGE_URI,
    "scan_scope": "/app/app",
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
                    "tool": 1,
                    "other": 1,
                },
            },
            "sources": {
                TEST_LOCAL_SOURCE_KEY: {
                    "summary": {
                        "status": "completed",
                    },
                    "workflows": [
                        {
                            "id": "workflow-agent",
                            "function": "app.chat.agent.build_agent",
                            "file_path": "/app/app/chat/agent.py",
                            "line": 120,
                            "distance": 0,
                        },
                        {
                            "id": "workflow-tool",
                            "function": "app.tools.lookup",
                            "file_path": "/app/app/tools.py",
                            "line": 40,
                            "distance": 1,
                        },
                    ],
                    "components": {
                        "agent": [
                            {
                                "name": "langchain.agents.create_agent",
                                "file_path": "/app/app/chat/agent.py",
                                "line_number": 195,
                                "category": "agent",
                                "instance_id": "langchain.agents.create_agent_195",
                                "assigned_target": "agent",
                                "workflows": [
                                    {
                                        "id": "workflow-agent",
                                        "function": "app.chat.agent.build_agent",
                                        "file_path": "/app/app/chat/agent.py",
                                        "line": 120,
                                        "distance": 0,
                                    },
                                ],
                            },
                        ],
                        "tool": [
                            {
                                "name": "typing.get_args",
                                "file_path": "/app/app/sync/modules/base.py",
                                "line_number": 90,
                                "category": "tool",
                                "instance_id": "typing.get_args_90",
                                "assigned_target": "tool",
                                "workflows": [
                                    {
                                        "id": "workflow-tool",
                                        "function": "app.tools.lookup",
                                        "file_path": "/app/app/tools.py",
                                        "line": 40,
                                        "distance": 1,
                                    },
                                ],
                            },
                        ],
                        "other": [
                            {
                                "name": "typing.get_origin",
                                "file_path": "/app/app/sync/modules/base.py",
                                "line_number": 89,
                                "category": "other",
                                "instance_id": "typing.get_origin_89",
                                "assigned_target": "other",
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
    "scanner": {
        "name": "cisco-aibom",
        "version": "0.4.0",
    },
    "report": {
        "aibom_analysis": {
            "metadata": {
                "analyzer_version": "0.4.0",
            },
            "sources": {
                TEST_LOCAL_SOURCE_KEY: {
                    "summary": {
                        "status": "failed",
                    },
                    "components": {
                        "agent": [
                            {
                                "name": "langchain.agents.create_agent",
                                "file_path": "/app/app/chat/agent.py",
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
    "scanner": {
        "name": "cisco-aibom",
        "version": "0.4.0",
    },
    "report": {
        "aibom_analysis": {
            "metadata": {
                "analyzer_version": "0.4.0",
            },
            "sources": {
                TEST_LOCAL_SOURCE_KEY: {
                    "summary": {
                        "status": "completed",
                    },
                    "components": {
                        "agent": [
                            {
                                "name": "langchain.agents.create_agent",
                                "file_path": "/app/app/chat/agent.py",
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
    "scanner": {
        "name": "cisco-aibom",
        "version": "0.4.0",
    },
    "report": {
        "aibom_analysis": {
            "metadata": {
                "analyzer_version": "0.4.0",
            },
            "sources": {
                TEST_LOCAL_SOURCE_KEY: {
                    "summary": {
                        "status": "completed",
                    },
                    "components": {
                        "agent": [
                            {
                                "name": "langchain.agents.create_agent",
                                "file_path": "/app/app/chat/agent.py",
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
