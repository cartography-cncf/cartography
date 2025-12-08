GET_SERVICES_DATA = [
    {
        "id": "PIJ90N7",
        "summary": "My Application Service",
        "type": "service",
        "self": "https://api.pagerduty.com/services/PIJ90N7",
        "html_url": "https://subdomain.pagerduty.com/services/PIJ90N7",
        "name": "My Application Service",
        "auto_resolve_timeout": 14400,
        "acknowledgement_timeout": 600,
        "created_at": "2015-11-06T11:12:51-05:00",
        "status": "active",
        "alert_creation": "create_alerts_and_incidents",
        "alert_grouping_parameters": {
            "type": "intelligent",
        },
        "integrations": [
            {
                "id": "PQ12345",
                "type": "generic_email_inbound_integration_reference",
                "summary": "Email Integration",
                "self": "https://api.pagerduty.com/services/PIJ90N7/integrations/PQ12345",
                "html_url": "https://subdomain.pagerduty.com/services/PIJ90N7/integrations/PQ12345",
            },
        ],
        "escalation_policy": {
            "id": "PT20YPA",
            "type": "escalation_policy_reference",
            "summary": "Another Escalation Policy",
            "self": "https://api.pagerduty.com/escalation_policies/PT20YPA",
            "html_url": "https://subdomain.pagerduty.com/escalation_policies/PT20YPA",
        },
        "teams": [
            {
                "id": "PQ9K7I8",
                "type": "team_reference",
                "summary": "Engineering",
                "self": "https://api.pagerduty.com/teams/PQ9K7I8",
                "html_url": "https://subdomain.pagerduty.com/teams/PQ9K7I8",
            },
        ],
        "incident_urgency_rule": {
            "type": "use_support_hours",
            "during_support_hours": {
                "type": "constant",
                "urgency": "high",
            },
            "outside_support_hours": {
                "type": "constant",
                "urgency": "low",
            },
        },
        "support_hours": {
            "type": "fixed_time_per_day",
            "time_zone": "America/Lima",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "days_of_week": [
                1,
                2,
                3,
                4,
                5,
            ],
        },
        "scheduled_actions": [
            {
                "type": "urgency_change",
                "at": {
                    "type": "named_time",
                    "name": "support_hours_start",
                },
                "to_urgency": "high",
            },
        ],
    },
]

GET_INTEGRATIONS_DATA = [
    {
        "id": "PE1U9CH",
        "type": "generic_email_inbound_integration",
        "summary": "Email",
        "self": "https://api.pagerduty.com/services/PIJ90N7/integrations/PE1U9CH",
        "html_url": "https://subdomain.pagerduty.com/services/PIJ90N7/integrations/PE1U9CH",
        "name": "Email",
        "service": {
            "id": "PIJ90N7",
            "type": "service_reference",
            "summary": "My Application Service",
            "self": "https://api.pagerduty.com/services/PIJ90N7",
            "html_url": "https://subdomain.pagerduty.com/services/PIJ90N7",
        },
        "created_at": "2015-10-14T13:33:02-07:00",
        "vendor": {
            "id": "PZQ6AUS",
            "type": "vendor_reference",
            "summary": "Amazon CloudWatch",
            "self": "https://api.pagerduty.com/vendors/PZQ6AUS",
        },
        "integration_email": "my-email-based-integration@subdomain.pagerduty.com",
    },
]
