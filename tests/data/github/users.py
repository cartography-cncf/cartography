GITHUB_ORG_DATA = {
    'url': 'https://example.com/my_org',
    'login': 'my_org',
}


GITHUB_USER_DATA = (
    [
        {
            'hasTwoFactorEnabled': None,
            'node': {
                'url': 'https://example.com/hjsimpson',
                'login': 'hjsimpson',
                'name': 'Homer Simpson',
                'isSiteAdmin': False,
                'email': 'hjsimpson@example.com',
                'company': 'Springfield Nuclear Power Plant',
            },
            'role': 'MEMBER',
        }, {
            'hasTwoFactorEnabled': None,
            'node': {
                'url': 'https://example.com/lmsimpson',
                'login': 'lmsimpson',
                'name': 'Lisa Simpson',
                'isSiteAdmin': False,
                'email': 'lmsimpson@example.com',
                'company': 'Simpson Residence',
            },
            'role': 'MEMBER',
        }, {
            'hasTwoFactorEnabled': True,
            'node': {
                'url': 'https://example.com/mbsimpson',
                'login': 'mbsimpson',
                'name': 'Marge Simpson',
                'isSiteAdmin': False,
                'email': 'mbsimpson@example.com',
                'company': 'Simpson Residence',
            },
            'role': 'ADMIN',
        },
    ],
    GITHUB_ORG_DATA,
)

GITHUB_USER_DATA_AT_TIMESTAMP_2 = (
    [
        {
            'hasTwoFactorEnabled': None,
            'node': {
                'url': 'https://example.com/hjsimpson',
                'login': 'hjsimpson',
                'name': 'Homer Simpson',
                'isSiteAdmin': False,
                'email': 'hjsimpson@example.com',
                'company': 'Springfield Nuclear Power Plant',
            },
            # In timestamp 2, Homer is now an admin and no longer a member.
            # This is used to test that stale relationships are removed.
            'role': 'ADMIN',
        }, {
            'hasTwoFactorEnabled': None,
            'node': {
                'url': 'https://example.com/lmsimpson',
                'login': 'lmsimpson',
                'name': 'Lisa Simpson',
                'isSiteAdmin': False,
                'email': 'lmsimpson@example.com',
                'company': 'Simpson Residence',
            },
            'role': 'MEMBER',
        }, {
            'hasTwoFactorEnabled': True,
            'node': {
                'url': 'https://example.com/mbsimpson',
                'login': 'mbsimpson',
                'name': 'Marge Simpson',
                'isSiteAdmin': False,
                'email': 'mbsimpson@example.com',
                'company': 'Simpson Residence',
            },
            # In timestamp 2, Marge is no longer an ADMIN and is now a MEMBER.
            'role': 'MEMBER',
        },
    ],
    GITHUB_ORG_DATA,
)


# Subtle differences between owner data and user data:
# 1. owner data does not include a `hasTwoFactorEnabled` field (it in unavailable in the GraphQL query for these owners)
# 2. an `organizationRole` field instead of a `role` field.  In owner data, membership within an org is not assumed, so
#    there is an 'UNAFFILIATED' value for owners of an org who are not also members of it.  (Otherwise the 'OWNER'
#    organizationRole matches the 'ADMIN' role in the user data, and the 'DIRECT_MEMBER' organizationRole matches
#    the 'MEMBER' role.)
GITHUB_ENTERPRISE_OWNER_DATA = (
    [
        {
            'node': {
                'url': 'https://example.com/kbroflovski',
                'login': 'kbroflovski',
                'name': 'Kyle Broflovski',
                'isSiteAdmin': False,
                'email': 'kbroflovski@example.com',
                'company': 'South Park Elementary',
            },
            'organizationRole': 'UNAFFILIATED',
        }, {
            'node': {
                'url': 'https://example.com/mbsimpson',
                'login': 'mbsimpson',
                'name': 'Marge Simpson',
                'isSiteAdmin': False,
                'email': 'mbsimpson@example.com',
                'company': 'Simpson Residence',
            },
            'organizationRole': 'OWNER',
        }, {
            'node': {
                'url': 'https://example.com/lmsimpson',
                'login': 'lmsimpson',
                'name': 'Lisa Simpson',
                'isSiteAdmin': False,
                'email': 'lmsimpson@example.com',
                'company': 'Simpson Residence',
            },
            'organizationRole': 'DIRECT_MEMBER',
        },
    ],
    GITHUB_ORG_DATA,
)
