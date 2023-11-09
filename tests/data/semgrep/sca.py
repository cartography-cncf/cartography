DEPLOYMENTS = {
    "id": "123456",
    "name": "YourOrg",
    "slug": "yourorg",
}

SCA_RESPONSE = {
    "vulns": [
        {
            "title": "Reachable vuln",
            "advisory": {
                "ruleId": "ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590",
                "title": "Reachable vuln",
                "description": "description",
                "ecosystem": "go",
                "severity": "HIGH",
                "references": {
                    "cveIds": ["CVE-2023-37897"],
                    "cweIds": ["CWE-617: Reachable Assertion"],
                    "owaspIds": ["A06:2021 - Vulnerable and Outdated Components"],
                    "urls": [
                        "https://github.com/advisories//GHSA-9436-3gmp-4f53",
                        "https://nvd.nist.gov/vuln/detail/CVE-2023-37897",
                    ],
                },
                "announcedAt": "2023-07-19T21:15:08Z",
                "ruleText": '{\n  "id": "ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590",\n  "languages": [\n    "python",\n    "java",\n    "ruby"\n  ],\n  "message": "message ",\n }',  # noqa E501
                "reachability": "MANUAL_REVIEW_REACHABLE",
                "vulnerableDependencies": [
                    {"name": "grav", "versionSpecifier": "<  1.7.42.1"},
                ],
                "safeDependencies": [
                    {"name": "grav", "versionSpecifier": "1.7.42.2"},
                ],
                "reachableIf": "a non-administrator, user account that has Admin panel access and Create/Update page permissions",  # noqa E501
            },
            "exposureType": "REACHABLE",
            "repositoryId": "123456",
            "matchedDependency": {"name": "grav", "versionSpecifier": "1.7.42.0"},
            "dependencyFileLocation": {
                "path": "go.mod",
                "startLine": "111",
                "url": "https://github.com/yourorg/yourrepo/blame/71bbed12f950de8335006d7f91112263d8504f1b/go.mod#L111",
                "startCol": "0",
                "endLine": "0",
                "endCol": "0",
            },
            "usages": [
                {
                    "findingId": "20128504",
                    "location": {
                        "path": "src/packages/directory/file1.go",
                        "startLine": "24",
                        "startCol": "57",
                        "endLine": "24",
                        "endCol": "78",
                        "url": "https://github.com/yourorg/yourrepo/blame/6fdee8f2727f4506cfbbe553e23b895e27956588/src/packages/directory/file1.go.ts#L24",  # noqa E501
                        "committedAt": "1970-01-01T00:00:00Z",
                    },
                },
                {
                    "findingId": "20128505",
                    "location": {
                        "path": "src/packages/directory/file2.go",
                        "startLine": "24",
                        "startCol": "37",
                        "endLine": "24",
                        "endCol": "54",
                        "url": "https://github.com/yourorg/yourrepo/blame/6fdee8f2727f4506cfbbe553e23b895e27956588/src/packages/directory/file2.go.ts#L24",  # noqa E501
                        "committedAt": "1970-01-01T00:00:00Z",
                    },
                },
            ],
            "triage": {
                "status": "NEW",
                "dismissReason": "UNKNOWN_REASON",
                "issueUrl": "",
                "prUrl": "",
            },
            "groupKey": "132465::::ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590::reachable",
            "closestSafeDependency": {"name": "grav", "versionSpecifier": "1.7.42.2"},
            "repositoryName": "yourorg/yourrepo",
            "openedAt": "2023-07-19T12:51:53Z",
            "firstTriagedAt": "1970-01-01T00:00:00Z",
            "transitivity": "DIRECT",
            "subdirectory": "",
            "packageManager": "no_package_manager",
        },
    ],
    "hasMore": True,
    "cursor": {
        "vulnOffset": "1",
        "issueOffset": "19311309",
    },
}

RAW_VULNS = SCA_RESPONSE["vulns"]
VULN_ID = "yourorg/yourrepo|ssc-92af1d99-4fb3-4d4e-a9f4-d57572cd6590"
USAGES = [
                {
                    "SCA_ID": VULN_ID,
                    "findingId": "20128504",
                    "path": "src/packages/directory/file1.go",
                    "startLine": "24",
                    "startCol": "57",
                    "endLine": "24",
                    "endCol": "78",
                    "url": "https://github.com/yourorg/yourrepo/blame/6fdee8f2727f4506cfbbe553e23b895e27956588/src/packages/directory/file1.go.ts#L24",  # noqa E501
                },
                {
                    "SCA_ID": VULN_ID,
                    "findingId": "20128505",
                    "path": "src/packages/directory/file2.go",
                    "startLine": "24",
                    "startCol": "37",
                    "endLine": "24",
                    "endCol": "54",
                    "url": "https://github.com/yourorg/yourrepo/blame/6fdee8f2727f4506cfbbe553e23b895e27956588/src/packages/directory/file2.go.ts#L24",  # noqa E501
                },
]
