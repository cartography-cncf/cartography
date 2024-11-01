REPO_ID = "123456"

DEPENDENCIES_RESPONSE = {
    "dependencies": [
        {
            "repositoryId": REPO_ID,
            "definedAt": {
                "path": "go.mod",
                "startLine": "6",
                "endLine": "6",
                "url": "https://github.com/org/repository/blob/00000000000000000000000000000000/go.mod#L6",
                "committedAt": "1970-01-01T00:00:00Z",
                "startCol": "0",
                "endCol": "0",
            },
            "transitivity": "DIRECT",
            "package": {
                "name": "github.com/foo/baz",
                "versionSpecifier": "1.2.3",
            },
            "ecosystem": "gomod",
            "licenses": [
                "MIT",
            ],
            "pathToTransitivity": [],
        },
        {
            "repositoryId": REPO_ID,
            "definedAt": {
                "path": "go.mod",
                "startLine": "7",
                "endLine": "7",
                "url": "https://github.com/org/repository/blob/00000000000000000000000000000000/go.mod#L7",
                "committedAt": "1970-01-01T00:00:00Z",
                "startCol": "0",
                "endCol": "0",
            },
            "transitivity": "TRANSITIVE",
            "package": {
                "name": "github.com/foo/buzz",
                "versionSpecifier": "4.5.0",
            },
            "ecosystem": "gomod",
            "licenses": [
                "MIT",
            ],
            "pathToTransitivity": [],
        },
    ],
    "hasMore": True,
    "cursor": "123456789",
}

RAW_DEPS = DEPENDENCIES_RESPONSE["dependencies"]
