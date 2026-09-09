from typing import Any

SSH_KEYS_ITEMS_PAGE_1: list[dict[str, Any]] = [
    {
        "id": "d2e0d160-2b93-4c86-ba0f-a09973bc7ce9",
        "name": "laptop",
        "fingerprint": "38:e5:5a:11:19:12:d3:36:22:a2:6a:f7:f0:69:c9:14",
    },
    {
        "id": "9a1f9e5b-4ec7-4d38-8e39-3f1a6a4a4b21",
        "name": "ci-deploy-key",
        "fingerprint": "9c:34:a1:0f:2b:88:44:7d:11:56:60:cd:e2:a5:3f:11",
    },
]

SSH_KEYS_ITEMS_PAGE_2: list[dict[str, Any]] = [
    {
        "id": "6b7e1d0f-8f3a-4a9d-9d7a-2e0b3c9a11ab",
        "name": "workstation",
        "fingerprint": "aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99",
    },
]

SSH_KEYS_PAGE_1: dict[str, Any] = {
    "page": 1,
    "per_page": 2,
    "pages": 2,
    "items": SSH_KEYS_ITEMS_PAGE_1,
}

SSH_KEYS_PAGE_2: dict[str, Any] = {
    "page": 2,
    "per_page": 2,
    "pages": 2,
    "items": SSH_KEYS_ITEMS_PAGE_2,
}

SSH_KEYS_RESPONSE: list[dict[str, Any]] = SSH_KEYS_ITEMS_PAGE_1 + SSH_KEYS_ITEMS_PAGE_2
