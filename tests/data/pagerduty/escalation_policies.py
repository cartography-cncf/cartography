GET_ESCALATION_POLICY_DATA = [
    {
        "id": "PANZZEQ",
        "type": "escalation_policy",
        "summary": "Engineering Escalation Policy",
        "on_call_handoff_notifications": "if_has_services",
        "self": "https://api.pagerduty.com/escalation_policies/PANZZEQ",
        "html_url": "https://subdomain.pagerduty.com/escalation_policies/PANZZEQ",
        "name": "Engineering Escalation Policy",
        "escalation_rules": [
            {
                "id": "PANZZEA",
                "escalation_delay_in_minutes": 30,
                "targets": [
                    {
                        "id": "PXPGF42",
                        "summary": "Earline Greenholt",
                        "type": "user_reference",
                        "self": "https://api.pagerduty.com/users/PXPGF42",
                        "html_url": "https://subdomain.pagerduty.com/users/PXPGF42",
                    },
                    {
                        "id": "PI7DH85",
                        "summary": "Daily Engineering Rotation",
                        "type": "schedule_reference",
                        "self": "https://api.pagerduty.com/schedules/PI7DH85",
                        "html_url": "https://subdomain.pagerduty.com/schedules/PI7DH85",
                    },
                ],
            },
        ],
        "services": [
            {
                "id": "PIJ90N7",
                "type": "service_reference",
                "summary": "My Mail Service",
                "self": "https://api.pagerduty.com/services/PIJ90N7",
                "html_url": "https://subdomain.pagerduty.com/services/PIJ90N7",
            },
        ],
        "num_loops": 0,
        "teams": [
            {
                "id": "PQ9K7I8",
                "type": "team_reference",
                "summary": "Engineering",
                "self": "https://api.pagerduty.com/teams/PQ9K7I8",
                "html_url": "https://subdomain.pagerduty.com/teams/PQ9K7I8",
            },
        ],
    },
]
