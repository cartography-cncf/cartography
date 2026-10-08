from datetime import datetime

from dateutil.tz import tzutc
from scaleway.cockpit.v1 import DataSource
from scaleway.cockpit.v1 import DataSourceOrigin
from scaleway.cockpit.v1 import DataSourceType
from scaleway.cockpit.v1 import Plan
from scaleway.cockpit.v1 import Token
from scaleway.cockpit.v1 import TokenScope

TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"

TEST_DATA_SOURCE_ID = "dsdsdsds-1111-4820-b8d6-0eef10cfcd6d"
TEST_TOKEN_ID = "tktktktk-1111-4820-b8d6-0eef10cfcd6d"

SCALEWAY_COCKPIT_PLAN = Plan(
    name="free",
    sample_ingestion_price=None,
    logs_ingestion_price=None,
    traces_ingestion_price=None,
    monthly_price=None,
    retention_metrics_interval=None,
    retention_logs_interval=None,
    retention_traces_interval=None,
)

SCALEWAY_COCKPIT_DATA_SOURCES = [
    DataSource(
        id=TEST_DATA_SOURCE_ID,
        project_id=TEST_PROJECT_ID,
        name="demo-metrics",
        url="https://metrics.cockpit.fr-par.scw.cloud",
        type_=DataSourceType.METRICS,
        origin=DataSourceOrigin.SCALEWAY,
        synchronized_with_grafana=True,
        retention_days=31,
        region="fr-par",
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        current_month_usage=None,
    ),
]

# `secret_key` mirrors what the live API actually returns alongside the token's
# metadata, so tests can assert it is discarded rather than merely absent from the
# fixture.
SCALEWAY_COCKPIT_TOKENS = [
    Token(
        id=TEST_TOKEN_ID,
        project_id=TEST_PROJECT_ID,
        name="demo-token",
        scopes=[TokenScope.READ_ONLY_METRICS, TokenScope.READ_ONLY_LOGS],
        region="fr-par",
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        secret_key="SUPER_SECRET_VALUE=do-not-ingest-me",
    ),
]
