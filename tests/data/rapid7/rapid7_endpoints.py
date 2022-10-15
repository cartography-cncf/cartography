GET_HOSTS = [
    {
        # Example from https://help.rapid7.com/insightvm/en-us/api/index.html#operation/getAssets
        "addresses": [{"ip": "123.245.34.235", "mac": "12:34:56:78:90:AB"}],
        "assessedForPolicies": False,
        "assessedForVulnerabilities": True,
        "configurations": [
            {"name": "<name>", "value": "<value>"},
            {"name": "cpuinfo", "value": "Intel(R) Core(TM) iXXXX CPU @ XHz"},
            {"name": "proxies", "value": "{}"},
            {"name": "release", "value": "10"},
            {"name": "timezone", "value": "GMT-4"},
            {
                "name": "azure",
                "value": {
                    "instanceId": "c56b2c59-4e9b-4b89-85e2-13f8146eb071",
                    "resourceId": "/subscriptions/SUB/resourceGroups/RG/providers/Microsoft.Compute/virtualMachines/HOST",
                },
            },
        ],
        "databases": [
            {"description": "Microsoft SQL Server", "id": 13, "name": "MSSQL"},
        ],
        "files": [
            {
                "attributes": [{"name": "<name>", "value": "<value>"}],
                "name": "ADMIN$",
                "size": -1,
                "type": "directory",
            },
        ],
        "history": [
            {
                "date": "2018-04-09T06:23:49Z",
                "description": "",
                "scanId": 12,
                "type": "SCAN",
                "user": "",
                "version": 8,
                "vulnerabilityExceptionId": "",
            },
        ],
        "hostName": "corporate-workstation-1102DC.acme.com",
        "hostNames": [
            {"name": "corporate-workstation-1102DC.acme.com", "source": "DNS"},
        ],
        "id": 282,
        "ids": [{"id": "c56b2c59-4e9b-4b89-85e2-13f8146eb071", "source": "WQL"}],
        "ip": "182.34.74.202",
        "links": [{"href": "https://hostname:3780/api/3/...", "rel": "self"}],
        "mac": "AB:12:CD:34:EF:56",
        "os": "Microsoft Windows Server 2008 Enterprise Edition SP1",
        "osFingerprint": {
            "architecture": "x86",
            "configurations": [{"name": "<name>", "value": "<value>"}],
            "cpe": {
                "edition": "enterprise",
                "language": "",
                "other": "",
                "part": "o",
                "product": "windows_server_2008",
                "swEdition": "",
                "targetHW": "",
                "targetSW": "",
                "update": "sp1",
                "v2.2": "cpe:/o:microsoft:windows_server_2008:-:sp1:enterprise",
                "v2.3": "cpe:2.3:o:microsoft:windows_server_2008:-:sp1:enterprise:*:*:*:*:*",
                "vendor": "microsoft",
                "version": "-",
            },
            "description": "Microsoft Windows Server 2008 Enterprise Edition SP1",
            "family": "Windows",
            "id": 35,
            "product": "Windows Server 2008 Enterprise Edition",
            "systemName": "Microsoft Windows",
            "type": "Workstation",
            "vendor": "Microsoft",
            "version": "SP1",
        },
        "rawRiskScore": 31214.3,
        "riskScore": 37457.16,
        "services": [
            {
                "configurations": [{"name": "<name>", "value": "<value>"}],
                "databases": [
                    {"description": "Microsoft SQL Server", "id": 13, "name": "MSSQL"},
                ],
                "family": "",
                "links": [{"href": "https://hostname:3780/api/3/...", "rel": "self"}],
                "name": "CIFS Name Service",
                "port": 139,
                "product": "Samba",
                "protocol": "tcp",
                "userGroups": [{"id": 972, "name": "Administrators"}],
                "users": [
                    {"fullName": "Smith, John", "id": 8952, "name": "john_smith"},
                ],
                "vendor": "",
                "version": "3.5.11",
                "webApplications": [
                    {
                        "id": 30712,
                        "pages": [
                            {
                                "linkType": "html-ref",
                                "path": "/docs/config/index.html",
                                "response": 200,
                            },
                        ],
                        "root": "/",
                        "virtualHost": "102.89.22.253",
                    },
                ],
            },
        ],
        "software": [
            {
                "configurations": [{"name": "<name>", "value": "<value>"}],
                "cpe": {
                    "edition": "enterprise",
                    "language": "",
                    "other": "",
                    "part": "o",
                    "product": "windows_server_2008",
                    "swEdition": "",
                    "targetHW": "",
                    "targetSW": "",
                    "update": "sp1",
                    "v2.2": "cpe:/o:microsoft:windows_server_2008:-:sp1:enterprise",
                    "v2.3": "cpe:2.3:o:microsoft:windows_server_2008:-:sp1:enterprise:*:*:*:*:*",
                    "vendor": "microsoft",
                    "version": "-",
                },
                "description": "Microsoft Outlook 2013 15.0.4867.1000",
                "family": "Office 2013",
                "id": 0,
                "product": "Outlook 2013",
                "type": "Productivity",
                "vendor": "Microsoft",
                "version": "15.0.4867.1000",
            },
        ],
        "type": "",
        "userGroups": [{"id": 972, "name": "Administrators"}],
        "users": [{"fullName": "Smith, John", "id": 8952, "name": "john_smith"}],
        "vulnerabilities": {
            "critical": 16,
            "exploits": 4,
            "malwareKits": 0,
            "moderate": 3,
            "severe": 76,
            "total": 95,
        },
    },
]
