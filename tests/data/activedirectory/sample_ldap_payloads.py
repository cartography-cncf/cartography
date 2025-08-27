MOCK_FOREST_ROOTDSE = {
    "objectGUID": b"\x00" * 16,
    "rootDomainNamingContext": "dc=example,dc=com",
    "forestFunctionality": "7",
}

MOCK_DOMAINS = [
    {
        "objectGUID": b"\x01" * 16,
        "dnsRoot": "example.com",
        "nETBIOSName": "EXAMPLE",
        "objectSid": b"\x01\x05\x00\x00\x00\x00\x00\x05\x15\x00\x00\x00\xaa\xaa\xaa\xaa\xbb\xbb\xbb\xbb\xcc\xcc\xcc\xcc",
    }
]

MOCK_OUS = [
    {
        "objectGUID": b"\x02" * 16,
        "distinguishedName": "ou=Engineering,dc=example,dc=com",
        "name": "Engineering",
        "gPLink": None,
    }
]

MOCK_GROUPS = [
    {
        "objectGUID": b"\x03" * 16,
        "distinguishedName": "cn=Domain Admins,cn=Users,dc=example,dc=com",
        "sAMAccountName": "Domain Admins",
        "objectSid": b"\x01\x05\x00\x00\x00\x00\x00\x05\x15\x00\x00\x00\xaa\xaa\xaa\xaa\xbb\xbb\xbb\xbb\xcc\xcc\xcc\xcc\x1f\x02\x00\x00",
        "groupType": 0,
        "member": [
            "cn=Alice,ou=Engineering,dc=example,dc=com",
        ],
        "memberOf": [],
    }
]

MOCK_USERS = [
    {
        "objectGUID": b"\x04" * 16,
        "distinguishedName": "cn=Alice,ou=Engineering,dc=example,dc=com",
        "userPrincipalName": "alice@example.com",
        "sAMAccountName": "alice",
        "objectSid": b"\x01\x05\x00\x00\x00\x00\x00\x05\x15\x00\x00\x00\xaa\xaa\xaa\xaa\xbb\xbb\xbb\xbb\xcc\xcc\xcc\xcc\x2a\x00\x00\x00",
        "userAccountControl": 512,
        "lastLogonTimestamp": None,
        "pwdLastSet": None,
        "servicePrincipalName": [],
        "memberOf": ["cn=Domain Admins,cn=Users,dc=example,dc=com"],
    }
]

