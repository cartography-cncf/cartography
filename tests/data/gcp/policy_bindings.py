# flake8: noqa
MOCK_IAM_ROLES = [
    {
        "name": "roles/editor",
        "title": "Editor",
        "description": "Edit access to all resources.",
        "includedPermissions": [
            "storage.buckets.get",
            "storage.buckets.list",
            "storage.buckets.update",
            "storage.objects.create",
            "storage.objects.delete",
            "compute.acceleratorTypes.get",
        ],
        "stage": "GA",
        "etag": "etag_456",
        "deleted": False,
        "version": 1,
    },
    {
        "name": "roles/viewer",
        "title": "Viewer",
        "description": "View access to all resources.",
        "includedPermissions": [
            "storage.buckets.get",
        ],
        "stage": "GA",
        "etag": "etag_viewer",
        "deleted": False,
        "version": 1,
    },
    {
        "name": "roles/storage.admin",
        "title": "Storage Admin",
        "description": "Full control of storage resources.",
        "includedPermissions": [
            "storage.buckets.get",
            "storage.buckets.create",
        ],
        "stage": "GA",
        "etag": "etag_storage_admin",
        "deleted": False,
        "version": 1,
    },
    {
        "name": "roles/storage.objectViewer",
        "title": "Storage Object Viewer",
        "description": "View storage objects.",
        "includedPermissions": [
            "storage.objects.get",
        ],
        "stage": "GA",
        "etag": "etag_object_viewer",
        "deleted": False,
        "version": 1,
    },
    {
        "name": "roles/test.gcp_extended",
        "title": "Test Extended GCP Permissions",
        "description": "Bundle of permissions used to exercise BigQuery, KMS and Artifact Registry permission relationships.",
        "includedPermissions": [
            "bigquery.tables.getData",
            "bigquery.datasets.get",
            "cloudkms.cryptoKeyVersions.useToDecrypt",
            "artifactregistry.repositories.downloadArtifacts",
        ],
        "stage": "GA",
        "etag": "etag_gcp_extended",
        "deleted": False,
        "version": 1,
    },
    {
        "name": "roles/iam.serviceAccountTokenCreator",
        "title": "Service Account Token Creator",
        "description": "Impersonate service accounts (create OAuth2 access tokens, sign blobs or JWTs, etc).",
        "includedPermissions": [
            "iam.serviceAccounts.getAccessToken",
            "iam.serviceAccounts.getOpenIdToken",
            "iam.serviceAccounts.implicitDelegation",
            "iam.serviceAccounts.signBlob",
            "iam.serviceAccounts.signJwt",
        ],
        "stage": "GA",
        "etag": "etag_sa_token_creator",
        "deleted": False,
        "version": 1,
    },
    {
        "name": "roles/bigquery.dataViewer",
        "title": "BigQuery Data Viewer",
        "description": "Read access to BigQuery datasets and tables.",
        "includedPermissions": [
            "bigquery.tables.getData",
            "bigquery.datasets.get",
        ],
        "stage": "GA",
        "etag": "etag_bigquery_data_viewer",
        "deleted": False,
        "version": 1,
    },
]

MOCK_IAM_SERVICE_ACCOUNTS = [
    {
        "name": "projects/project-abc/serviceAccounts/sa@project-abc.iam.gserviceaccount.com",
        "projectId": "project-abc",
        "uniqueId": "112233445566778899",
        "email": "sa@project-abc.iam.gserviceaccount.com",
        "displayName": "Service Account",
        "etag": "etag_123",
        "description": "Test service account",
        "oauth2ClientId": "112233445566778899",
        "disabled": False,
    },
]

MOCK_GSUITE_USERS = [
    {
        "users": [
            {
                "id": "user-alice",
                "agreedToTerms": True,
                "archived": False,
                "changePasswordAtNextLogin": False,
                "creationTime": "2023-01-01T00:00:00.000Z",
                "customerId": "customer-123",
                "etag": "etag-user-alice",
                "includeInGlobalAddressList": True,
                "ipWhitelisted": False,
                "isAdmin": True,
                "isDelegatedAdmin": False,
                "isEnforcedIn2Sv": True,
                "isEnrolledIn2Sv": True,
                "isMailboxSetup": True,
                "kind": "admin#directory#user",
                "lastLoginTime": "2024-01-01T12:34:56.000Z",
                "name": {
                    "fullName": "Alice Admin",
                    "familyName": "Admin",
                    "givenName": "Alice",
                },
                "orgUnitPath": "/",
                "primaryEmail": "alice@example.com",
                "suspended": False,
                "thumbnailPhotoEtag": "photo-etag-1",
                "thumbnailPhotoUrl": "https://example.com/photo1.jpg",
            },
            {
                "id": "user-bob",
                "agreedToTerms": True,
                "archived": False,
                "changePasswordAtNextLogin": False,
                "creationTime": "2023-02-01T00:00:00.000Z",
                "customerId": "customer-123",
                "etag": "etag-user-bob",
                "includeInGlobalAddressList": True,
                "ipWhitelisted": False,
                "isAdmin": False,
                "isDelegatedAdmin": False,
                "isEnforcedIn2Sv": False,
                "isEnrolledIn2Sv": False,
                "isMailboxSetup": True,
                "kind": "admin#directory#user",
                "lastLoginTime": "2024-02-01T06:00:00.000Z",
                "name": {
                    "fullName": "Bob Builder",
                    "familyName": "Builder",
                    "givenName": "Bob",
                },
                "orgUnitPath": "/Engineering",
                "primaryEmail": "bob@example.com",
                "suspended": False,
                "thumbnailPhotoEtag": "photo-etag-2",
                "thumbnailPhotoUrl": "https://example.com/photo2.jpg",
            },
        ],
    },
]

MOCK_GSUITE_GROUPS = [
    {
        "id": "group-viewers",
        "adminCreated": True,
        "description": "Viewers group",
        "directMembersCount": 1,
        "email": "viewers@example.com",
        "etag": "etag-group-viewers",
        "kind": "admin#directory#group",
        "name": "Viewers",
    },
]

MOCK_GSUITE_GROUP_MEMBERS = {
    "viewers@example.com": [
        {
            "id": "user-bob",
            "email": "bob@example.com",
            "type": "USER",
            "role": "MEMBER",
        },
    ],
}

MOCK_POLICY_BINDINGS_RESPONSE = {
    "project_id": "project-abc",
    "organization": "organizations/1337",
    "policy_results": [
        {
            "full_resource_name": "//cloudresourcemanager.googleapis.com/projects/project-abc",
            "policies": [
                {
                    "attached_resource": "//cloudresourcemanager.googleapis.com/projects/project-abc",
                    "policy": {
                        "bindings": [
                            {
                                "role": "roles/editor",
                                "members": [
                                    "user:alice@example.com",  # GSuite user
                                    "serviceAccount:sa@project-abc.iam.gserviceaccount.com",  # IAM service account
                                ],
                            },
                            {
                                "role": "roles/viewer",
                                "members": [
                                    "group:viewers@example.com",  # GSuite group
                                ],
                            },
                            {
                                "role": "roles/storage.admin",
                                "members": [
                                    "user:bob@example.com",  # GSuite user
                                ],
                                "condition": {
                                    "title": "Expires on 2024-12-31",
                                    "expression": "request.time < timestamp('2024-12-31T00:00:00Z')",
                                },
                            },
                            {
                                "role": "roles/test.gcp_extended",
                                "members": [
                                    "user:alice@example.com",  # GSuite user
                                ],
                            },
                            {
                                "role": "roles/iam.serviceAccountTokenCreator",
                                "members": [
                                    "user:bob@example.com",  # GSuite user
                                ],
                            },
                        ],
                    },
                },
            ],
        },
        {
            "full_resource_name": "//storage.googleapis.com/buckets/test-bucket",
            "policies": [
                {
                    "attached_resource": "//storage.googleapis.com/buckets/test-bucket",
                    "policy": {
                        "bindings": [
                            {
                                "role": "roles/storage.objectViewer",
                                "members": [
                                    "user:alice@example.com",  # GSuite user
                                    "allUsers",  # Public exposure
                                ],
                            },
                        ],
                    },
                },
            ],
        },
        # Resource-scoped binding on a specific BigQuery table. Used by
        # test_sync_gcp_permission_relationships to verify that scope keys
        # disambiguate sibling tables sharing the same leaf name across
        # different datasets.
        {
            "full_resource_name": (
                "//bigquery.googleapis.com/projects/project-abc/"
                "datasets/dataset_a/tables/events"
            ),
            "policies": [
                {
                    "attached_resource": (
                        "//bigquery.googleapis.com/projects/project-abc/"
                        "datasets/dataset_a/tables/events"
                    ),
                    "policy": {
                        "bindings": [
                            {
                                "role": "roles/bigquery.dataViewer",
                                "members": [
                                    "user:bob@example.com",  # GSuite user
                                ],
                            },
                        ],
                    },
                },
            ],
        },
    ],
}
