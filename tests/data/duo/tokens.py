from typing import Any
from typing import Dict
from typing import List


GET_TOKENS_RESPONSE: List[Dict[str, Any]] = [
    {
        "admins": [],
        "serial": "serial1",
        "token_id": "tokenid1",
        "totp_step": None,
        "type": "yk",
        "users": [
            {
                "alias1": None,
                "alias2": None,
                "alias3": None,
                "alias4": None,
                "aliases": {},
                "created": 1676754959,
                "email": "email1@example.com",
                "firstname": "firstname1",
                "is_enrolled": False,
                "last_directory_sync": None,
                "last_login": 1684127404,
                "lastname": "lastname1",
                "notes": "",
                "realname": "real name 1",
                "status": "active",
                "user_id": "userid1",
                "username": "username1",
            },
        ],
    },
    {
        "admins": [
            {
                "admin_id": "adminid1",
                "created": None,
                "email": "adminemail1@example.com",
                "last_login": 1684190278,
                "name": "admin real name 1",
            },
        ],
        "serial": "serial2",
        "token_id": "tokenid2",
        "totp_step": None,
        "type": "yk",
        "users": [],
    },
    {
        "admins": [],
        "serial": "serial3",
        "token_id": "tokenid3",
        "totp_step": None,
        "type": "yk",
        "users": [
            {
                "alias1": None,
                "alias2": None,
                "alias3": None,
                "alias4": None,
                "aliases": {},
                "created": 1572913142,
                "email": "email3@example.com",
                "firstname": None,
                "is_enrolled": False,
                "last_directory_sync": None,
                "last_login": 1683734550,
                "lastname": None,
                "notes": "",
                "realname": "real name 3",
                "status": "active",
                "user_id": "userid3",
                "username": "username3",
            },
        ],
    },
]
