LIST_SCHEDULES_DATA = [
    {
        "id": "PI7DH85",
        "type": "schedule",
        "summary": "Daily Engineering Rotation",
        "self": "https://api.pagerduty.com/schedules/PI7DH85",
        "html_url": "https://subdomain.pagerduty.com/schedules/PI7DH85",
        "name": "Daily Engineering Rotation",
        "time_zone": "America/New_York",
        "description": "Rotation schedule for engineering",
        "escalation_policies": [
            {
                "id": "PT20YPA",
                "type": "escalation_policy_reference",
                "summary": "Another Escalation Policy",
                "self": "https://api.pagerduty.com/escalation_policies/PT20YPA",
                "html_url": "https://subdomain.pagerduty.com/escalation_policies/PT20YPA",
            },
        ],
        "users": [
            {
                "id": "PXPGF42",
                "type": "user_reference",
                "summary": "Earline Greenholt",
                "self": "https://api.pagerduty.com/users/PXPGF42",
                "html_url": "https://subdomain.pagerduty.com/users/PXPGF42",
            },
        ],
        "schedule_layers": [
            {
                "name": "Night Shift",
                "start": "2015-11-06T20:00:00-05:00",
                "end": "2016-11-06T20:00:00-05:00",
                "rotation_virtual_start": "2015-11-06T20:00:00-05:00",
                "rotation_turn_length_seconds": 86400,
                "users": [
                    {
                        "user": {
                            "id": "PXPGF42",
                            "type": "user_reference",
                            "summary": "Earline Greenholt",
                            "self": "https://api.pagerduty.com/users/PXPGF42",
                            "html_url": "https://subdomain.pagerduty.com/users/PXPGF42",
                        },
                    },
                ],
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "08:00:00",
                        "duration_seconds": 32400,
                    },
                ],
            },
        ],
    },
]
