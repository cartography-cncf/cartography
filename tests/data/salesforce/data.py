ORG_ID = "00D000000000001EAA"

SALESFORCE_ORGANIZATION = {
    "Id": ORG_ID,
    "Name": "Simpson Corp",
    "OrganizationType": "Enterprise Edition",
    "InstanceName": "NA1",
    "IsSandbox": False,
    "PrimaryContact": "Homer Simpson",
    "Country": "US",
    "LanguageLocaleKey": "en_US",
    "NamespacePrefix": None,
    "TrialExpirationDate": None,
    "CreatedDate": "2020-01-01T00:00:00.000+0000",
}

SALESFORCE_PROFILES = [
    {
        "Id": "00e000000000001AAA",
        "Name": "System Administrator",
        "UserType": "Standard",
        "Description": "Full access",
        "PermissionsModifyAllData": True,
        "PermissionsViewAllData": True,
        "PermissionsApiEnabled": True,
        "PermissionsManageUsers": True,
        "CreatedDate": "2020-01-01T00:00:00.000+0000",
    },
    {
        "Id": "00e000000000002AAA",
        "Name": "Standard User",
        "UserType": "Standard",
        "Description": "Limited access",
        "PermissionsModifyAllData": False,
        "PermissionsViewAllData": False,
        "PermissionsApiEnabled": True,
        "PermissionsManageUsers": False,
        "CreatedDate": "2020-01-01T00:00:00.000+0000",
    },
]

SALESFORCE_USER_ROLES = [
    {
        "Id": "00E000000000001AAA",
        "Name": "CEO",
        "DeveloperName": "CEO",
        "ParentRoleId": None,
        "RollupDescription": None,
        "PortalType": "None",
    },
    {
        "Id": "00E000000000002AAA",
        "Name": "VP Sales",
        "DeveloperName": "VP_Sales",
        "ParentRoleId": "00E000000000001AAA",
        "RollupDescription": None,
        "PortalType": "None",
    },
]

SALESFORCE_USERS = [
    {
        "Id": "005000000000001AAA",
        "Username": "hjsimpson@simpson.corp",
        "Name": "Homer Simpson",
        "FirstName": "Homer",
        "LastName": "Simpson",
        "Email": "hjsimpson@simpson.corp",
        "Alias": "hsimpson",
        "IsActive": True,
        "UserType": "Standard",
        "ProfileId": "00e000000000001AAA",
        "UserRoleId": "00E000000000001AAA",
        "ManagerId": None,
        "Department": "Executive",
        "Title": "CEO",
        "FederationIdentifier": None,
        "CreatedDate": "2020-01-02T00:00:00.000+0000",
        "LastLoginDate": "2023-06-01T12:00:00.000+0000",
        "LastPasswordChangeDate": "2023-01-01T00:00:00.000+0000",
    },
    {
        "Id": "005000000000002AAA",
        "Username": "mbsimpson@simpson.corp",
        "Name": "Marge Simpson",
        "FirstName": "Marge",
        "LastName": "Simpson",
        "Email": "mbsimpson@simpson.corp",
        "Alias": "msimpson",
        "IsActive": True,
        "UserType": "Standard",
        "ProfileId": "00e000000000002AAA",
        "UserRoleId": "00E000000000002AAA",
        "ManagerId": "005000000000001AAA",
        "Department": "Sales",
        "Title": "VP Sales",
        "FederationIdentifier": None,
        "CreatedDate": "2020-01-03T00:00:00.000+0000",
        "LastLoginDate": "2023-06-02T12:00:00.000+0000",
        "LastPasswordChangeDate": "2023-01-02T00:00:00.000+0000",
    },
]

SALESFORCE_PERMISSION_SETS = [
    {
        "Id": "0PS000000000001AAA",
        "Name": "API_Access",
        "Label": "API Access",
        "Description": "Grants API access",
        "Type": "Regular",
        "IsOwnedByProfile": False,
        "ProfileId": None,
        "PermissionsModifyAllData": False,
        "PermissionsViewAllData": False,
        "PermissionsApiEnabled": True,
        "NamespacePrefix": None,
        "CreatedDate": "2021-01-01T00:00:00.000+0000",
    },
]

SALESFORCE_PERMISSION_SET_ASSIGNMENTS = [
    {
        "Id": "0Pa000000000001AAA",
        "AssigneeId": "005000000000001AAA",
        "PermissionSetId": "0PS000000000001AAA",
    },
]

SALESFORCE_GROUPS = [
    {
        "Id": "00G000000000001AAA",
        "Name": "All Internal Users",
        "DeveloperName": "AllInternalUsers",
        "Type": "Regular",
        "RelatedId": None,
    },
    {
        "Id": "00G000000000002AAA",
        "Name": "Admins",
        "DeveloperName": "Admins",
        "Type": "Regular",
        "RelatedId": None,
    },
]

SALESFORCE_GROUP_MEMBERS = [
    # Users in "All Internal Users"
    {
        "Id": "011000000000001AAA",
        "GroupId": "00G000000000001AAA",
        "UserOrGroupId": "005000000000001AAA",
    },
    {
        "Id": "011000000000002AAA",
        "GroupId": "00G000000000001AAA",
        "UserOrGroupId": "005000000000002AAA",
    },
    # Homer in "Admins"
    {
        "Id": "011000000000003AAA",
        "GroupId": "00G000000000002AAA",
        "UserOrGroupId": "005000000000001AAA",
    },
    # Nested group: "Admins" is a member of "All Internal Users"
    {
        "Id": "011000000000004AAA",
        "GroupId": "00G000000000001AAA",
        "UserOrGroupId": "00G000000000002AAA",
    },
]

SALESFORCE_CONNECTED_APPS = [
    {
        "Id": "0Ci000000000001AAA",
        "Name": "Slack",
        "OptionsAllowAdminApprovedUsersOnly": False,
        "CreatedDate": "2022-01-01T00:00:00.000+0000",
        "LastModifiedDate": "2022-06-01T00:00:00.000+0000",
    },
]

SALESFORCE_OAUTH_TOKENS = [
    {
        "Id": "0Da000000000001AAA",
        "AppName": "Slack",
        "UserId": "005000000000001AAA",
    },
]
