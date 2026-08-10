# Shape returned by artifact_allowlists.get(): one entry per artifact type,
# with the queried type injected under "artifact_type".
DATABRICKS_ARTIFACT_ALLOWLISTS = [
    {
        "artifact_type": "INIT_SCRIPT",
        "artifact_matchers": [
            {
                "artifact": "/Volumes/prod/finance/landing/",
                "match_type": "PREFIX_MATCH",
            },
        ],
        "created_at": 1782835899900,
        "created_by": "admin@subimage.io",
    },
    {
        "artifact_type": "LIBRARY_MAVEN",
        "artifact_matchers": [
            {"artifact": "org.example:lib", "match_type": "PREFIX_MATCH"},
        ],
        "created_at": 1782835899900,
        "created_by": "admin@subimage.io",
    },
]
