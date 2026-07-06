# Raw items of GET /project/{slug}/schedule.
CIRCLECI_SCHEDULES = [
    {
        "id": "sched-1",
        "name": "nightly",
        "description": "Nightly build",
        "project_slug": "gh/acme/web",
        "actor": {"id": "user-9999-zzzz", "login": "alice", "name": "Alice Example"},
        "timetable": {
            "per-hour": 1,
            "hours-of-day": [0],
            "days-of-week": ["MON", "TUE"],
        },
    },
]
