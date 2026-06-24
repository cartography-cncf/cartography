import copy
from typing import Any

import tests.data.aws.ecr

TEST_REPOSITORY_URI = "205930638578.dkr.ecr.us-east-1.amazonaws.com/subimage-backend"
TEST_SOURCE_KEY = (
    f"{TEST_REPOSITORY_URI}" f"@{tests.data.aws.ecr.SINGLE_PLATFORM_DIGEST}"
)
TEST_IMAGE_URI = "205930638578.dkr.ecr.us-east-1.amazonaws.com/subimage-backend:latest"
TEST_DIGEST_BASED_IMAGE_URI = TEST_SOURCE_KEY
TEST_SINGLE_PLATFORM_IMAGE_URI = TEST_IMAGE_URI
TEST_UNMATCHED_IMAGE_URI = (
    "205930638578.dkr.ecr.us-east-1.amazonaws.com/unmatched-backend"
    "@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
)

TEST_GAR_PROJECT_ID = "test-aibom-gar-project"
TEST_GAR_REPOSITORY_ID = (
    f"projects/{TEST_GAR_PROJECT_ID}/locations/us-central1/repositories/docker-repo"
)
TEST_GAR_IMAGE_DIGEST = "sha256:gar123"
TEST_GAR_IMAGE_URI = (
    f"us-central1-docker.pkg.dev/{TEST_GAR_PROJECT_ID}/docker-repo/my-app:latest"
)

AIBOM_REPORT = {
    "aibom_analysis": {
        "metadata": {
            "run_id": "4a06dcd7-f495-4ef8-a977-d2ec51e60ff9",
            "analyzer_version": "1.0.0rc4",
            "started_at": "2026-05-18T21:40:05Z",
            "output_format": "json",
            "sources_requested": 1,
            "llm_model": "gpt-5.4",
            "total_tokens": 6729082,
            "prompt_tokens": 6659670,
            "completion_tokens": 69412,
            "completed_at": "2026-05-18T22:19:20Z",
            "error_count": 0,
            "sources_analyzed": 1,
            "sources_with_errors": 0,
            "status": "completed",
            "report_schema_version": "2",
        },
        "sources": {
            TEST_SOURCE_KEY: {
                "source_name": TEST_SOURCE_KEY,
                "source_path": "/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h",
                "components": {
                    "secret": [
                        {
                            "name": "vault-secret",
                            "component_type": "secret",
                            "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sync/modules/gitlab.py",
                            "line_number": 394,
                            "framework": "",
                            "detection_source": "code_analysis",
                            "heuristic_confidence": 0.8,
                            "agentic_confidence": None,
                            "needs_agentic": True,
                            "agentic_hint": "",
                            "model_name": None,
                            "embedding_model": None,
                            "description": None,
                            "text": None,
                            "transport": None,
                            "config_source": None,
                            "storage_uri": None,
                            "dataset_source": None,
                            "skill_format": None,
                            "hyperparameters": {},
                            "training_info": None,
                            "metrics": {},
                            "kb_concept": None,
                            "kb_label": None,
                            "sdk_version": None,
                            "decision_annotation": {
                                "decision": "confirmed",
                                "justification": "Kept in the "
                                "final AIBOM "
                                "because the scan "
                                "identified "
                                "secret "
                                "'vault-secret'.",
                                "evidence_kinds": ["code_context"],
                                "evidence_locations": [
                                    {
                                        "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sync/modules/gitlab.py",
                                        "start_line": 394,
                                        "end_line": 394,
                                        "role": "primary",
                                    }
                                ],
                                "code_snippet": None,
                            },
                            "metadata": {
                                "secret_source": "vault_sdk",
                                "secret_path": "",
                                "has_vault_import": True,
                                "evidence": [
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/utils/gcp_credentials.py",
                                        "line": 26,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app",
                                        "test_only": False,
                                    },
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sync/modules/scan.py",
                                        "line": 215,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app",
                                        "test_only": False,
                                    },
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sync/modules/scan.py",
                                        "line": 393,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app",
                                        "test_only": False,
                                    },
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sync/modules/vulnerabilities.py",
                                        "line": 208,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app",
                                        "test_only": False,
                                    },
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sync/modules/github.py",
                                        "line": 209,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app",
                                        "test_only": False,
                                    },
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sync/modules/github.py",
                                        "line": 480,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app",
                                        "test_only": False,
                                    },
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sync/modules/gcp.py",
                                        "line": 285,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app",
                                        "test_only": False,
                                    },
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/scripts/utils/github_installation_lookup.py",
                                        "line": 34,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app",
                                        "test_only": False,
                                    },
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/scripts/audit/query_stale_node_labels_across_customers.py",
                                        "line": 239,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app",
                                        "test_only": False,
                                    },
                                ],
                                "evidence_count": 10,
                                "evidence_files": [
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/utils/gcp_credentials.py",
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sync/modules/gitlab.py",
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sync/modules/scan.py",
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sync/modules/vulnerabilities.py",
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sync/modules/github.py",
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sync/modules/gcp.py",
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/scripts/utils/github_installation_lookup.py",
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/scripts/audit/query_stale_node_labels_across_customers.py",
                                ],
                                "consolidated_count": 10,
                            },
                            "instance_id": "vault-secret_/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sync/modules/gitlab.py_394",
                            "confidence": 0.8,
                        },
                        {
                            "name": "env_secret_OPENAI_API_KEY",
                            "component_type": "secret",
                            "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/.env.local.example",
                            "line_number": 10,
                            "framework": "",
                            "detection_source": "config_file",
                            "heuristic_confidence": 1.0,
                            "agentic_confidence": None,
                            "needs_agentic": True,
                            "agentic_hint": "",
                            "model_name": None,
                            "embedding_model": None,
                            "description": "API key variable `OPENAI_API_KEY` present "
                            "(value redacted)",
                            "text": None,
                            "transport": None,
                            "config_source": ".env.local.example",
                            "storage_uri": None,
                            "dataset_source": None,
                            "skill_format": None,
                            "hyperparameters": {},
                            "training_info": None,
                            "metrics": {},
                            "kb_concept": None,
                            "kb_label": None,
                            "sdk_version": None,
                            "decision_annotation": {
                                "decision": "confirmed",
                                "justification": "Kept in the "
                                "final AIBOM "
                                "because the scan "
                                "identified "
                                "secret "
                                "'env_secret_OPENAI_API_KEY'.",
                                "evidence_kinds": ["code_context"],
                                "evidence_locations": [
                                    {
                                        "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/.env.local.example",
                                        "start_line": 10,
                                        "end_line": 10,
                                        "role": "primary",
                                    }
                                ],
                                "code_snippet": None,
                            },
                            "metadata": {
                                "env_var": "OPENAI_API_KEY",
                                "redacted": True,
                                "config_kind": ".env",
                                "evidence_count": 1,
                                "evidence_files": [
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/.env.local.example"
                                ],
                            },
                            "instance_id": "env_secret_OPENAI_API_KEY_/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/.env.local.example_10",
                            "confidence": 1.0,
                        },
                    ],
                    "dependency": [
                        {
                            "name": "litellm",
                            "component_type": "dependency",
                            "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/uv.lock",
                            "line_number": 2706,
                            "framework": "",
                            "detection_source": "dependency_manifest",
                            "heuristic_confidence": 1.0,
                            "agentic_confidence": None,
                            "needs_agentic": True,
                            "agentic_hint": "",
                            "model_name": None,
                            "embedding_model": None,
                            "description": "4 known vulnerabilities in litellm "
                            "1.83.0",
                            "text": None,
                            "transport": None,
                            "config_source": None,
                            "storage_uri": None,
                            "dataset_source": None,
                            "skill_format": None,
                            "hyperparameters": {},
                            "training_info": None,
                            "metrics": {},
                            "kb_concept": None,
                            "kb_label": None,
                            "sdk_version": "1.83.0",
                            "decision_annotation": {
                                "decision": "confirmed",
                                "justification": "Kept in the "
                                "final AIBOM "
                                "because the "
                                "scan "
                                "identified "
                                "dependency "
                                "'litellm'.",
                                "evidence_kinds": ["code_context"],
                                "evidence_locations": [
                                    {
                                        "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/uv.lock",
                                        "start_line": 2706,
                                        "end_line": 2706,
                                        "role": "primary",
                                    }
                                ],
                                "code_snippet": None,
                            },
                            "metadata": {
                                "ecosystem": "pypi",
                                "version_spec": "1.83.0",
                                "manifest": "uv.lock",
                                "known_ai_package": True,
                                "vulnerabilities": [
                                    {
                                        "id": "GHSA-r75f-5x8p-qvmc",
                                        "summary": "",
                                        "severity": "info",
                                        "cvss_score": 0.0,
                                        "affected_package": "litellm",
                                        "affected_version": "1.83.0",
                                        "fixed_version": "",
                                        "source": "osv",
                                        "url": "",
                                    },
                                    {
                                        "id": "GHSA-v4p8-mg3p-g94g",
                                        "summary": "",
                                        "severity": "info",
                                        "cvss_score": 0.0,
                                        "affected_package": "litellm",
                                        "affected_version": "1.83.0",
                                        "fixed_version": "",
                                        "source": "osv",
                                        "url": "",
                                    },
                                    {
                                        "id": "GHSA-wxxx-gvqv-xp7p",
                                        "summary": "",
                                        "severity": "info",
                                        "cvss_score": 0.0,
                                        "affected_package": "litellm",
                                        "affected_version": "1.83.0",
                                        "fixed_version": "",
                                        "source": "osv",
                                        "url": "",
                                    },
                                    {
                                        "id": "GHSA-xqmj-j6mv-4862",
                                        "summary": "",
                                        "severity": "info",
                                        "cvss_score": 0.0,
                                        "affected_package": "litellm",
                                        "affected_version": "1.83.0",
                                        "fixed_version": "",
                                        "source": "osv",
                                        "url": "",
                                    },
                                ],
                                "risk_flag": {
                                    "flag": "vulnerable_dependency:litellm",
                                    "severity": "info",
                                    "weight": 1,
                                    "description": "4 known "
                                    "vulnerabilities "
                                    "in litellm "
                                    "1.83.0",
                                },
                                "evidence": [
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/uv.lock",
                                        "line": 2706,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app",
                                        "test_only": False,
                                    }
                                ],
                                "evidence_count": 2,
                                "evidence_files": [
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/uv.lock"
                                ],
                                "consolidated_count": 2,
                            },
                            "instance_id": "litellm_/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/uv.lock_2706",
                            "confidence": 1.0,
                        }
                    ],
                    "mcp_server": [
                        {
                            "name": "attack_path_tools",
                            "component_type": "mcp_server",
                            "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/attack_path/mcp.py",
                            "line_number": 36,
                            "framework": "mcp",
                            "detection_source": "agentic",
                            "heuristic_confidence": 1.0,
                            "agentic_confidence": None,
                            "needs_agentic": True,
                            "agentic_hint": "",
                            "model_name": None,
                            "embedding_model": None,
                            "description": None,
                            "text": None,
                            "transport": "stdio",
                            "config_source": None,
                            "storage_uri": None,
                            "dataset_source": None,
                            "skill_format": None,
                            "hyperparameters": {},
                            "training_info": None,
                            "metrics": {},
                            "kb_concept": None,
                            "kb_label": None,
                            "sdk_version": None,
                            "decision_annotation": {
                                "decision": "added",
                                "justification": "The "
                                "ToolCollection "
                                "instance "
                                "serves as "
                                "the MCP tool "
                                "host for "
                                "this module "
                                "because "
                                "decorated "
                                "functions "
                                "are "
                                "registered "
                                "against it "
                                "as callable "
                                "tools.",
                                "evidence_kinds": [
                                    "tool_result",
                                    "relationship_context",
                                ],
                                "evidence_locations": [
                                    {
                                        "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/attack_path/mcp.py",
                                        "start_line": 36,
                                        "end_line": 40,
                                        "role": "primary",
                                    },
                                    {
                                        "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/attack_path/mcp.py",
                                        "start_line": 39,
                                        "end_line": 160,
                                        "role": "supporting",
                                    },
                                ],
                                "code_snippet": None,
                            },
                            "metadata": {
                                "evidence_count": 1,
                                "evidence_files": [
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/attack_path/mcp.py"
                                ],
                            },
                            "instance_id": "attack_path_tools_/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/attack_path/mcp.py_36",
                            "confidence": 1.0,
                        }
                    ],
                    "tool": [
                        {
                            "name": "subimageGetTicket",
                            "component_type": "tool",
                            "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/integrations/linear/mcp.py",
                            "line_number": 102,
                            "framework": "mcp",
                            "detection_source": "agentic",
                            "heuristic_confidence": 1.0,
                            "agentic_confidence": None,
                            "needs_agentic": True,
                            "agentic_hint": "",
                            "model_name": None,
                            "embedding_model": None,
                            "description": None,
                            "text": None,
                            "transport": None,
                            "config_source": None,
                            "storage_uri": None,
                            "dataset_source": None,
                            "skill_format": None,
                            "hyperparameters": {},
                            "training_info": None,
                            "metrics": {},
                            "kb_concept": None,
                            "kb_label": None,
                            "sdk_version": None,
                            "decision_annotation": {
                                "decision": "added",
                                "justification": "This file "
                                "registers a "
                                "concrete MCP tool "
                                "named "
                                "subimageGetTicket "
                                "via the "
                                "linear_tools.tool "
                                "decorator, but "
                                "that tool is not "
                                "present in the "
                                "detected component "
                                "lists.",
                                "evidence_kinds": ["code_context", "tool_result"],
                                "evidence_locations": [
                                    {
                                        "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/integrations/linear/mcp.py",
                                        "start_line": 102,
                                        "end_line": 119,
                                        "role": "primary",
                                    }
                                ],
                                "code_snippet": None,
                            },
                            "metadata": {
                                "mcp_tool_name": "subimageGetTicket",
                                "evidence_count": 1,
                                "evidence_files": [
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/integrations/linear/mcp.py"
                                ],
                            },
                            "instance_id": "subimageGetTicket_/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/integrations/linear/mcp.py_102",
                            "confidence": 1.0,
                        }
                    ],
                    "agent": [
                        {
                            "name": "Agent",
                            "component_type": "agent",
                            "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sub_agents/cloud_cli/agent.py",
                            "line_number": 39,
                            "framework": "",
                            "detection_source": "kb_enrichment",
                            "heuristic_confidence": 0.2,
                            "agentic_confidence": 0.82,
                            "needs_agentic": True,
                            "agentic_hint": "Class 'Agent' in path 'cloud_cli/'. A "
                            "class name alone is NOT proof of an AI "
                            "component. REMOVE unless code_context "
                            "proves this is a genuine AI agent. Classes "
                            "in AI-adjacent directories are often "
                            "ordinary handlers, utilities, or DTOs.",
                            "model_name": "gpt-5.2",
                            "embedding_model": "text-embedding-3-small",
                            "description": None,
                            "text": None,
                            "transport": None,
                            "config_source": None,
                            "storage_uri": None,
                            "dataset_source": None,
                            "skill_format": None,
                            "hyperparameters": {},
                            "training_info": None,
                            "metrics": {},
                            "kb_concept": None,
                            "kb_label": None,
                            "sdk_version": None,
                            "decision_annotation": {
                                "decision": "confirmed",
                                "justification": "Kept in the final "
                                "AIBOM because the "
                                "scan identified "
                                "agent 'Agent'.",
                                "evidence_kinds": ["code_context"],
                                "evidence_locations": [
                                    {
                                        "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sub_agents/cloud_cli/agent.py",
                                        "start_line": 39,
                                        "end_line": 39,
                                        "role": "primary",
                                    }
                                ],
                                "code_snippet": None,
                            },
                            "metadata": {
                                "suggestive_signal": True,
                                "parent_dir": "cloud_cli",
                                "evidence": [
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/chat_v2/compaction.py",
                                        "line": 197,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app",
                                        "test_only": False,
                                    }
                                ],
                                "evidence_count": 2,
                                "evidence_files": [
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/chat_v2/compaction.py",
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sub_agents/cloud_cli/agent.py",
                                ],
                                "consolidated_count": 2,
                            },
                            "instance_id": "Agent_/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sub_agents/cloud_cli/agent.py_39",
                            "confidence": 0.2,
                        }
                    ],
                    "dataset": [
                        {
                            "name": "dataset",
                            "component_type": "dataset",
                            "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/declarative_schema/fetcher.py",
                            "line_number": 497,
                            "framework": "cloud-storage",
                            "detection_source": "code_analysis",
                            "heuristic_confidence": 0.3,
                            "agentic_confidence": None,
                            "needs_agentic": True,
                            "agentic_hint": "pd.read_csv/cloud-storage without "
                            "ML/data imports",
                            "model_name": None,
                            "embedding_model": None,
                            "description": "Training or analytics data loading",
                            "text": "s3_path: S3 path to data file (e.g., "
                            "s3://bucket/team-members.jsonl)",
                            "transport": None,
                            "config_source": None,
                            "storage_uri": "s3://bucket/team-members.jsonl",
                            "dataset_source": "s3",
                            "skill_format": None,
                            "hyperparameters": {},
                            "training_info": None,
                            "metrics": {},
                            "kb_concept": None,
                            "kb_label": None,
                            "sdk_version": None,
                            "decision_annotation": {
                                "decision": "confirmed",
                                "justification": "Kept in the "
                                "final AIBOM "
                                "because the "
                                "scan identified "
                                "dataset "
                                "'dataset'.",
                                "evidence_kinds": ["code_context"],
                                "evidence_locations": [
                                    {
                                        "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/declarative_schema/fetcher.py",
                                        "start_line": 497,
                                        "end_line": 497,
                                        "role": "primary",
                                    }
                                ],
                                "code_snippet": None,
                            },
                            "metadata": {
                                "evidence": [
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/declarative_schema/fetcher.py",
                                        "line": 507,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app",
                                        "test_only": False,
                                    },
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/declarative_schema/fetcher.py",
                                        "line": 605,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app",
                                        "test_only": False,
                                    },
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/external/cartography/tests/data/gcp/vertex.py",
                                        "line": 132,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/external/cartography",
                                        "test_only": True,
                                    },
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/external/cartography/tests/data/aws/bedrock/__init__.py",
                                        "line": 231,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/external/cartography",
                                        "test_only": True,
                                    },
                                ],
                                "evidence_count": 5,
                                "evidence_files": [
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/declarative_schema/fetcher.py",
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/external/cartography/tests/data/gcp/vertex.py",
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/external/cartography/tests/data/aws/bedrock/__init__.py",
                                ],
                                "consolidated_count": 5,
                            },
                            "instance_id": "dataset_/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/declarative_schema/fetcher.py_497",
                            "confidence": 0.3,
                        }
                    ],
                    "skill": [
                        {
                            "name": "AGENTS.md: Cartography Intel Module Development "
                            "Guide",
                            "component_type": "skill",
                            "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/external/cartography/AGENTS.md",
                            "line_number": 0,
                            "framework": "",
                            "detection_source": "config_file",
                            "heuristic_confidence": 1.0,
                            "agentic_confidence": None,
                            "needs_agentic": True,
                            "agentic_hint": "",
                            "model_name": None,
                            "embedding_model": None,
                            "description": "> **For AI Coding Assistants**: This "
                            "document provides comprehensive guidance "
                            "for understanding and developing "
                            "Cartography intel modules. It contains "
                            "codebase-specific patterns, architectural "
                            "decis...",
                            "text": None,
                            "transport": None,
                            "config_source": None,
                            "storage_uri": None,
                            "dataset_source": None,
                            "skill_format": "agents_md",
                            "hyperparameters": {},
                            "training_info": None,
                            "metrics": {},
                            "kb_concept": "cartography-intel-modules",
                            "kb_label": "Cartography Intel Module Development Guide",
                            "sdk_version": None,
                            "decision_annotation": {
                                "decision": "confirmed",
                                "justification": "Kept in the final "
                                "AIBOM because the "
                                "scan identified "
                                "skill 'AGENTS.md: "
                                "Cartography Intel "
                                "Module "
                                "Development "
                                "Guide'.",
                                "evidence_kinds": ["code_context"],
                                "evidence_locations": [
                                    {
                                        "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/external/cartography/AGENTS.md",
                                        "start_line": 1,
                                        "end_line": 1,
                                        "role": "primary",
                                    }
                                ],
                                "code_snippet": None,
                            },
                            "metadata": {
                                "trigger_patterns": [],
                                "file_count": 1,
                                "files": ["AGENTS.md"],
                                "evidence_count": 1,
                                "evidence_files": [
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/external/cartography/AGENTS.md"
                                ],
                            },
                            "instance_id": "AGENTS.md: Cartography Intel Module "
                            "Development "
                            "Guide_/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/external/cartography/AGENTS.md_0",
                            "confidence": 1.0,
                        }
                    ],
                    "model": [
                        {
                            "name": "gpt-5.2",
                            "component_type": "model",
                            "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sub_agents/query/agent.py",
                            "line_number": 39,
                            "framework": "openai",
                            "detection_source": "agentic",
                            "heuristic_confidence": 1.0,
                            "agentic_confidence": None,
                            "needs_agentic": True,
                            "agentic_hint": "",
                            "model_name": "gpt-5.2",
                            "embedding_model": None,
                            "description": None,
                            "text": None,
                            "transport": None,
                            "config_source": None,
                            "storage_uri": None,
                            "dataset_source": None,
                            "skill_format": None,
                            "hyperparameters": {},
                            "training_info": None,
                            "metrics": {},
                            "kb_concept": None,
                            "kb_label": None,
                            "sdk_version": None,
                            "decision_annotation": {
                                "decision": "added",
                                "justification": "A concrete model "
                                "identifier is "
                                "passed to "
                                "OpenAIChatModel "
                                "in the query "
                                "agent definition, "
                                "so it belongs in "
                                "the AIBOM as the "
                                "model used by "
                                "this agent.",
                                "evidence_kinds": ["code_context", "registry_lookup"],
                                "evidence_locations": [
                                    {
                                        "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sub_agents/query/agent.py",
                                        "start_line": 39,
                                        "end_line": 41,
                                        "role": "primary",
                                    }
                                ],
                                "code_snippet": None,
                            },
                            "metadata": {
                                "model_provider": "openai",
                                "license": "proprietary",
                                "deprecated": False,
                                "model_card_url": "https://platform.openai.com/docs/models",
                                "context_length": 400000,
                                "evidence": [
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/chat_v2/tools.py",
                                        "line": 91,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app",
                                        "test_only": False,
                                    },
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/chat_v2/tools.py",
                                        "line": 92,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app",
                                        "test_only": False,
                                    },
                                    {
                                        "file": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sub_agents/vuln_fix/agent.py",
                                        "line": 50,
                                        "service": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app",
                                        "test_only": False,
                                    },
                                ],
                                "evidence_count": 4,
                                "evidence_files": [
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/chat_v2/tools.py",
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sub_agents/query/agent.py",
                                    "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sub_agents/vuln_fix/agent.py",
                                ],
                                "consolidated_count": 4,
                            },
                            "instance_id": "gpt-5.2_/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sub_agents/query/agent.py_39",
                            "confidence": 1.0,
                        }
                    ],
                },
                "relationships": [
                    {
                        "source_instance_id": "",
                        "target_instance_id": "",
                        "relationship_type": "USES_MODEL",
                        "label": "USES_MODEL",
                        "source_name": "Agent",
                        "target_name": "gpt-5.2",
                        "source_type": "agent",
                        "target_type": "model",
                        "source_repo": "",
                        "target_repo": "",
                        "decision_annotation": {
                            "decision": "derived",
                            "justification": "The chat agent is "
                            "instantiated with an "
                            "OpenAIChatModel "
                            "configured to use "
                            "gpt-5.2.",
                            "evidence_kinds": [
                                "relationship_context",
                                "code_context",
                                "registry_lookup",
                            ],
                            "evidence_locations": [
                                {
                                    "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/chat_v2/tools.py",
                                    "start_line": 91,
                                    "end_line": 103,
                                    "role": "source",
                                }
                            ],
                            "code_snippet": None,
                        },
                    }
                ],
                "summary": {
                    "status": "completed",
                    "source_kind": "container",
                    "assets_discovered": 53,
                    "last_generated_at": "2026-05-18T22:19:12Z",
                },
                "metadata": {
                    "elapsed_s": 2285.77,
                    "prompt_tokens": 6659670,
                    "completion_tokens": 69412,
                    "total_tokens": 6729082,
                },
            },
        },
        "summary": {
            "total_sources": 1,
            "total_components": 53,
            "pending_agent_review": 53,
            "test_only_components": 0,
            "component_types": {
                "secret": 3,
                "dependency": 9,
                "mcp_server": 6,
                "tool": 27,
                "agent": 1,
                "dataset": 1,
                "skill": 3,
                "model": 3,
            },
            "total_relationships": 20,
            "risk_score": 100,
            "risk_severity": "critical",
        },
        "risk": {
            "score": 100,
            "severity": "critical",
            "flags": [
                {
                    "flag": "hardcoded_api_key",
                    "severity": "high",
                    "weight": 35,
                    "description": "Hardcoded AI API key detected in source code",
                    "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sync/modules/gitlab.py",
                    "line_number": 394,
                    "decision_annotation": {
                        "decision": "flagged",
                        "justification": "Hardcoded AI API key detected in "
                        "source code",
                        "evidence_kinds": ["code_context"],
                        "evidence_locations": [
                            {
                                "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sync/modules/gitlab.py",
                                "start_line": 394,
                                "end_line": 394,
                                "role": "primary",
                            }
                        ],
                        "code_snippet": None,
                    },
                    "metadata": {},
                },
                {
                    "flag": "hardcoded_api_key",
                    "severity": "high",
                    "weight": 35,
                    "description": "Hardcoded AI API key detected in source code",
                    "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/.env.local.example",
                    "line_number": 10,
                    "decision_annotation": {
                        "decision": "flagged",
                        "justification": "Hardcoded AI API key detected in "
                        "source code",
                        "evidence_kinds": ["code_context"],
                        "evidence_locations": [
                            {
                                "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/.env.local.example",
                                "start_line": 10,
                                "end_line": 10,
                                "role": "primary",
                            }
                        ],
                        "code_snippet": None,
                    },
                    "metadata": {},
                },
                {
                    "flag": "hardcoded_api_key",
                    "severity": "high",
                    "weight": 35,
                    "description": "Hardcoded AI API key detected in source code",
                    "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/.env.local.example",
                    "line_number": 13,
                    "decision_annotation": {
                        "decision": "flagged",
                        "justification": "Hardcoded AI API key detected in "
                        "source code",
                        "evidence_kinds": ["code_context"],
                        "evidence_locations": [
                            {
                                "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/.env.local.example",
                                "start_line": 13,
                                "end_line": 13,
                                "role": "primary",
                            }
                        ],
                        "code_snippet": None,
                    },
                    "metadata": {},
                },
                {
                    "flag": "unpinned_model",
                    "severity": "low",
                    "weight": 10,
                    "description": "Model version not pinned to a specific release",
                    "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/chat_v2/service.py",
                    "line_number": 95,
                    "decision_annotation": {
                        "decision": "flagged",
                        "justification": "Model version not pinned to a "
                        "specific release",
                        "evidence_kinds": ["code_context"],
                        "evidence_locations": [
                            {
                                "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/chat_v2/service.py",
                                "start_line": 95,
                                "end_line": 95,
                                "role": "primary",
                            }
                        ],
                        "code_snippet": None,
                    },
                    "metadata": {},
                },
                {
                    "flag": "unpinned_model",
                    "severity": "low",
                    "weight": 10,
                    "description": "Model version not pinned to a specific release",
                    "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sub_agents/cloud_cli/agent.py",
                    "line_number": 29,
                    "decision_annotation": {
                        "decision": "flagged",
                        "justification": "Model version not pinned to a "
                        "specific release",
                        "evidence_kinds": ["code_context"],
                        "evidence_locations": [
                            {
                                "file_path": "/private/var/folders/r9/q5vn3m2x30b2bv81r550cp_c0000gn/T/aibom_container_81p0fq2h/app/app/sub_agents/cloud_cli/agent.py",
                                "start_line": 29,
                                "end_line": 29,
                                "role": "primary",
                            }
                        ],
                        "code_snippet": None,
                    },
                    "metadata": {},
                },
            ],
        },
        "errors": [],
    },
}

# Code-repository anchors used by the GitHub/GitLab linking tests. AIBOM source
# keys for repository scans are plain repo URLs with no `@sha256:` digest.
TEST_GITHUB_REPO_URL = "https://github.com/example-org/example-repo"
TEST_GITLAB_PROJECT_URL = "https://gitlab.com/example-group/example-project"


def build_repo_anchored_report(source_key: str) -> dict[str, Any]:
    """
    Return a copy of ``AIBOM_REPORT`` re-anchored on a code-repository source
    key (a plain repo URL) instead of the digest-qualified image source key.
    """
    report: dict[str, Any] = copy.deepcopy(AIBOM_REPORT)
    sources: dict[str, Any] = report["aibom_analysis"]["sources"]
    source_data = sources.pop(TEST_SOURCE_KEY)
    source_data["source_name"] = source_key
    sources[source_key] = source_data
    return report
