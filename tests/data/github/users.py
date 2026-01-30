GITHUB_ORG_DATA = {
    "url": "https://github.com/simpsoncorp",
    "login": "SimpsonCorp",
}


GITHUB_USER_DATA = (
    [
        {
            "hasTwoFactorEnabled": None,
            "node": {
                "url": "https://github.com/hjsimpson",
                "login": "hjsimpson",
                "name": "Homer Simpson",
                "isSiteAdmin": False,
                "email": "hjsimpson@simpson.corp",
                "company": "Springfield Nuclear Power Plant",
                "organizationVerifiedDomainEmails": ["hjsimpson@burns.corp"],
            },
            "role": "MEMBER",
        },
        {
            "hasTwoFactorEnabled": None,
            "node": {
                "url": "https://github.com/lmsimpson",
                "login": "lmsimpson",
                "name": "Lisa Simpson",
                "isSiteAdmin": False,
                "email": "lmsimpson@simpson.corp",
                "company": "Simpson Residence",
            },
            "role": "MEMBER",
        },
        {
            "hasTwoFactorEnabled": True,
            "node": {
                "url": "https://github.com/mbsimpson",
                "login": "mbsimpson",
                "name": "Marge Simpson",
                "isSiteAdmin": False,
                "email": "mbsimpson@simpson.corp",
                "company": "Simpson Residence",
            },
            "role": "ADMIN",
        },
    ],
    GITHUB_ORG_DATA,
)

GITHUB_USER_DATA_AT_TIMESTAMP_2 = (
    [
        {
            "hasTwoFactorEnabled": None,
            "node": {
                "url": "https://github.com/hjsimpson",
                "login": "hjsimpson",
                "name": "Homer Simpson",
                "isSiteAdmin": False,
                "email": "hjsimpson@simpson.corp",
                "company": "Springfield Nuclear Power Plant",
                "organizationVerifiedDomainEmails": ["hjsimpson@burns.corp"],
            },
            # In timestamp 2, Homer is now an admin and no longer a member.
            # This is used to test that stale relationships are removed.
            "role": "ADMIN",
        },
        {
            "hasTwoFactorEnabled": None,
            "node": {
                "url": "https://github.com/lmsimpson",
                "login": "lmsimpson",
                "name": "Lisa Simpson",
                "isSiteAdmin": False,
                "email": "lmsimpson@simpson.corp",
                "company": "Simpson Residence",
            },
            "role": "MEMBER",
        },
        {
            "hasTwoFactorEnabled": True,
            "node": {
                "url": "https://github.com/mbsimpson",
                "login": "mbsimpson",
                "name": "Marge Simpson",
                "isSiteAdmin": False,
                "email": "mbsimpson@simpson.corp",
                "company": "Simpson Residence",
            },
            # In timestamp 2, Marge is no longer an ADMIN and is now a MEMBER.
            "role": "MEMBER",
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
            "node": {
                "url": "https://github.com/kbroflovski",
                "login": "kbroflovski",
                "name": "Kyle Broflovski",
                "isSiteAdmin": False,
                "email": "kbroflovski@south.park",
                "company": "South Park Elementary",
            },
            "organizationRole": "UNAFFILIATED",
        },
        {
            "node": {
                "url": "https://github.com/mbsimpson",
                "login": "mbsimpson",
                "name": "Marge Simpson",
                "isSiteAdmin": False,
                "email": "mbsimpson@simpson.corp",
                "company": "Simpson Residence",
            },
            "organizationRole": "OWNER",
        },
        {
            "node": {
                "url": "https://github.com/lmsimpson",
                "login": "lmsimpson",
                "name": "Lisa Simpson",
                "isSiteAdmin": False,
                "email": "lmsimpson@simpson.corp",
                "company": "Simpson Residence",
            },
            "organizationRole": "DIRECT_MEMBER",
        },
    ],
    GITHUB_ORG_DATA,
)
