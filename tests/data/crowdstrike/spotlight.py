GET_SPOTLIGHT_VULNERABILITIES = [
    {
        "id": "00000000000000000000000000000000_00000000000000000000000000000000",
        "cid": "11111111111111111111111111111111",
        "aid": "00000000000000000000000000000000",
        "created_timestamp": "2022-03-14T05:04:27Z",
        "updated_timestamp": "2022-03-14T13:33:19Z",
        "status": "open",
        "apps": [
            {
                "product_name_version": "e2fsprogs 1.42.9-12.amzn2.0.2",
                "sub_status": "open",
                "remediation": {
                    "ids": ["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"],
                },
            },
        ],
        "app": {
            "product_name_version": "e2fsprogs 1.42.9-12.amzn2.0.2",
        },
        "cve": {
            "id": "CVE-2019-5094",
            "base_score": 6.7,
            "severity": "MEDIUM",
            "exploit_status": 30,
            "exprt_rating": "LOW",
            "description": "An exploitable code execution...",
            "published_date": "2019-09-24T22:15:00Z",
            "references": ["https://www.debian.org/security/2019/dsa-4535"],
            "exploitability_score": 0.8,
            "impact_score": 5.9,
            "vector": "CVSS:3.1/AV:L/AC:L/PR:H/UI:N/S:U/C:H/I:H/A:H",
        },
        "host_info": {
            "hostname": "ip-10-0-0-1.us-east-1.compute.internal",
            "local_ip": "10.0.0.1",
            "machine_domain": "",
            "os_version": "Amazon Linux 2",
            "ou": "",
            "site_name": "",
            "system_manufacturer": "Amazon EC2",
            "groups": [
                {
                    "id": "00000000000000000000000000000000",
                    "name": "test_group",
                },
            ],
            "tags": ["test"],
            "platform": "Linux",
        },
        "remediation": {
            "ids": ["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"],
            "entities": [
                {
                    "id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                    "reference": "Amazon Linux e2fsprogs",
                    "title": "Update Amazon Linux e2fsprogs",
                    "action": "Update e2fsprogs on Amazon Linux 2",
                    "link": "",
                },
            ],
        },
    },
]
