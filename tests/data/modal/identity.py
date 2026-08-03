"""Shapes returned by the identity-related adapter helpers."""

from datetime import datetime
from datetime import timezone

# cartography.intel.modal.util.list_workspace_members()
MODAL_WORKSPACE_MEMBERS = [
    {
        "id": "us-ydIZVCWluEtzFTbpJvjHcK",
        "member_id": "me-u92j7zUIW7uLzofhHdpIbZ",
        "email": "alice@example.com",
        "display_name": "alice",
        "member_role": "MEMBER_ROLE_OWNER",
        "identity_provider_type": "IDENTITY_PROVIDER_TYPE_GOOGLE_OAUTH",
        "idp_external_id": None,
        "avatar_url": None,
        "joined_at": datetime(2026, 7, 29, 20, 4, 3, tzinfo=timezone.utc),
        "last_active_at": datetime(2026, 7, 29, 21, 31, 50, tzinfo=timezone.utc),
        "deleted_at": None,
    },
    {
        "id": "us-2QpLmNrTvBxWsZdKfGhYjA",
        "member_id": "me-4RtYuIoPaSdFgHjKlZxCvB",
        "email": "bob@example.com",
        "display_name": "bob",
        # A GitHub-backed member in a workspace that otherwise federates via Okta is
        # exactly the kind of finding this field exists for.
        "member_role": "MEMBER_ROLE_USER",
        "identity_provider_type": "IDENTITY_PROVIDER_TYPE_GITHUB",
        "idp_external_id": "1234567",
        "avatar_url": "https://avatars.example.com/bob.png",
        "joined_at": datetime(2026, 7, 30, 9, 0, 0, tzinfo=timezone.utc),
        "last_active_at": None,
        "deleted_at": None,
    },
]

# cartography.intel.modal.util.list_service_users()
MODAL_SERVICE_USERS = [
    {
        "id": "su-8HjKlZxCvBnMqWeRtYuIoP",
        "name": "ci-bot",
        "token_id": "ak-4pE5t96YiNM0svmOjIet7z",
        # Modal reports the creator as a workspace username, not an email.
        "created_by": "alice",
        "created_at": datetime(2026, 7, 29, 20, 10, 0, tzinfo=timezone.utc),
        "last_used_at": datetime(2026, 7, 30, 6, 0, 0, tzinfo=timezone.utc),
    },
    {
        "id": "su-1AsDfGhJkLzXcVbNmQwErT",
        "name": "stale-bot",
        "token_id": "ak-9ZxCvBnMqWeRtYuIoPaSdF",
        "created_by": "nobody-we-know",
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        # Never used: the signal for a dormant credential.
        "last_used_at": None,
    },
]

# cartography.intel.modal.util.list_proxy_tokens()
MODAL_PROXY_TOKENS = [
    {
        "id": "wk-5TgBnHyUjMkIoLpQaZwSxE",
        "token_id": "wk-5TgBnHyUjMkIoLpQaZwSxE",
        "created_at": datetime(2026, 7, 29, 20, 20, 0, tzinfo=timezone.utc),
        # Unscoped: valid against every proxy-auth-protected endpoint in the workspace.
        "scoped": False,
    },
    {
        "id": "wk-6YhNjUmIkOlPaQsWdEfRgT",
        "token_id": "wk-6YhNjUmIkOlPaQsWdEfRgT",
        "created_at": datetime(2026, 7, 30, 7, 0, 0, tzinfo=timezone.utc),
        "scoped": True,
    },
]

# cartography.intel.modal.util.get_environment_roles()
MODAL_ENVIRONMENT_ROLE_PRINCIPALS = [
    {
        "user_id": "us-ydIZVCWluEtzFTbpJvjHcK",
        "service_user_id": None,
        "email": "alice@example.com",
        "user_name": "alice",
        "service_user_name": None,
        "role": "ENVIRONMENT_ROLE_CONTRIBUTOR",
    },
    {
        "user_id": "us-2QpLmNrTvBxWsZdKfGhYjA",
        "service_user_id": None,
        "email": "bob@example.com",
        "user_name": "bob",
        "service_user_name": None,
        "role": "ENVIRONMENT_ROLE_VIEWER",
    },
    {
        "user_id": None,
        "service_user_id": "su-8HjKlZxCvBnMqWeRtYuIoP",
        "email": None,
        "user_name": None,
        "service_user_name": "ci-bot",
        "role": "ENVIRONMENT_ROLE_CONTRIBUTOR",
    },
]
