ORG_AUDIT_CONFIGS = [
    {
        "service": "allServices",
        "auditLogConfigs": [
            {"logType": "ADMIN_READ"},
            {"logType": "DATA_READ"},
            {"logType": "DATA_WRITE"},
        ],
    },
    {
        "service": "cloudtasks.googleapis.com",
        "auditLogConfigs": [
            {"logType": "DATA_READ"},
        ],
    },
    {
        "service": "empty.googleapis.com",
        "auditLogConfigs": [],
    },
    {
        "service": "exempted.googleapis.com",
        "auditLogConfigs": [
            {
                "logType": "DATA_READ",
                "exemptedMembers": [
                    "serviceAccount:test@example.iam.gserviceaccount.com",
                ],
            },
        ],
    },
]

FOLDER_AUDIT_CONFIGS = [
    {
        "service": "allServices",
        "auditLogConfigs": [
            {"logType": "ADMIN_READ"},
            {"logType": "DATA_WRITE"},
        ],
    },
]

PROJECT_AUDIT_CONFIGS = [
    {
        "service": "cloudtasks.googleapis.com",
        "auditLogConfigs": [
            {"logType": "DATA_READ"},
            {"logType": "DATA_WRITE"},
        ],
    },
]
