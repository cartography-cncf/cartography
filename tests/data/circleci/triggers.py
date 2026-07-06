# Raw items of GET /projects/{id}/pipeline-definitions/{def_id}/triggers,
# keyed by pipeline-definition id.
CIRCLECI_TRIGGERS = {
    "def-1": [
        {
            "id": "trig-1",
            "event_name": "push",
            "event_preset": "all-pushes",
            "event_source": {"provider": "github_app", "repo": "acme/web"},
            "checkout_ref": "main",
            "config_ref": "main",
            "disabled": False,
            "parameters": {},
        },
        {
            # A scheduled trigger: how scheduled pipeline runs are modelled.
            "id": "trig-2",
            "event_name": "nightly",
            "description": "nightly build",
            "event_source": {
                "provider": "schedule",
                "schedule": {
                    "attribution_actor": {"id": "user-9999-zzzz"},
                    "cron_expression": "0 19 6 * *",
                },
            },
            "checkout_ref": "main",
            "config_ref": "main",
            "disabled": True,
        },
    ],
}
