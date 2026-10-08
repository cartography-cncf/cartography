from typing import Any

ROUTER_AGGREGATED_RESPONSE: dict[str, Any] = {
    "id": "projects/project-abc/aggregated/routers",
    "items": {
        "regions/us-central1": {
            "routers": [
                {
                    "name": "router-no-nats",
                    "selfLink": "https://www.googleapis.com/compute/v1/projects/"
                    "project-abc/regions/us-central1/routers/router-no-nats",
                    "network": "https://www.googleapis.com/compute/v1/projects/"
                    "project-abc/global/networks/default",
                },
                {
                    "name": "router-with-nats",
                    "selfLink": "https://www.googleapis.com/compute/v1/projects/"
                    "project-abc/regions/us-central1/routers/router-with-nats",
                    "network": "https://www.googleapis.com/compute/v1/projects/"
                    "project-abc/global/networks/default",
                    "nats": [
                        {
                            "name": "nat-logging-on",
                            "natIpAllocateOption": "AUTO_ONLY",
                            "sourceSubnetworkIpRangesToNat": "ALL_SUBNETWORKS_ALL_IP_RANGES",
                            "logConfig": {
                                "enable": True,
                                "filter": "ALL",
                            },
                        },
                        {
                            "name": "nat-logging-off",
                            "natIpAllocateOption": "MANUAL_ONLY",
                            "sourceSubnetworkIpRangesToNat": "LIST_OF_SUBNETWORKS",
                            "logConfig": {
                                "enable": False,
                                "filter": "ERRORS_ONLY",
                            },
                        },
                        {
                            "name": "nat-no-log-config",
                            "natIpAllocateOption": "AUTO_ONLY",
                            "sourceSubnetworkIpRangesToNat": "ALL_SUBNETWORKS_ALL_IP_RANGES",
                        },
                    ],
                },
            ],
        },
    },
}

ROUTER_PAGE_1_RESPONSE: dict[str, Any] = {
    "id": "projects/project-abc/aggregated/routers",
    "items": {
        "regions/us-central1": {
            "routers": [
                {
                    "name": "router-page-1",
                },
            ],
        },
    },
}

ROUTER_PAGE_2_RESPONSE: dict[str, Any] = {
    "id": "projects/project-abc/aggregated/routers",
    "items": {
        "regions/us-central1": {
            "routers": [
                {
                    "name": "router-page-2",
                },
            ],
        },
    },
}
