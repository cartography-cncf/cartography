ORG_LOG_SINKS = [
    {
        "name": "organizations/123456789012/sinks/org-audit-sink",
        "destination": "bigquery.googleapis.com/projects/log-project/datasets/audit_logs",
        "filter": 'logName:"cloudaudit.googleapis.com/activity"',
        "description": "Organization audit sink",
        "disabled": False,
        "includeChildren": True,
        "writerIdentity": "serviceAccount:org-writer@gcp-sa-logging.iam.gserviceaccount.com",
        "outputVersionFormat": "V2",
    },
]

FOLDER_LOG_SINKS = [
    {
        "name": "folders/987654321098/sinks/folder-disabled-sink",
        "destination": "storage.googleapis.com/folder-audit-logs",
        "filter": 'logName:"cloudaudit.googleapis.com/data_access"',
        "disabled": True,
        "writerIdentity": "serviceAccount:folder-writer@gcp-sa-logging.iam.gserviceaccount.com",
    },
]

PROJECT_LOG_SINKS = [
    {
        "name": "projects/test-project/sinks/project-system-event-sink",
        "destination": "pubsub.googleapis.com/projects/log-project/topics/system-events",
        "filter": 'logName:"cloudaudit.googleapis.com/system_event"',
        "disabled": False,
        "includeChildren": False,
        "writerIdentity": "serviceAccount:project-writer@gcp-sa-logging.iam.gserviceaccount.com",
    },
]
