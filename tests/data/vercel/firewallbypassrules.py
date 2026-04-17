# Vercel's firewall bypass endpoint returns PascalCase field names.
VERCEL_FIREWALL_BYPASS_RULES = [
    {
        "Id": "fbr_123",
        "Domain": "example.com",
        "Ip": "203.0.113.42",
        "Note": "Office IP",
        "Action": "bypass",
        "CreatedAt": 1640995200000,
        "ActorId": "user_homer",
        "ProjectId": "prj_abc",
        "IsProjectRule": True,
    },
    {
        "Id": "fbr_456",
        "Domain": "example.org",
        "Ip": "198.51.100.17",
        "Note": "VPN IP",
        "Action": "bypass",
        "CreatedAt": 1641081600000,
        "ActorId": "user_homer",
        "ProjectId": "prj_abc",
        "IsProjectRule": True,
    },
]
