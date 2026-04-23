FIXES_RESPONSE = {
    "fixDetails": {
        "GHSA-xxxx-yyyy-zzzz": {
            "type": "fixFound",
            "value": {
                "ghsa": "GHSA-xxxx-yyyy-zzzz",
                "cve": None,
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
