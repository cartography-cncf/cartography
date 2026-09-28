"""SHOW USER PROGRAMMATIC ACCESS TOKENS rows, as the SQL API returns them.

Every value is a string or None and every key is lowercased, which is what the SQL
API does regardless of the column's declared type.
"""

from typing import Any

SNOWFLAKE_ACCESS_TOKENS: list[dict[str, Any]] = [
    {
        "name": "donut_dashboard",
        "user_name": "HOMER",
        "role_restriction": "",
        "expires_at": "1787067633.789",
        "status": "ACTIVE",
        "comment": None,
        "created_on": "1785771633.789",
        "created_by": "HOMER",
        # A live exemption from the network policy that would otherwise gate the
        # token, which is the security-relevant field on this listing.
        "mins_to_bypass_required_network_policy": "477",
        "rotated_to": None,
    },
    {
        "name": "scram_ingest",
        "user_name": "SCRAM_BOT",
        "role_restriction": "SAFETY_INSPECTOR",
        "expires_at": "1790000000.000",
        "status": "ACTIVE",
        "comment": "used by the nightly reactor load",
        "created_on": "1785000000.000",
        "created_by": "ACCOUNTADMIN",
        "mins_to_bypass_required_network_policy": "",
        "rotated_to": "scram_ingest_v2",
    },
    {
        # An expired token still owned by a disabled user, which is the shape a
        # leftover contractor credential takes. It proves the ownership edge is
        # built from the token's own user_name rather than only for active users.
        "name": "retired_contractor",
        "user_name": "SMITHERS",
        "role_restriction": "",
        "expires_at": None,
        "status": "EXPIRED",
        "comment": None,
        "created_on": "1780000000.000",
        "created_by": "ACCOUNTADMIN",
        "mins_to_bypass_required_network_policy": None,
        "rotated_to": None,
    },
]
