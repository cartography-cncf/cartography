AI_SAST_FINDING_ID = 81234501

AI_SAST_RESPONSE = {
    "findings": [
        {
            "id": AI_SAST_FINDING_ID,
            "ref": "main",
            "syntactic_id": "11223344556677889900aabbccddeeff",
            "match_based_id": "0f8c79a6f7e0ff2f908ff5bc366ae1548465069bae8892088051e1c3b4b12c6b_0",
            "repository": {
                "name": "simpsoncorp/sample_repo",
                "url": "https://github.com/simpsoncorp/sample_repo",
            },
            "line_of_code_url": "https://github.com/simpsoncorp/sample_repo/blob/71bbed12f950de8335006d7f91112263d8504f1b/src/api/orders.py#L17",
            "first_seen_scan_id": 30469990,
            "state": "unresolved",
            "triage_state": "untriaged",
            "status": "open",
            "confidence": "medium",
            "created_at": "2025-01-15T09:30:00.000000Z",
            "relevant_since": "2025-01-15T09:30:00.000000Z",
            "rule_name": "ai.detection.idor",
            "rule_message": "Deprecated message.",
            "ai_impact": "An attacker could access or modify other users' orders by manipulating the order identifier in the request.",
            "location": {
                "file_path": "src/api/orders.py",
                "line": 17,
                "column": 5,
                "end_line": 19,
                "end_column": 30,
            },
            "triaged_at": None,
            "triage_comment": None,
            "triage_reason": None,
            "state_updated_at": None,
            "rule": {
                "name": "ai.detection.idor",
                "message": "Insecure direct object reference: the order is fetched by a user-supplied ID without an ownership check.",
                "confidence": "medium",
                "category": "security",
                "subcategories": ["vuln"],
                "vulnerability_classes": ["Insecure Direct Object Reference (IDOR)"],
                "cwe_names": [
                    "CWE-639: Authorization Bypass Through User-Controlled Key",
                ],
                "owasp_names": ["A01:2021 - Broken Access Control"],
            },
            "severity": "high",
            "assistant": {
                "autofix": {
                    "fix_code": "order = Order.objects.get(id=order_id, owner=request.user)",
                    "explanation": "",
                },
                "autotriage": {
                    "verdict": "true_positive",
                    "reason": "",
                },
                "component": {
                    "tag": "user data",
                    "risk": "high",
                },
                "guidance": {
                    "summary": "Scope the query to the authenticated user.",
                    "instructions": "Filter the order lookup by the requesting user before returning it.",
                },
                "rule_explanation": {
                    "summary": "Order fetched without an ownership check",
                    "explanation": "The handler loads an order by ID taken from the request without verifying it belongs to the caller.",
                },
            },
        },
    ],
}

RAW_FINDINGS = AI_SAST_RESPONSE["findings"]
