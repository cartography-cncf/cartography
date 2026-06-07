SAST_FINDING_ID = 73537200

SAST_RESPONSE = {
    "findings": [
        {
            "id": SAST_FINDING_ID,
            "ref": "main",
            "syntactic_id": "aabbccdd11223344556677889900aabb",
            "match_based_id": "aabbccdd11223344556677889900aabbccdd11223344556677889900aabbccdd11223344556677889900",
            "repository": {
                "name": "simpsoncorp/sample_repo",
                "url": "https://github.com/simpsoncorp/sample_repo",
            },
            "line_of_code_url": "https://github.com/simpsoncorp/sample_repo/blob/71bbed12f950de8335006d7f91112263d8504f1b/src/api/auth.py#L42",
            "first_seen_scan_id": 30469983,
            "state": "unresolved",
            "triage_state": "untriaged",
            "status": "open",
            "confidence": "high",
            "created_at": "2024-08-01T10:00:00.000000Z",
            "relevant_since": "2024-08-01T10:00:00.000000Z",
            "rule_name": "python.lang.security.audit.sqli.formatted-sql-query",
            "rule_message": "Detected SQL statement that is tainted by `request` object. This could lead to SQL injection if the variable is user-controlled and not properly sanitized.",
            "location": {
                "file_path": "src/api/auth.py",
                "line": 42,
                "column": 10,
                "end_line": 42,
                "end_column": 65,
            },
            "triaged_at": None,
            "triage_comment": None,
            "triage_reason": None,
            "state_updated_at": None,
            "categories": ["security"],
            "rule": {
                "name": "python.lang.security.audit.sqli.formatted-sql-query",
                "message": "Detected SQL statement that is tainted by `request` object. This could lead to SQL injection if the variable is user-controlled and not properly sanitized.",
                "confidence": "high",
                "category": "security",
                "subcategories": ["vuln"],
                "vulnerability_classes": ["SQL Injection"],
                "cwe_names": [
                    "CWE-89: Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection')",
                ],
                "owasp_names": ["A03:2021 - Injection"],
            },
            "severity": "high",
            "assistant": {
                "autofix": {
                    "fix_code": "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
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
                    "summary": "Use parameterized queries instead of string concatenation.",
                    "instructions": "Replace the string-formatted SQL with a parameterized query using %s placeholders and pass user-controlled values as a separate argument to cursor.execute().",
                },
                "rule_explanation": {
                    "summary": "User input directly concatenated into SQL query",
                    "explanation": "This code is vulnerable to SQL injection because user input from the `user_id` parameter is directly concatenated into the SQL query string without sanitization or parameterization.",
                },
            },
        },
    ],
}

RAW_FINDINGS = SAST_RESPONSE["findings"]
