VULN_ID = 73537136
USAGE_ID = hash(
    "org/repository/blob/commit_id/src/packages/linked-accounts/components/LinkedAccountsTable/constants.tsx#L274",
)

SCA_RESPONSE = {
    "findings": [
        {
            "id": VULN_ID,
            "ref": "main",
            "syntactic_id": "91f6bebf5c374b3db9ae6b0afeb8ba4f",
            "match_based_id": "cf89274a455b0f7dae15d218af143cf317fb9886d12f3dcbe0e37cad02d0d29411cecb9a2c3fedc9e973de",
            "repository": {
                "name": "org/repository",
                "url": "https: //github.com/org/repository",
            },
            "line_of_code_url": "https: //github.com/org/repository/blob/71bbed12f950de8335006d7f91112263d8504f1b/src/packages/components/AccountsTable/constants.tsx#L274",  # noqa E501
            "first_seen_scan_id": 30469982,
            "state": "unresolved",
            "triage_state": "untriaged",
            "status": "open",
            "confidence": "high",
            "created_at": "2024-07-11T20:46:25.269650Z",
            "relevant_since": "2024-07-11T20:46:25.268845Z",
            "rule_name": "ssc-1e99e462-0fc5-4109-ad52-d2b5a7048232",
            "rule_message": "description",
            "location": {
                "file_path": "src/packages/linked-accounts/components/LinkedAccountsTable/constants.tsx",
                "line": 274,
                "column": 37,
                "end_line": 274,
                "end_column": 62,
            },
            "triaged_at": None,
            "triage_comment": None,
            "triage_reason": None,
            "state_updated_at": None,
            "categories": ["security"],
            "rule": {
                "name": "ssc-1e99e462-0fc5-4109-ad52-d2b5a7048232",
                "message": "description",
                "confidence": "high",
                "category": "security",
                "subcategories": [],
                "vulnerability_classes": ["Denial-of-Service (DoS)"],
                "cwe_names": [
                    "CWE-1333: Inefficient Regular Expression Complexity",
                    "CWE-400: Uncontrolled Resource Consumption",
                ],
                "owasp_names": ["A06: 2021 - Vulnerable and Outdated Components"],
            },
            "severity": "high",
            "vulnerability_identifier": "CVE-2022-31129",
            "reachability": "reachable",
            "reachable_condition": None,
            "found_dependency": {
                "package": "moment",
                "version": "2.29.2",
                "ecosystem": "npm",
                "transitivity": "direct",
                "lockfile_line_url": "https: //github.com/org/repository/blob/commit_id/package-lock.json#L14373",
            },
            "fix_recommendations": [{"package": "moment", "version": "2.29.4"}],
            "usage": {
                "location": {
                    "path": "src/packages/linked-accounts/components/LinkedAccountsTable/constants.tsx",
                    "start_line": 274,
                    "start_col": 37,
                    "end_line": 274,
                    "end_col": 62,
                    "url": "https: //github.com/org/repository/blob/commit_id/src/packages/linked-accounts/components/LinkedAccountsTable/constants.tsx#L274",  # noqa E501
                },
                "external_ticket": None,
            },
        },
    ],
}

RAW_VULNS = SCA_RESPONSE["findings"]

USAGES = [
    {
        "SCA_ID": VULN_ID,
        "findingId": USAGE_ID,
        "path": "src/packages/linked-accounts/components/LinkedAccountsTable/constants.tsx",
        "start_line": 274,
        "start_col": 37,
        "end_line": 274,
        "end_col": 62,
        "url": "https: //github.com/org/repository/blob/commit_id/src/packages/linked-accounts/components/LinkedAccountsTable/constants.tsx#L274",  # noqa E501
    },
]
