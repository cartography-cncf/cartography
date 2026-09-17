from typing import Any

TAC_AUTHENTICATOR: dict[str, Any] = {
    "id": "aut-tac",
    "key": "tac",
    "name": "TAC",
    "status": "ACTIVE",
    "type": "tac",
    "provider": {
        "type": "TAC",
        "configuration": {
            "minTtl": 10,
            "maxTtl": 14400,
            "defaultTtl": 60,
            "length": 16,
            "complexity": {
                "numbers": True,
                "letters": False,
                "specialCharacters": False,
            },
            "multiUseAllowed": False,
        },
    },
    "_links": {},
}
