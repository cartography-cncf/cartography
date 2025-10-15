import datetime

from msgraph.generated.models.group import Group
from msgraph.generated.models.organization import Organization
from msgraph.generated.models.service_principal import ServicePrincipal
from msgraph.generated.models.user import User

# Mock Azure Subscription
AZURE_SUBSCRIPTION = {
    "id": "/subscriptions/12345678-1234-1234-1234-123456789012",
    "subscriptionId": "12345678-1234-1234-1234-123456789012",
    "displayName": "Test Subscription",
    "state": "Enabled",
}

# Mock Entra Tenant
MOCK_ENTRA_TENANT = Organization(
    id="12345678-1234-1234-1234-123456789012",
    display_name="Test Tenant",
    created_date_time=datetime.datetime(
        2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
    ),
    default_usage_location="US",
    deleted_date_time=None,
    marketing_notification_emails=[],
    mobile_device_management_authority=None,
    on_premises_last_sync_date_time=None,
    on_premises_sync_enabled=False,
    partner_tenant_type=None,
    postal_code=None,
    preferred_language="en",
    state=None,
    street=None,
    tenant_type="AAD",
)

# Mock Entra Users (as User objects from msgraph)
ENTRA_USERS = [
    User(
        id="user-123",
        odata_type="#microsoft.graph.user",
        user_principal_name="alice@contoso.com",
        display_name="Alice Smith",
        given_name="Alice",
        surname="Smith",
        mail="alice@contoso.com",
        account_enabled=True,
        department="IT",
        job_title="Database Administrator",
    ),
    User(
        id="user-456",
        odata_type="#microsoft.graph.user",
        user_principal_name="bob@contoso.com",
        display_name="Bob Jones",
        given_name="Bob",
        surname="Jones",
        mail="bob@contoso.com",
        account_enabled=True,
        department="Engineering",
        job_title="Software Engineer",
    ),
]

# Mock Entra Groups (as Group objects from msgraph)
ENTRA_GROUPS = [
    Group(
        id="group-789",
        odata_type="#microsoft.graph.group",
        display_name="SQL Admins",
        description="Database administrators group",
        mail="sql-admins@contoso.com",
        mail_enabled=True,
        mail_nickname="sql-admins",
        security_enabled=True,
        group_types=["Unified"],
        visibility="Private",
    ),
]


# Mock Entra Service Principals (as ServicePrincipal objects from msgraph)
ENTRA_SERVICE_PRINCIPALS = [
    ServicePrincipal(
        id="sp-101",
        odata_type="#microsoft.graph.servicePrincipal",
        display_name="Test App Service Principal",
        app_id="11111111-1111-1111-1111-111111111111",
        account_enabled=True,
        service_principal_type="Application",
        sign_in_audience="AzureADMyOrg",
    ),
]

# Mock Azure Role Definitions
AZURE_ROLE_DEFINITIONS = [
    {
        "id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/8e3af657-a8ff-443c-a75c-2fe8c4bcb635",
        "name": "Owner",
        "role_name": "Owner",
        "description": "Grants full access to manage all resources",
        "permissions": [
            {
                "actions": ["*"],
                "not_actions": [],
                "data_actions": [],
                "not_data_actions": [],
            }
        ],
        "subscription_id": "12345678-1234-1234-1234-123456789012",
    },
    {
        "id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7",
        "name": "Reader",
        "role_name": "Reader",
        "description": "View all resources but not make changes",
        "permissions": [
            {
                "actions": [
                    "*/read",
                    "Microsoft.Resources/subscriptions/resourceGroups/read",
                    "Microsoft.Resources/subscriptions/read",
                    "Microsoft.Authorization/*/read",
                ],
                "not_actions": [
                    "Microsoft.KeyVault/vaults/secrets/read",
                    "Microsoft.KeyVault/vaults/keys/read",
                ],
                "data_actions": [
                    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read",
                    "Microsoft.Storage/storageAccounts/queueServices/queues/messages/read",
                    "Microsoft.Storage/storageAccounts/tableServices/tables/entities/read",
                ],
                "not_data_actions": [
                    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/immutabilityPolicies/read",
                    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/legalHold/read",
                ],
            }
        ],
        "subscription_id": "12345678-1234-1234-1234-123456789012",
    },
    {
        "id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/9b7fa4d4-9aa6-4d26-9dfc-4ef0b805d5d4",
        "name": "SQL Server Contributor",
        "role_name": "SQL Server Contributor",
        "description": "Lets you manage SQL servers and databases",
        "permissions": [
            {
                "actions": [
                    "Microsoft.Sql/servers/*",
                    "Microsoft.Sql/servers/databases/*",
                    "Microsoft.Sql/servers/administrators/*",
                    "Microsoft.Sql/servers/securityAlertPolicies/*",
                    "Microsoft.Sql/servers/vulnerabilityAssessments/*",
                    "Microsoft.Sql/servers/auditingSettings/*",
                    "Microsoft.Sql/servers/encryptionProtector/*",
                    "Microsoft.Sql/servers/transparentDataEncryption/*",
                ],
                "not_actions": [
                    "Microsoft.Sql/servers/delete",
                    "Microsoft.Sql/servers/firewallRules/delete",
                ],
                "data_actions": [
                    "Microsoft.Sql/servers/databases/queryStore/*",
                    "Microsoft.Sql/servers/databases/transparentDataEncryption/*",
                ],
                "not_data_actions": [
                    "Microsoft.Sql/servers/databases/queryStore/delete",
                    "Microsoft.Sql/servers/databases/transparentDataEncryption/delete",
                ],
            }
        ],
        "subscription_id": "12345678-1234-1234-1234-123456789012",
    },
]

# Mock Azure Role Assignments
AZURE_ROLE_ASSIGNMENTS = [
    {
        "id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-1",
        "name": "assignment-1",
        "principal_id": "user-123",
        "principal_type": "User",
        "role_definition_id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/8e3af657-a8ff-443c-a75c-2fe8c4bcb635",
        "scope": "/subscriptions/12345678-1234-1234-1234-123456789012",
        "subscription_id": "12345678-1234-1234-1234-123456789012",
    },
    {
        "id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-2",
        "name": "assignment-2",
        "principal_id": "group-789",
        "principal_type": "Group",
        "role_definition_id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/9b7fa4d4-9aa6-4d26-9dfc-4ef0b805d5d4",
        "scope": "/subscriptions/12345678-1234-1234-1234-123456789012",
        "subscription_id": "12345678-1234-1234-1234-123456789012",
    },
    {
        "id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-3",
        "name": "assignment-3",
        "principal_id": "user-456",
        "principal_type": "User",
        "role_definition_id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7",
        "scope": "/subscriptions/12345678-1234-1234-1234-123456789012",
        "subscription_id": "12345678-1234-1234-1234-123456789012",
    },
    {
        "id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-4",
        "name": "assignment-4",
        "principal_id": "sp-101",
        "principal_type": "ServicePrincipal",
        "role_definition_id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7",
        "scope": "/subscriptions/12345678-1234-1234-1234-123456789012",
        "subscription_id": "12345678-1234-1234-1234-123456789012",
    },
]

# Mock Azure Permissions (separate nodes)
AZURE_PERMISSIONS = [
    {
        "id": "perm-1",
        "actions": ["*"],
        "notActions": [],
        "dataActions": [],
        "notDataActions": [],
    },
    {
        "id": "perm-2",
        "actions": [
            "*/read",
            "Microsoft.Resources/subscriptions/resourceGroups/read",
            "Microsoft.Resources/subscriptions/read",
            "Microsoft.Authorization/*/read",
        ],
        "notActions": [
            "Microsoft.KeyVault/vaults/secrets/read",
            "Microsoft.KeyVault/vaults/keys/read",
        ],
        "dataActions": [
            "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read",
            "Microsoft.Storage/storageAccounts/queueServices/queues/messages/read",
            "Microsoft.Storage/storageAccounts/tableServices/tables/entities/read",
        ],
        "notDataActions": [
            "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/immutabilityPolicies/read",
            "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/legalHold/read",
        ],
    },
    {
        "id": "perm-3",
        "actions": [
            "Microsoft.Sql/servers/*",
            "Microsoft.Sql/servers/databases/*",
            "Microsoft.Sql/servers/administrators/*",
            "Microsoft.Sql/servers/securityAlertPolicies/*",
            "Microsoft.Sql/servers/vulnerabilityAssessments/*",
            "Microsoft.Sql/servers/auditingSettings/*",
            "Microsoft.Sql/servers/encryptionProtector/*",
            "Microsoft.Sql/servers/transparentDataEncryption/*",
        ],
        "notActions": [
            "Microsoft.Sql/servers/delete",
            "Microsoft.Sql/servers/firewallRules/delete",
        ],
        "dataActions": [
            "Microsoft.Sql/servers/databases/queryStore/*",
            "Microsoft.Sql/servers/databases/transparentDataEncryption/*",
        ],
        "notDataActions": [
            "Microsoft.Sql/servers/databases/queryStore/delete",
            "Microsoft.Sql/servers/databases/transparentDataEncryption/delete",
        ],
    },
]
