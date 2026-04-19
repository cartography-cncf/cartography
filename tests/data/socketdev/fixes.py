FIXES_RESPONSE = {
    "fixDetails": {
        "CVE-2024-0001": {
            "type": "fixFound",
            "value": {
                "ghsa": "GHSA-xxxx-yyyy-zzzz",
                "cve": "CVE-2024-0001",
                "advisoryDetails": None,
                "fixDetails": {
                    "fixes": [
                        {
                            "purl": "pkg:npm/lodash@4.17.21",
                            "fixedVersion": "4.17.22",
                            "manifestFiles": ["package.json"],
                            "updateType": "patch",
                        },
                    ],
                },
            },
        },
    },
}
