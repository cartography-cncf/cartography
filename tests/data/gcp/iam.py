# flake8: noqa
# Source: https://cloud.google.com/iam/docs/reference/rest/v1/organizations.roles#Role
LIST_ORG_ROLES_RESPONSE = {
    'roles': [
        {
            'name': 'roles/viewer',
            'title': 'Viewer',
            'description': 'Read-only access.',
            'includedPermissions': ['storage.buckets.get', 'storage.buckets.list'],
            'etag': 'abc123',
        },
        {
            'name': 'organizations/123456789/roles/customOrgRole',
            'title': 'Custom Org Role',
            'description': 'A custom organization-level role',
            'includedPermissions': ['storage.buckets.get'],
            'etag': 'def456',
        },
    ],
}

LIST_PROJECT_ROLES_RESPONSE = {
    'roles': [
        {
            'name': 'projects/project-123/roles/customRole1',
            'title': 'Custom Project Role 1',
            'description': 'A custom project-level role',
            'includedPermissions': ['storage.buckets.get'],
            'etag': 'ghi789',
        },
        {
            'name': 'projects/project-123/roles/customRole2',
            'title': 'Custom Project Role 2',
            'description': 'Another custom project-level role',
            'includedPermissions': ['storage.buckets.list'],
            'etag': 'jkl012',
        },
    ],
}

# Source: https://cloud.google.com/iam/docs/reference/rest/v1/projects.serviceAccounts#resource:-serviceaccount
LIST_SERVICE_ACCOUNTS_RESPONSE = {
    'accounts': [
        {
            'name': 'projects/project-123/serviceAccounts/112233445566778899',
            'projectId': 'project-123',
            'uniqueId': '112233445566778899',
            'email': 'service-1@project-123.iam.gserviceaccount.com',
            'displayName': 'Service Account 1',
            'etag': 'mno345',
            'oauth2ClientId': '112233445566778899',
        },
        {
            'name': 'projects/project-123/serviceAccounts/998877665544332211',
            'projectId': 'project-123',
            'uniqueId': '998877665544332211',
            'email': 'service-2@project-123.iam.gserviceaccount.com',
            'displayName': 'Service Account 2',
            'etag': 'pqr678',
            'oauth2ClientId': '998877665544332211',
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
