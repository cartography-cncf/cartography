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
    ],
}
