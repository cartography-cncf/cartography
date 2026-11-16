API_URL = "https://app.sentra.io"
API_KEY = "sentra-test-api-key"

ORGANIZATION_ID = 4242
TENANT_ID = str(ORGANIZATION_ID)
AWS_ACCOUNT_ID = "123456789012"

CURRENT_USER = {
    "email": "cartography@example.com",
    "hashed_org": "hashed-org",
    "hashed_user": "hashed-user",
    "id": None,
    "name": "cartography-service-account",
    "notify_on_scan_completion": False,
    "organization_id": ORGANIZATION_ID,
    "organization_name": "Example Org",
    "organization_type": "customer",
    "pylon_email_hash": "hash",
    "role_id": 1,
    "role_name": "Viewer",
}

DATA_CLASS_EMAIL_ID = "class-email"
DATA_CLASS_AWS_KEY_ID = "class-aws-access-key"

DATA_CLASSES = [
    {
        "id": DATA_CLASS_EMAIL_ID,
        "name": "Email Address",
        "description": "An email address.",
        "category": "Personal",
        "classifier_types": [],
        "confidence_threshold": 0.8,
        "created_at": "2025-01-10T00:00:00Z",
        "enabled": True,
        "experimental": False,
        "findings_count": 120,
        "is_ai": False,
        "organization_id": ORGANIZATION_ID,
        "sensitivity_weight": 2,
        "source": "SENTRA",
        "type": "FINDING_LEVEL",
    },
    {
        "id": DATA_CLASS_AWS_KEY_ID,
        "name": "AWS Access Key",
        "description": "An AWS access key ID and secret.",
        "category": "Credentials",
        "classifier_types": [],
        "confidence_threshold": 0.9,
        "created_at": "2025-01-10T00:00:00Z",
        "enabled": True,
        "experimental": False,
        "findings_count": 3,
        "is_ai": False,
        "organization_id": ORGANIZATION_ID,
        "sensitivity_weight": 5,
        "source": "SENTRA",
        "type": "FINDING_LEVEL",
    },
]

S3_STORE_ID = "store-s3-logs"
S3_BUCKET_NAME = "example-app-logs"
RDS_STORE_ID = "store-rds-orders"
RDS_INSTANCE_ARN = f"arn:aws:rds:us-east-1:{AWS_ACCOUNT_ID}:db:orders"
SNOWFLAKE_STORE_ID = "store-snowflake-analytics"


def _store(**overrides):
    store = {
        "Connector__account_id": AWS_ACCOUNT_ID,
        "Connector__account_type": "AWS",
        "Connector__environment": "production",
        "Connector__name": "prod-aws",
        "alerts_count": 0,
        "category": None,
        "connector_id": 7,
        "context_labels": [],
        "context_labels_counts": [],
        "created_at": "2024-06-01T00:00:00Z",
        "custom_tags": None,
        "data_classes": [],
        "database_engine": None,
        "drive_type": None,
        "encryption_method": None,
        "findings_count": 0,
        "hosting_service": None,
        "is_backed_up": None,
        "is_encrypted": True,
        "is_encrypted_in_transit": True,
        "is_logging_enabled": False,
        "is_managed": True,
        "last_scan_status": "SCANNED",
        "last_scanned": "2026-11-15T03:00:00Z",
        "native_unique_id": None,
        "owner_tags": {},
        "public_access_level": "private",
        "region": "us-east-1",
        "scan_status": "SCANNED",
        "scan_status_breakdown": [],
        "sensitivity_level": 0,
        "used_storage": 1024,
    }
    store.update(overrides)
    return store


DATA_STORES = [
    # An S3 store without an ARN: linked to its bucket by name.
    _store(
        id=S3_STORE_ID,
        name=S3_BUCKET_NAME,
        category="Object Storage",
        hosting_service="s3",
        encryption_method="S3:SSE-KMS",
        public_access_level="can_be_public",
        sensitivity_level=3,
        findings_count=123,
        alerts_count=1,
        data_classes=[
            {
                "id": DATA_CLASS_EMAIL_ID,
                "name": "Email Address",
                "category": "Personal",
            },
            {
                "id": DATA_CLASS_AWS_KEY_ID,
                "name": "AWS Access Key",
                "category": "Credentials",
            },
        ],
    ),
    # An RDS store whose native ID is the instance ARN.
    _store(
        id=RDS_STORE_ID,
        name="orders",
        category="RDBMS",
        hosting_service="rds",
        database_engine="postgres",
        database_engine_version="15.4",
        native_unique_id=RDS_INSTANCE_ARN,
        sensitivity_level=2,
        data_classes=[
            {
                "id": DATA_CLASS_EMAIL_ID,
                "name": "Email Address",
                "category": "Personal",
            },
        ],
    ),
    # A SaaS store: ingested without a cloud resource link.
    _store(
        id=SNOWFLAKE_STORE_ID,
        name="ANALYTICS",
        category="Data Warehouse",
        hosting_service="snowflake",
        Connector__account_id="xy12345",
        Connector__account_type="SNOWFLAKE",
        Connector__name="snowflake-prod",
        connector_id=8,
        region=None,
    ),
]

STORE_ALERT_ID = "alert-public-credentials"
ROLE_ALERT_ID = "alert-role-excessive-access"
ROLE_ARN = f"arn:aws:iam::{AWS_ACCOUNT_ID}:role/data-pipeline"


def _alert(**overrides):
    alert = {
        "Connector__account_id": AWS_ACCOUNT_ID,
        "Connector__account_type": "AWS",
        "Connector__environment": "production",
        "Connector__name": "prod-aws",
        "Policy__status": "enabled",
        "Policy__type": "rule_based",
        "connector_id": 7,
        "content": {"type": "VIOLATED_STORE", "violated_asset_ids": []},
        "controls": [],
        "created_at": "2026-11-01T00:00:00Z",
        "data_classes": [],
        "frameworks": [],
        "last_modified": "2026-11-14T00:00:00Z",
        "occurrences": 1,
        "opened_at": "2026-11-01T00:00:00Z",
        "organization_id": ORGANIZATION_ID,
        "recommendation": None,
        "risk_type": None,
        "sensitivity_level": 0,
        "status": "opened",
        "status_reason": "none",
        "tags": [],
        "total_violated_assets_count": None,
    }
    alert.update(overrides)
    return alert


ALERTS = [
    _alert(
        id=STORE_ALERT_ID,
        name="Credentials in a store that can be public",
        description="The store holds credentials and can be made public.",
        recommendation="Block public access to the bucket.",
        severity="critical",
        type="VIOLATED_STORE",
        risk_type="exposed_data",
        policy_id="policy-public-creds",
        frameworks=["SOC2"],
        entity_type="STORE",
        entity_id=S3_STORE_ID,
        entity={"name": S3_BUCKET_NAME, "owners": [], "cloud_unique_id": None},
        sensitivity_level=3,
        data_classes=[
            {
                "id": DATA_CLASS_AWS_KEY_ID,
                "name": "AWS Access Key",
                "category": "Credentials",
            },
        ],
        total_violated_assets_count=4,
    ),
    _alert(
        id=ROLE_ALERT_ID,
        name="Role with access to sensitive data it never uses",
        description="The role can read sensitive data stores.",
        severity="high",
        status="in_progress",
        type="VIOLATED_IAM_ROLE",
        risk_type="excessive_access",
        policy_id="policy-unused-access",
        content={"type": "VIOLATED_IAM_ROLE"},
        entity_type="IAM_ROLE",
        entity_id="identity-role-data-pipeline",
        entity={"name": "data-pipeline", "owners": [], "cloud_unique_id": ROLE_ARN},
    ),
]
