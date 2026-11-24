FAKE_DEPLOYMENT_ID = "FAKE-DEPLOYMENT-ID-123"
FAKE_WEB_APP_URL = f"https://script.google.com/macros/s/{FAKE_DEPLOYMENT_ID}/exec"

# Project 1: HEAD-only anonymous web app (no versionNumber -> must not count)
PROJECT_HEAD_ONLY = {
    "scriptId": "script-head-only-1",
    "title": "Head Only Script",
    "parentId": "folder-parent-1",
    "createTime": "2024-01-10T00:00:00Z",
    "updateTime": "2024-01-11T00:00:00Z",
    "creator": {
        "domain": "simpson.corp",
        "email": "mbsimpson@simpson.corp",
        "name": "Marge Simpson",
    },
    "lastModifyUser": {
        "domain": "simpson.corp",
        "email": "mbsimpson@simpson.corp",
        "name": "Marge Simpson",
    },
}

DEPLOYMENTS_HEAD_ONLY = [
    {
        "deploymentId": "FAKE-DEPLOYMENT-HEAD-1",
        "updateTime": "2024-01-11T00:00:00Z",
        "deploymentConfig": {
            "scriptId": "script-head-only-1",
            "manifestFileName": "appsscript",
            "description": "HEAD deployment",
        },
        "entryPoints": [
            {
                "entryPointType": "WEB_APP",
                "webApp": {
                    "url": "https://script.google.com/macros/s/FAKE-DEPLOYMENT-HEAD-1/dev",
                    "entryPointConfig": {
                        "access": "ANYONE_ANONYMOUS",
                        "executeAs": "USER_DEPLOYING",
                    },
                },
            }
        ],
    }
]

# Project 2: Versioned ANYONE_ANONYMOUS + USER_DEPLOYING web app
PROJECT_ANON_OWNER = {
    "scriptId": "script-anon-owner-2",
    "title": "Public Webhook",
    "createTime": "2024-02-01T00:00:00Z",
    "updateTime": "2024-02-02T00:00:00Z",
    "creator": {
        "domain": "simpson.corp",
        "email": "mbsimpson@simpson.corp",
        "name": "Marge Simpson",
    },
}

DEPLOYMENTS_ANON_OWNER = [
    {
        "deploymentId": FAKE_DEPLOYMENT_ID,
        "updateTime": "2024-02-02T00:00:00Z",
        "deploymentConfig": {
            "scriptId": "script-anon-owner-2",
            "manifestFileName": "appsscript",
            "versionNumber": 3,
            "description": "Production webhook",
        },
        "entryPoints": [
            {
                "entryPointType": "WEB_APP",
                "webApp": {
                    "url": FAKE_WEB_APP_URL,
                    "entryPointConfig": {
                        "access": "ANYONE_ANONYMOUS",
                        "executeAs": "USER_DEPLOYING",
                    },
                },
            }
        ],
    }
]

# Project 3: Versioned DOMAIN + USER_ACCESSING web app
PROJECT_DOMAIN_USER = {
    "scriptId": "script-domain-user-3",
    "title": "Internal Tool",
    "createTime": "2024-03-01T00:00:00Z",
    "updateTime": "2024-03-02T00:00:00Z",
    "creator": {
        "domain": "simpson.corp",
        "email": "hjsimpson@simpson.corp",
        "name": "Homer Simpson",
    },
}

DEPLOYMENTS_DOMAIN_USER = [
    {
        "deploymentId": "FAKE-DEPLOYMENT-DOMAIN-3",
        "updateTime": "2024-03-02T00:00:00Z",
        "deploymentConfig": {
            "scriptId": "script-domain-user-3",
            "manifestFileName": "appsscript",
            "versionNumber": 1,
        },
        "entryPoints": [
            {
                "entryPointType": "WEB_APP",
                "webApp": {
                    "url": "https://script.google.com/macros/s/FAKE-DEPLOYMENT-DOMAIN-3/exec",
                    "entryPointConfig": {
                        "access": "DOMAIN",
                        "executeAs": "USER_ACCESSING",
                    },
                },
            }
        ],
    }
]

# Project 4: Two versioned web apps of different access + an EXECUTION_API entry point
PROJECT_MULTI_DEPLOY = {
    "scriptId": "script-multi-deploy-4",
    "title": "Multi Deployment App",
    "createTime": "2024-04-01T00:00:00Z",
    "updateTime": "2024-04-02T00:00:00Z",
    "creator": {
        "domain": "simpson.corp",
        "email": "hjsimpson@simpson.corp",
        "name": "Homer Simpson",
    },
}

DEPLOYMENTS_MULTI_DEPLOY = [
    {
        "deploymentId": "FAKE-DEPLOYMENT-MULTI-4A",
        "updateTime": "2024-04-01T00:00:00Z",
        "deploymentConfig": {
            "scriptId": "script-multi-deploy-4",
            "manifestFileName": "appsscript",
            "versionNumber": 1,
        },
        "entryPoints": [
            {
                "entryPointType": "WEB_APP",
                "webApp": {
                    "url": "https://script.google.com/macros/s/FAKE-DEPLOYMENT-MULTI-4A/exec",
                    "entryPointConfig": {
                        "access": "MYSELF",
                        "executeAs": "USER_DEPLOYING",
                    },
                },
            },
            {
                "entryPointType": "EXECUTION_API",
                "executionApi": {
                    "entryPointConfig": {
                        "access": "DOMAIN",
                    },
                },
            },
        ],
    },
    {
        "deploymentId": "FAKE-DEPLOYMENT-MULTI-4B",
        "updateTime": "2024-04-02T00:00:00Z",
        "deploymentConfig": {
            "scriptId": "script-multi-deploy-4",
            "manifestFileName": "appsscript",
            "versionNumber": 2,
        },
        "entryPoints": [
            {
                "entryPointType": "WEB_APP",
                "webApp": {
                    "url": "https://script.google.com/macros/s/FAKE-DEPLOYMENT-MULTI-4B/exec",
                    "entryPointConfig": {
                        "access": "ANYONE",
                        "executeAs": "USER_ACCESSING",
                    },
                },
            },
        ],
    },
]

# Project 5: No deployments
PROJECT_NO_DEPLOYMENTS = {
    "scriptId": "script-no-deploy-5",
    "title": "Draft Script",
    "createTime": "2024-05-01T00:00:00Z",
    "updateTime": "2024-05-01T00:00:00Z",
    "creator": {
        "domain": "simpson.corp",
        "email": "mbsimpson@simpson.corp",
        "name": "Marge Simpson",
    },
}

DEPLOYMENTS_NONE: list[dict] = []
