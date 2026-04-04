JFROG_REPOSITORIES = [
    {
        "key": "docker-prod",
        "type": "LOCAL",
        "url": "https://example.jfrog.io/artifactory/docker-prod",
        "packageType": "Docker",
        "description": "Production docker images",
        "projectKey": "PRJ",
        "rclass": "local",
    },
    {
        "key": "maven-remote",
        "type": "REMOTE",
        "url": "https://example.jfrog.io/artifactory/maven-remote",
        "packageType": "Maven",
        "description": "Remote Maven cache",
        "projectKey": "PRJ",
        "rclass": "remote",
    },
]
