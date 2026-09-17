TENANT_ID = "00000000-1111-2222-3333-444444444444"
AAD_DEVICE_ID = "11111111-2222-3333-4444-555555555555"
MACHINES = [
    {
        "id": "machine-1",
        "computerDnsName": "laptop.example.test",
        "aadDeviceId": AAD_DEVICE_ID,
        "osPlatform": "Windows11",
        "healthStatus": "Active",
        "onboardingStatus": "Onboarded",
        "riskScore": "Medium",
        "exposureLevel": "Low",
        "lastSeen": "2026-09-17T10:00:00Z",
    },
    {"id": "machine-2", "healthStatus": "Inactive"},
]
ALERTS = [
    {
        "id": "alert-1",
        "tenantId": TENANT_ID,
        "providerAlertId": "provider-alert-1",
        "title": "Suspicious process execution",
        "severity": "medium",
        "status": "new",
        "serviceSource": "microsoftDefenderForEndpoint",
        "detectionSource": "antivirus",
        "createdDateTime": "2026-09-17T09:00:00Z",
        "categories": ["Execution"],
        "mitreTechniques": ["T1059"],
        "evidence": [
            {
                "@odata.type": "#microsoft.graph.security.deviceEvidence",
                "mdeDeviceId": "machine-1",
            },
            {
                "@odata.type": "#microsoft.graph.security.deviceEvidence",
                "mdeDeviceId": "machine-2",
            },
            {
                "@odata.type": "#microsoft.graph.security.deviceEvidence",
                "mdeDeviceId": "machine-outside-retention",
            },
            {"@odata.type": "#microsoft.graph.security.userEvidence"},
        ],
    },
]
