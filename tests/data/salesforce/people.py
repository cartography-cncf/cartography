# Mock Salesforce SOQL query responses. Each record carries the Salesforce-internal
# "attributes" key that the REST API attaches, so tests also exercise strip_attributes().

SALESFORCE_ORGANIZATION = {
    "attributes": {
        "type": "Organization",
        "url": "/services/data/v60.0/sobjects/Organization/00Dxx0000001gPLEAY",
    },
    "Id": "00Dxx0000001gPLEAY",
    "Name": "Simpson Corp",
    "InstanceName": "NA139",
    "OrganizationType": "Enterprise Edition",
    "IsSandbox": False,
}

SALESFORCE_PROFILES = [
    {
        "attributes": {"type": "Profile"},
        "Id": "00exx000000Admin",
        "Name": "System Administrator",
        "UserType": "Standard",
    },
    {
        "attributes": {"type": "Profile"},
        "Id": "00exx000000Stand",
        "Name": "Standard User",
        "UserType": "Standard",
    },
]

SALESFORCE_PERMISSION_SETS = [
    {
        "attributes": {"type": "PermissionSet"},
        "Id": "0PSxx00000Sales",
        "Name": "Sales_Access",
        "Label": "Sales Access",
        "Type": "Regular",
        "IsOwnedByProfile": False,
    },
    {
        "attributes": {"type": "PermissionSet"},
        "Id": "0PSxx00000Repor",
        "Name": "Report_Builder",
        "Label": "Report Builder",
        "Type": "Regular",
        "IsOwnedByProfile": False,
    },
]

SALESFORCE_USERS = [
    {
        "attributes": {"type": "User"},
        "Id": "005xx0000Marge",
        "Username": "mbsimpson@simpson.corp",
        "Name": "Marge Simpson",
        "Email": "mbsimpson@simpson.corp",
        "IsActive": True,
        "UserType": "Standard",
        "ProfileId": "00exx000000Admin",
    },
    {
        "attributes": {"type": "User"},
        "Id": "005xx0000Homer",
        "Username": "hjsimpson@simpson.corp",
        "Name": "Homer Simpson",
        "Email": "hjsimpson@simpson.corp",
        "IsActive": True,
        "UserType": "Standard",
        "ProfileId": "00exx000000Stand",
    },
]

# Marge has both permission sets; Homer has only Sales_Access.
SALESFORCE_PERMISSION_SET_ASSIGNMENTS = [
    {
        "attributes": {"type": "PermissionSetAssignment"},
        "AssigneeId": "005xx0000Marge",
        "PermissionSetId": "0PSxx00000Sales",
    },
    {
        "attributes": {"type": "PermissionSetAssignment"},
        "AssigneeId": "005xx0000Marge",
        "PermissionSetId": "0PSxx00000Repor",
    },
    {
        "attributes": {"type": "PermissionSetAssignment"},
        "AssigneeId": "005xx0000Homer",
        "PermissionSetId": "0PSxx00000Sales",
    },
]
