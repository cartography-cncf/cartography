from datetime import datetime

from dateutil.tz import tzutc
from scaleway.mailbox.v1alpha1 import Domain
from scaleway.mailbox.v1alpha1 import Mailbox

TEST_MAILBOX_DOMAIN_ID = "11111111-1111-1111-1111-111111111111"
TEST_MAILBOX_ID = "22222222-2222-2222-2222-222222222222"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_MAILBOX_EMAIL = "test@example.com"

SCALEWAY_MAILBOX_DOMAINS = [
    Domain(
        id=TEST_MAILBOX_DOMAIN_ID,
        project_id=TEST_PROJECT_ID,
        created_at=datetime(2026, 7, 10, 12, 0, 0, tzinfo=tzutc()),
        updated_at=datetime(2026, 7, 10, 12, 30, 0, tzinfo=tzutc()),
        name="example.com",
        status="ready",
        mailbox_total_count=10,
        webmail_url="https://webmail.example.com",
        imap_url="imap://imap.example.com",
        pop3_url="pop3://pop3.example.com",
        smtp_url="smtp://smtp.example.com",
        jmap_url="https://jmap.example.com",
    ),
]

SCALEWAY_MAILBOXES = [
    Mailbox(
        id=TEST_MAILBOX_ID,
        domain_id=TEST_MAILBOX_DOMAIN_ID,
        email=TEST_MAILBOX_EMAIL,
        status="ready",
        subscription_period="monthly",
        subscription_period_started_at=datetime(2026, 7, 10, 12, 0, 0, tzinfo=tzutc()),
        next_subscription_period="monthly",
        next_subscription_period_starts_at=datetime(
            2026, 8, 10, 12, 0, 0, tzinfo=tzutc()
        ),
        created_at=datetime(2026, 7, 10, 12, 0, 0, tzinfo=tzutc()),
        updated_at=datetime(2026, 7, 10, 12, 30, 0, tzinfo=tzutc()),
        deletion_scheduled_at=None,
    ),
]
