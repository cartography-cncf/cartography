CLOUDFLARE_WORKER_ROUTES = [
    {
        "id": "7c1e5f3a9b2d4c6e8f0a1b2c3d4e5f60",
        "pattern": "photos.simpson.corp/resize/*",
        "script": "donut-image-resizer",
    },
    {
        "id": "8d2f6a4b0c3e5d7f9a1b2c3d4e5f6071",
        "pattern": "api.simpson.corp/reactor/*",
        "script": "reactor-status-api",
    },
    # A route can exist without a script attached, in which case requests fall
    # through to the origin.
    {
        "id": "9e3a7b5c1d4f6e8a0b2c3d4e5f607182",
        "pattern": "legacy.simpson.corp/*",
    },
]
