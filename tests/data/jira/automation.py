from tests.data.jira.access import CLOUD_ID

RULE_UUID_PROJECT = "aaaaaaaa-1111-4111-8111-111111111111"
RULE_UUID_GLOBAL = "bbbbbbbb-2222-4222-8222-222222222222"

SLACK_TEAM_ID = "T01234567"
SLACK_TOKEN_PART = "fakeSlackToken999"
SLACK_WEBHOOK_URL = (
    f"https://hooks.slack.com/services/{SLACK_TEAM_ID}/B09876543/{SLACK_TOKEN_PART}"
)
GITHUB_API_URL = "https://api.github.com/repos/Example-Org/Service-Repo/dispatches"
GITHUB_REPO_ID = "https://github.com/Example-Org/Service-Repo"
UNRELATED_WEBHOOK_URL = "https://hooks.example.com/ingest?token=FAKE-SECRET-123"
SMART_VALUE_URL = "https://{{webhook.host}}/api/event"
FAKE_SECRET = "FAKE-SECRET-123"

SUMMARY_PAGE_1 = {
    "links": {
        "self": f"https://api.atlassian.com/automation/public/jira/{CLOUD_ID}/rest/v1/rule/summary?limit=100",
        "next": "?cursor=cursor-page-2&limit=100",
        "prev": None,
    },
    "data": [
        {
            "uuid": RULE_UUID_PROJECT,
            "name": "Notify GitHub and Slack on issue create",
            "state": "ENABLED",
            "description": "Project-scoped rule",
            "authorAccountId": "user-1",
            "actorAccountId": "user-1",
            "created": 1700000000000,
            "updated": 1700000100000,
            "labels": [],
            "ruleScopeARIs": [f"ari:cloud:jira:{CLOUD_ID}:project/100"],
        }
    ],
}

SUMMARY_PAGE_2 = {
    "links": {
        "self": f"https://api.atlassian.com/automation/public/jira/{CLOUD_ID}/rest/v1/rule/summary?cursor=cursor-page-2&limit=100",
        "next": None,
        "prev": None,
    },
    "data": [
        {
            "uuid": RULE_UUID_GLOBAL,
            "name": "Global incoming webhook relay",
            "state": "DISABLED",
            "description": "Global rule with incoming webhook",
            "authorAccountId": "user-1",
            "actorAccountId": "user-1",
            "created": 1700000200000,
            "updated": 1700000300000,
            "labels": [],
            "ruleScopeARIs": [f"ari:cloud:jira:{CLOUD_ID}:site/{CLOUD_ID}"],
        }
    ],
}

RULE_DETAIL_PROJECT = {
    "rule": {
        "uuid": RULE_UUID_PROJECT,
        "name": "Notify GitHub and Slack on issue create",
        "state": "ENABLED",
        "description": "Project-scoped rule",
        "canOtherRuleTrigger": False,
        "notifyOnError": "FIRSTERROR",
        "authorAccountId": "user-1",
        "actor": {"type": "ACCOUNT_ID", "actor": "user-1"},
        "trigger": {
            "component": "TRIGGER",
            "type": "jira.issue.event.trigger:created",
            "value": {},
            "conditions": [],
            "id": "trigger-1",
        },
        "components": [
            {
                "component": "ACTION",
                "type": "jira.issue.outgoing.webhook",
                "value": {
                    "url": GITHUB_API_URL,
                    "urlSecure": False,
                    "headers": [],
                    "method": "POST",
                },
                "children": [],
                "conditions": [],
            },
            {
                "component": "BRANCH",
                "type": "jira.issue.related",
                "value": {},
                "conditions": [],
                "children": [
                    {
                        "component": "ACTION",
                        "type": "slack.notification",
                        "value": {
                            "webhookUrl": SLACK_WEBHOOK_URL,
                            "body": "Issue created",
                            "channel": "#alerts",
                            "automationSender": "Jira",
                            "webhookUrlSecure": False,
                        },
                        "children": [],
                        "conditions": [],
                    }
                ],
            },
        ],
        "ruleScopeARIs": [f"ari:cloud:jira:{CLOUD_ID}:project/100"],
        "labels": [],
        "writeAccessType": "OWNER_ONLY",
        "collaborators": [],
        "created": 1700000000000,
        "updated": 1700000100000,
    },
    "connections": [],
}

RULE_DETAIL_GLOBAL = {
    "rule": {
        "uuid": RULE_UUID_GLOBAL,
        "name": "Global incoming webhook relay",
        "state": "DISABLED",
        "description": "Global rule with incoming webhook",
        "canOtherRuleTrigger": True,
        "notifyOnError": "NEVER",
        "authorAccountId": "user-1",
        "actor": {"type": "RULE_ACTOR_APP", "actor": "automation-app"},
        "trigger": {
            "component": "TRIGGER",
            "type": "jira.incoming.webhook",
            "value": {},
            "conditions": [],
            "id": "trigger-2",
        },
        "components": [
            {
                "component": "ACTION",
                "type": "jira.issue.outgoing.webhook",
                "value": {
                    "url": UNRELATED_WEBHOOK_URL,
                    "urlSecure": False,
                    "headers": [
                        {
                            "id": "h-1",
                            "name": "Authorization",
                            "value": f"Bearer {FAKE_SECRET}",
                            "headerSecure": False,
                        }
                    ],
                    "customBody": f'{{"secret": "{FAKE_SECRET}"}}',
                    "method": "POST",
                },
                "children": [],
                "conditions": [],
            },
            {
                "component": "ACTION",
                "type": "jira.issue.outgoing.webhook",
                "value": {
                    "url": SMART_VALUE_URL,
                    "urlSecure": False,
                    "headers": [],
                    "method": "POST",
                },
                "children": [],
                "conditions": [],
            },
        ],
        "ruleScopeARIs": [f"ari:cloud:jira:{CLOUD_ID}:site/{CLOUD_ID}"],
        "labels": [],
        "writeAccessType": "ADMIN_ONLY",
        "collaborators": [],
        "created": 1700000200000,
        "updated": 1700000300000,
    },
    "connections": [],
}
