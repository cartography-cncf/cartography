# flake8: noqa
# Source: https://cloud.google.com/iam/docs/reference/rest/v1/organizations.roles#Role
LIST_ROLES_RESPONSE = {
    "roles": [
        {
            "name": "projects/project-123/roles/customRole1",
            "title": "Custom Role 1",
            "description": "This is a custom project role",
            "includedPermissions": [
                "iam.roles.get",
                "iam.roles.list",
                "storage.buckets.get",
                "storage.buckets.list",
            ],
            "stage": "GA",
            "etag": "etag_123",
            "deleted": False,
            "version": 1,
        },
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
            ],
            "stage": "GA",
            "etag": "etag_456",
            "deleted": False,
            "version": 1,
        },
        {
            "name": "projects/project-123/roles/customRole2",
            "title": "Custom Role 2",
            "description": "This is a deleted custom role",
            "includedPermissions": [
                "iam.serviceAccounts.get",
                "iam.serviceAccounts.list",
            ],
            "stage": "DISABLED",
            "etag": "etag_789",
            "deleted": True,
            "version": 2,
        },
    ],
}

# Source: https://cloud.google.com/iam/docs/reference/rest/v1/projects.serviceAccounts#resource:-serviceaccount
LIST_SERVICE_ACCOUNTS_RESPONSE = {
    "accounts": [
        {
            "name": "projects/project-123/serviceAccounts/service-account-1@project-123.iam.gserviceaccount.com",
            "projectId": "project-123",
            "uniqueId": "112233445566778899",
            "email": "service-account-1@project-123.iam.gserviceaccount.com",
            "displayName": "Service Account 1",
            "etag": "etag_123",
            "description": "Test service account 1",
            "oauth2ClientId": "112233445566778899",
            "disabled": False,
        },
        {
            "name": "projects/project-123/serviceAccounts/service-account-2@project-123.iam.gserviceaccount.com",
            "projectId": "project-123",
            "uniqueId": "998877665544332211",
            "email": "service-account-2@project-123.iam.gserviceaccount.com",
            "displayName": "Service Account 2",
            "etag": "etag_456",
            "description": "Test service account 2",
            "oauth2ClientId": "998877665544332211",
            "disabled": True,
        },
    ],
}

# Source: https://cloud.google.com/iam/docs/reference/rest/v1/projects.serviceAccounts.keys#resource:-serviceaccountkey
LIST_SERVICE_ACCOUNT_KEYS_RESPONSE = {
    "keys": [
        {
            "name": "projects/project-123/serviceAccounts/service-account-1@project-123.iam.gserviceaccount.com/keys/1234567890",
            "validAfterTime": "2023-01-01T00:00:00Z",
            "validBeforeTime": "2024-01-01T00:00:00Z",
            "keyAlgorithm": "KEY_ALG_RSA_2048",
            "keyOrigin": "GOOGLE_PROVIDED",
            "keyType": "SYSTEM_MANAGED",
        },
        {
            "name": "projects/project-123/serviceAccounts/service-account-1@project-123.iam.gserviceaccount.com/keys/0987654321",
            "validAfterTime": "2023-02-01T00:00:00Z",
            "validBeforeTime": "2024-02-01T00:00:00Z",
            "keyAlgorithm": "KEY_ALG_RSA_2048",
            "keyOrigin": "USER_PROVIDED",
            "keyType": "USER_MANAGED",
        },
    ],
}
