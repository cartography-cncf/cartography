# flake8: noqa
# Test organization ID
TEST_ORG_ID = "organizations/123456789012"

# Source: https://cloud.google.com/iam/docs/reference/rest/v1/roles#Role
# Predefined/Basic roles (global, not project or org specific)
LIST_PREDEFINED_ROLES_RESPONSE = {
    "roles": [
        {
            "name": "roles/owner",
            "title": "Owner",
            "description": "Full access to all resources.",
            "includedPermissions": [
                "resourcemanager.projects.get",
                "resourcemanager.projects.delete",
                "iam.roles.create",
                "iam.roles.delete",
            ],
            "stage": "GA",
            "etag": "etag_owner",
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
            "name": "roles/viewer",
            "title": "Viewer",
            "description": "View access to all resources.",
            "includedPermissions": [
                "storage.buckets.get",
                "storage.buckets.list",
            ],
            "stage": "GA",
            "etag": "etag_viewer",
            "deleted": False,
            "version": 1,
        },
        {
            "name": "roles/iam.securityAdmin",
            "title": "Security Admin",
            "description": "Security administrator role.",
            "includedPermissions": [
                "iam.roles.get",
                "iam.roles.list",
                "iam.serviceAccounts.get",
            ],
            "stage": "GA",
            "etag": "etag_secadmin",
            "deleted": False,
            "version": 1,
        },
    ],
}

# Source: https://cloud.google.com/iam/docs/reference/rest/v1/organizations.roles#Role
# Custom organization-level roles
LIST_ORG_ROLES_RESPONSE = {
    "roles": [
        {
            "name": "organizations/123456789012/roles/customOrgRole1",
            "title": "Custom Org Role 1",
            "description": "This is a custom organization role",
            "includedPermissions": [
                "resourcemanager.organizations.get",
                "resourcemanager.folders.list",
            ],
            "stage": "GA",
            "etag": "etag_org_123",
            "deleted": False,
            "version": 1,
        },
        {
            "name": "organizations/123456789012/roles/customOrgRole2",
            "title": "Custom Org Role 2",
            "description": "Another custom organization role",
            "includedPermissions": [
                "iam.serviceAccounts.get",
                "iam.serviceAccounts.list",
            ],
            "stage": "GA",
            "etag": "etag_org_456",
            "deleted": False,
            "version": 1,
        },
    ],
}

# Source: https://cloud.google.com/iam/docs/reference/rest/v1/projects.roles#Role
# Custom project-level roles only (no predefined roles)
LIST_PROJECT_CUSTOM_ROLES_RESPONSE = {
    "roles": [
        {
            "name": "projects/project-abc/roles/customRole1",
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
            "name": "projects/project-abc/roles/customRole2",
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

# Combined response for backward compatibility (used by get_gcp_roles)
# Source: https://cloud.google.com/iam/docs/reference/rest/v1/organizations.roles#Role
LIST_ROLES_RESPONSE = {
    "roles": [
        {
            "name": "projects/project-abc/roles/customRole1",
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
            "name": "projects/project-abc/roles/customRole2",
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
            "name": "projects/project-abc/serviceAccounts/service-account-1@project-abc.iam.gserviceaccount.com",
            "projectId": "project-abc",
            "uniqueId": "112233445566778899",
            "email": "service-account-1@project-abc.iam.gserviceaccount.com",
            "displayName": "Service Account 1",
            "etag": "etag_123",
            "description": "Test service account 1",
            "oauth2ClientId": "112233445566778899",
            "disabled": False,
        },
        {
            "name": "projects/project-abc/serviceAccounts/service-account-2@project-abc.iam.gserviceaccount.com",
            "projectId": "project-abc",
            "uniqueId": "998877665544332211",
            "email": "service-account-2@project-abc.iam.gserviceaccount.com",
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
            "name": "projects/project-abc/serviceAccounts/service-account-1@project-abc.iam.gserviceaccount.com/keys/1234567890",
            "validAfterTime": "2023-01-01T00:00:00Z",
            "validBeforeTime": "2024-01-01T00:00:00Z",
            "keyAlgorithm": "KEY_ALG_RSA_2048",
            "keyOrigin": "GOOGLE_PROVIDED",
            "keyType": "SYSTEM_MANAGED",
        },
        {
            "name": "projects/project-abc/serviceAccounts/service-account-1@project-abc.iam.gserviceaccount.com/keys/0987654321",
            "validAfterTime": "2023-02-01T00:00:00Z",
            "validBeforeTime": "2024-02-01T00:00:00Z",
            "keyAlgorithm": "KEY_ALG_RSA_2048",
            "keyOrigin": "USER_PROVIDED",
            "keyType": "USER_MANAGED",
        },
    ],
}

# Source: https://cloud.google.com/asset-inventory/docs/reference/rest/v1/assets/list
# Cloud Asset Inventory API response for service accounts
CAI_SERVICE_ACCOUNTS_RESPONSE = {
    "assets": [
        {
            "name": "//iam.googleapis.com/projects/project-abc/serviceAccounts/112233445566778899",
            "assetType": "iam.googleapis.com/ServiceAccount",
            "resource": {
                "version": "v1",
                "discoveryDocumentUri": "https://iam.googleapis.com/$discovery/rest",
                "discoveryName": "ServiceAccount",
                "parent": "//cloudresourcemanager.googleapis.com/projects/project-abc",
                "data": {
                    "name": "projects/project-abc/serviceAccounts/service-account-1@project-abc.iam.gserviceaccount.com",
                    "projectId": "project-abc",
                    "uniqueId": "112233445566778899",
                    "email": "service-account-1@project-abc.iam.gserviceaccount.com",
                    "displayName": "Service Account 1",
                    "etag": "etag_123",
                    "description": "Test service account 1",
                    "oauth2ClientId": "112233445566778899",
                    "disabled": False,
                },
            },
            "ancestors": [
                "projects/project-abc",
                "organizations/123456789",
            ],
            "updateTime": "2023-01-01T00:00:00Z",
        },
        {
            "name": "//iam.googleapis.com/projects/project-abc/serviceAccounts/998877665544332211",
            "assetType": "iam.googleapis.com/ServiceAccount",
            "resource": {
                "version": "v1",
                "discoveryDocumentUri": "https://iam.googleapis.com/$discovery/rest",
                "discoveryName": "ServiceAccount",
                "parent": "//cloudresourcemanager.googleapis.com/projects/project-abc",
                "data": {
                    "name": "projects/project-abc/serviceAccounts/service-account-2@project-abc.iam.gserviceaccount.com",
                    "projectId": "project-abc",
                    "uniqueId": "998877665544332211",
                    "email": "service-account-2@project-abc.iam.gserviceaccount.com",
                    "displayName": "Service Account 2",
                    "etag": "etag_456",
                    "description": "Test service account 2",
                    "oauth2ClientId": "998877665544332211",
                    "disabled": True,
                },
            },
            "ancestors": [
                "projects/project-abc",
                "organizations/123456789",
            ],
            "updateTime": "2023-01-02T00:00:00Z",
        },
    ],
}

# Cloud Asset Inventory API response for roles
CAI_ROLES_RESPONSE = {
    "assets": [
        {
            "name": "//iam.googleapis.com/projects/project-abc/roles/customRole1",
            "assetType": "iam.googleapis.com/Role",
            "resource": {
                "version": "v1",
                "discoveryDocumentUri": "https://iam.googleapis.com/$discovery/rest",
                "discoveryName": "Role",
                "parent": "//cloudresourcemanager.googleapis.com/projects/project-abc",
                "data": {
                    "name": "projects/project-abc/roles/customRole1",
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
                },
            },
            "ancestors": [
                "projects/project-abc",
                "organizations/123456789",
            ],
            "updateTime": "2023-01-01T00:00:00Z",
        },
        {
            "name": "//iam.googleapis.com/projects/project-abc/roles/customRole2",
            "assetType": "iam.googleapis.com/Role",
            "resource": {
                "version": "v1",
                "discoveryDocumentUri": "https://iam.googleapis.com/$discovery/rest",
                "discoveryName": "Role",
                "parent": "//cloudresourcemanager.googleapis.com/projects/project-abc",
                "data": {
                    "name": "projects/project-abc/roles/customRole2",
                    "title": "Custom Role 2",
                    "description": "This is a deleted custom role",
                    "includedPermissions": [
                        "iam.serviceAccounts.get",
                        "iam.serviceAccounts.list",
                    ],
                    "stage": "DISABLED",
                    "etag": "etag_789",
                    "deleted": True,
                },
            },
            "ancestors": [
                "projects/project-abc",
                "organizations/123456789",
            ],
            "updateTime": "2023-01-03T00:00:00Z",
        },
    ],
}
