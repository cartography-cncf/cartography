"""
A whole-project bundle captured from the Railway public API (the `ProjectBundle` document in
cartography/intel/railway/queries.py), with identifiers replaced by stable fakes.

Kept in raw GraphQL shape - Relay `edges`/`node` wrappers and nested `source` / `status`
objects intact - because unwrapping and flattening those is what the transforms do.

Four things are hand-added, since a throwaway Hobby project cannot produce them:
  * custom domains, which need a real domain plus DNS verification (one verified, one not);
  * a git source and root directory on one service instance, to exercise source context;
  * deployment commit metadata, including a malformed value to exercise validation;
  * a deployment trigger, which requires a linked GitHub account.
Everything else is exactly what the live API returned.
"""

from typing import Any

RAILWAY_PROJECT_BUNDLE: dict[str, Any] = {
    "createdAt": "2026-07-27T18:00:44.634Z",
    "deletedAt": None,
    "description": None,
    "environments": {
        "edges": [
            {
                "node": {
                    "createdAt": "2026-07-27T18:01:14.104Z",
                    "deploymentTriggers": {
                        "edges": [],
                        "pageInfo": {"endCursor": None, "hasNextPage": False},
                    },
                    "deployments": {
                        "edges": [],
                        "pageInfo": {"endCursor": None, "hasNextPage": False},
                    },
                    "id": "55555555-5555-5555-5555-555555555555",
                    "isEphemeral": False,
                    "name": "staging",
                    "projectId": "33333333-3333-3333-3333-333333333333",
                    "serviceInstances": {
                        "edges": [],
                        "pageInfo": {"endCursor": None, "hasNextPage": False},
                    },
                    "variables": {
                        "edges": [],
                        "pageInfo": {"endCursor": None, "hasNextPage": False},
                    },
                    "volumeInstances": {
                        "edges": [],
                        "pageInfo": {"endCursor": None, "hasNextPage": False},
                    },
                }
            },
            {
                "node": {
                    "createdAt": "2026-07-27T18:00:44.708Z",
                    "deploymentTriggers": {
                        "edges": [
                            {
                                "node": {
                                    "id": "dt111111-1111-1111-1111-111111111111",
                                    "provider": "github",
                                    "repository": "acme/api",
                                    "branch": "main",
                                    "serviceId": "77777777-7777-7777-7777-777777777777",
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                }
                            }
                        ],
                        "pageInfo": {"endCursor": None, "hasNextPage": False},
                    },
                    "deployments": {
                        "edges": [
                            {
                                "node": {
                                    "canRedeploy": True,
                                    "createdAt": "2026-07-27T18:02:21.021Z",
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                                    "meta": {
                                        "commitHash": "0123456789ABCDEF0123456789ABCDEF01234567",
                                    },
                                    "projectId": "33333333-3333-3333-3333-333333333333",
                                    "serviceId": "77777777-7777-7777-7777-777777777777",
                                    "staticUrl": None,
                                    "status": "SUCCESS",
                                    "statusUpdatedAt": "2026-07-27T18:02:26.300Z",
                                    "url": None,
                                }
                            },
                            {
                                "node": {
                                    "canRedeploy": True,
                                    "createdAt": "2026-07-27T18:01:57.350Z",
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                                    "meta": {"commitHash": "main"},
                                    "projectId": "33333333-3333-3333-3333-333333333333",
                                    "serviceId": "66666666-6666-6666-6666-666666666666",
                                    "staticUrl": "web-production-abcde.up.railway.app",
                                    "status": "SUCCESS",
                                    "statusUpdatedAt": "2026-07-27T18:02:04.313Z",
                                    "url": None,
                                }
                            },
                        ],
                        "pageInfo": {"endCursor": "CURSOR", "hasNextPage": False},
                    },
                    "id": "44444444-4444-4444-4444-444444444444",
                    "isEphemeral": False,
                    "name": "production",
                    "projectId": "33333333-3333-3333-3333-333333333333",
                    "serviceInstances": {
                        "edges": [
                            {
                                "node": {
                                    "buildCommand": None,
                                    "builder": "RAILPACK",
                                    "createdAt": "2026-07-27T18:02:19.791Z",
                                    "cronSchedule": None,
                                    "dockerfilePath": None,
                                    "domains": {
                                        "customDomains": [],
                                        "serviceDomains": [],
                                    },
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "healthcheckPath": None,
                                    "id": "99999999-9999-9999-9999-999999999999",
                                    "ipv6EgressEnabled": False,
                                    "latestDeployment": {
                                        "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                                        "status": "SUCCESS",
                                    },
                                    "numReplicas": 1,
                                    "region": None,
                                    "restartPolicyMaxRetries": 10,
                                    "restartPolicyType": "ON_FAILURE",
                                    "rootDirectory": "/backend",
                                    "serviceId": "77777777-7777-7777-7777-777777777777",
                                    "serviceName": "Postgres",
                                    "sleepApplication": False,
                                    "source": {"image": None, "repo": "acme/api"},
                                    "startCommand": None,
                                    "updatedAt": "2026-07-27T18:02:19.805Z",
                                }
                            },
                            {
                                "node": {
                                    "buildCommand": None,
                                    "builder": "RAILPACK",
                                    "createdAt": "2026-07-27T18:00:53.409Z",
                                    "cronSchedule": None,
                                    "dockerfilePath": None,
                                    "domains": {
                                        "customDomains": [
                                            {
                                                "id": "dc111111-1111-1111-1111-111111111111",
                                                "domain": "app.example.com",
                                                "targetPort": 8080,
                                                "isRailwayDomain": False,
                                                "syncStatus": "ACTIVE",
                                                "status": {
                                                    "verified": True,
                                                    "certificateStatus": "ISSUED",
                                                    "verificationDnsHost": None,
                                                },
                                            },
                                            {
                                                "id": "dc222222-2222-2222-2222-222222222222",
                                                "domain": "staging.example.com",
                                                "targetPort": None,
                                                "isRailwayDomain": False,
                                                "syncStatus": "CREATING",
                                                "status": {
                                                    "verified": False,
                                                    "certificateStatus": "PENDING",
                                                    "verificationDnsHost": "_railway.staging.example.com",
                                                },
                                            },
                                        ],
                                        "serviceDomains": [
                                            {
                                                "createdAt": "2026-07-27T18:01:14.958Z",
                                                "domain": "web-production-abcde.up.railway.app",
                                                "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
                                                "suffix": "up.railway.app",
                                                "syncStatus": "ACTIVE",
                                                "targetPort": None,
                                            }
                                        ],
                                    },
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "healthcheckPath": None,
                                    "id": "88888888-8888-8888-8888-888888888888",
                                    "ipv6EgressEnabled": False,
                                    "latestDeployment": {
                                        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                                        "status": "SUCCESS",
                                    },
                                    "numReplicas": None,
                                    "region": None,
                                    "restartPolicyMaxRetries": 10,
                                    "restartPolicyType": "ON_FAILURE",
                                    "rootDirectory": None,
                                    "serviceId": "66666666-6666-6666-6666-666666666666",
                                    "serviceName": "web",
                                    "sleepApplication": False,
                                    "source": {
                                        "image": "nginxdemos/hello",
                                        "repo": None,
                                    },
                                    "startCommand": None,
                                    "updatedAt": "2026-07-27T18:02:00.075Z",
                                }
                            },
                        ],
                        "pageInfo": {"endCursor": "CURSOR", "hasNextPage": False},
                    },
                    "variables": {
                        "edges": [
                            {
                                "node": {
                                    "createdAt": "2026-07-27T18:02:19.955Z",
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "1c4e1cd2-6abe-401e-ab12-f5fa13bfe1b9",
                                    "isSealed": False,
                                    "name": "POSTGRES_USER",
                                    "serviceId": "77777777-7777-7777-7777-777777777777",
                                }
                            },
                            {
                                "node": {
                                    "createdAt": "2026-07-27T18:02:19.941Z",
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "33183b6c-ba7c-4a61-8aad-1d5409f6cbab",
                                    "isSealed": False,
                                    "name": "DATABASE_URL",
                                    "serviceId": "77777777-7777-7777-7777-777777777777",
                                }
                            },
                            {
                                "node": {
                                    "createdAt": "2026-07-27T18:02:19.924Z",
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "33cb9b8d-90a6-4940-9091-7e0a19941dbd",
                                    "isSealed": False,
                                    "name": "POSTGRES_DB",
                                    "serviceId": "77777777-7777-7777-7777-777777777777",
                                }
                            },
                            {
                                "node": {
                                    "createdAt": "2026-07-27T18:02:20.005Z",
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "47a6a10f-5f34-43e3-a9a9-c72bab793aec",
                                    "isSealed": False,
                                    "name": "RAILWAY_DEPLOYMENT_DRAINING_SECONDS",
                                    "serviceId": "77777777-7777-7777-7777-777777777777",
                                }
                            },
                            {
                                "node": {
                                    "createdAt": "2026-07-27T18:02:19.968Z",
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "4b7a21fe-d14a-4207-86e6-961e50306ab1",
                                    "isSealed": False,
                                    "name": "SSL_CERT_DAYS",
                                    "serviceId": "77777777-7777-7777-7777-777777777777",
                                }
                            },
                            {
                                "node": {
                                    "createdAt": "2026-07-27T18:02:19.832Z",
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "58ded11c-a9b8-4154-8dc1-fc2c21815ad6",
                                    "isSealed": False,
                                    "name": "PGDATA",
                                    "serviceId": "77777777-7777-7777-7777-777777777777",
                                }
                            },
                            {
                                "node": {
                                    "createdAt": "2026-07-27T18:02:19.979Z",
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "67ce0a54-a56c-4dff-a534-62c0b06ef375",
                                    "isSealed": False,
                                    "name": "POSTGRES_PASSWORD",
                                    "serviceId": "77777777-7777-7777-7777-777777777777",
                                }
                            },
                            {
                                "node": {
                                    "createdAt": "2026-07-27T18:02:19.992Z",
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "69bae3a7-89f4-4927-982b-f83f17089c9e",
                                    "isSealed": False,
                                    "name": "DATABASE_PUBLIC_URL",
                                    "serviceId": "77777777-7777-7777-7777-777777777777",
                                }
                            },
                            {
                                "node": {
                                    "createdAt": "2026-07-27T18:02:19.906Z",
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "8c9db457-b6c4-40d5-b246-10969c3f004f",
                                    "isSealed": False,
                                    "name": "PGPASSWORD",
                                    "serviceId": "77777777-7777-7777-7777-777777777777",
                                }
                            },
                            {
                                "node": {
                                    "createdAt": "2026-07-27T18:02:19.848Z",
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "8f5fb3d2-97d6-4bbc-b1fa-11afaa43baaa",
                                    "isSealed": False,
                                    "name": "PGHOST",
                                    "serviceId": "77777777-7777-7777-7777-777777777777",
                                }
                            },
                            {
                                "node": {
                                    "createdAt": "2026-07-27T18:02:19.863Z",
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "a7492173-e15d-4f1a-8f61-1d64875077f4",
                                    "isSealed": False,
                                    "name": "PGPORT",
                                    "serviceId": "77777777-7777-7777-7777-777777777777",
                                }
                            },
                            {
                                "node": {
                                    "createdAt": "2026-07-27T18:02:19.874Z",
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "acc10b88-e954-4d60-8ea0-903812e83848",
                                    "isSealed": False,
                                    "name": "PGUSER",
                                    "serviceId": "77777777-7777-7777-7777-777777777777",
                                }
                            },
                            {
                                "node": {
                                    "createdAt": "2026-07-27T18:02:19.892Z",
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "c3d33ff5-26ab-429d-a565-2b46263b9509",
                                    "isSealed": False,
                                    "name": "PGDATABASE",
                                    "serviceId": "77777777-7777-7777-7777-777777777777",
                                }
                            },
                            {
                                "node": {
                                    "createdAt": "2026-07-27T18:01:16.475Z",
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "eb81ef18-1120-4a00-be88-91a478317532",
                                    "isSealed": False,
                                    "name": "FEATURE_FLAG",
                                    "serviceId": "66666666-6666-6666-6666-666666666666",
                                }
                            },
                        ],
                        "pageInfo": {"endCursor": "CURSOR", "hasNextPage": False},
                    },
                    "volumeInstances": {
                        "edges": [
                            {
                                "node": {
                                    "createdAt": "2026-07-27T18:01:56.600Z",
                                    "currentSizeMB": 32.145408,
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "f3333333-3333-3333-3333-333333333333",
                                    "mountPath": "/data",
                                    "region": "us-west2",
                                    "serviceId": "66666666-6666-6666-6666-666666666666",
                                    "sizeMB": 500,
                                    "state": "READY",
                                    "volumeId": "f1111111-1111-1111-1111-111111111111",
                                }
                            },
                            {
                                "node": {
                                    "createdAt": "2026-07-27T18:02:19.581Z",
                                    "currentSizeMB": 82.82112,
                                    "environmentId": "44444444-4444-4444-4444-444444444444",
                                    "id": "f4444444-4444-4444-4444-444444444444",
                                    "mountPath": "/var/lib/postgresql/data",
                                    "region": "us-west2",
                                    "serviceId": "77777777-7777-7777-7777-777777777777",
                                    "sizeMB": 500,
                                    "state": "READY",
                                    "volumeId": "f2222222-2222-2222-2222-222222222222",
                                }
                            },
                        ],
                        "pageInfo": {"endCursor": "CURSOR", "hasNextPage": False},
                    },
                }
            },
        ],
        "pageInfo": {"endCursor": "CURSOR", "hasNextPage": False},
    },
    "id": "33333333-3333-3333-3333-333333333333",
    "isPublic": False,
    "isTempProject": False,
    "members": [],
    "name": "cartography-fixture",
    "prDeploys": False,
    "services": {
        "edges": [
            {
                "node": {
                    "createdAt": "2026-07-27T18:00:53.381Z",
                    "icon": None,
                    "id": "66666666-6666-6666-6666-666666666666",
                    "isRestricted": False,
                    "name": "web",
                    "projectId": "33333333-3333-3333-3333-333333333333",
                    "templateId": None,
                    "updatedAt": "2026-07-27T18:00:53.381Z",
                }
            },
            {
                "node": {
                    "createdAt": "2026-07-27T18:02:17.950Z",
                    "icon": "https://devicons.railway.app/i/postgresql.svg",
                    "id": "77777777-7777-7777-7777-777777777777",
                    "isRestricted": False,
                    "name": "Postgres",
                    "projectId": "33333333-3333-3333-3333-333333333333",
                    "templateId": "b55da7dc-09be-4140-bc65-1284d15d349c",
                    "updatedAt": "2026-07-27T18:02:17.950Z",
                }
            },
        ],
        "pageInfo": {"endCursor": "CURSOR", "hasNextPage": False},
    },
    "subscriptionType": "trial",
    "updatedAt": "2026-07-27T18:00:44.634Z",
    "volumes": {
        "edges": [
            {
                "node": {
                    "createdAt": "2026-07-27T18:01:31.577Z",
                    "id": "f1111111-1111-1111-1111-111111111111",
                    "name": "web-volume",
                    "projectId": "33333333-3333-3333-3333-333333333333",
                }
            },
            {
                "node": {
                    "createdAt": "2026-07-27T18:02:17.967Z",
                    "id": "f2222222-2222-2222-2222-222222222222",
                    "name": "postgres-volume",
                    "projectId": "33333333-3333-3333-3333-333333333333",
                }
            },
        ],
        "pageInfo": {"endCursor": "CURSOR", "hasNextPage": False},
    },
    "workspaceId": "11111111-1111-1111-1111-111111111111",
}
