ORG_IDENTITY = {
    "data": {
        "organization": {
            "url": "https://github.com/simpsoncorp",
            "login": "simpsoncorp",
        },
    },
}

ORG_IP_ALLOW_LIST = {
    "data": {"organization": {"ipAllowListEnabledSetting": "DISABLED"}},
}

ORG_NOTIFICATION_RESTRICTION = {
    "data": {
        "organization": {"notificationDeliveryRestrictionEnabledSetting": "ENABLED"},
    },
}

ORG_DOMAINS_PAGE_1 = {
    "data": {
        "organization": {
            "domains": {
                "pageInfo": {"endCursor": "cursor-1", "hasNextPage": True},
                "nodes": [
                    {
                        "id": "VD_kwDOAAABcc4AAAAA",
                        "domain": "simpsoncorp.com",
                        "isVerified": True,
                        "isApproved": False,
                        "isRequiredForPolicyEnforcement": True,
                        "createdAt": "2024-01-02T03:04:05Z",
                        "updatedAt": "2024-01-02T03:04:05Z",
                    },
                ],
            },
        },
    },
}

ORG_DOMAINS_PAGE_2 = {
    "data": {
        "organization": {
            "domains": {
                "pageInfo": {"endCursor": None, "hasNextPage": False},
                "nodes": [
                    {
                        "id": "VD_kwDOAAABcc4AAAAB",
                        "domain": "springfield-nuclear.example",
                        "isVerified": False,
                        "isApproved": True,
                        "isRequiredForPolicyEnforcement": False,
                        "createdAt": "2024-02-02T03:04:05Z",
                        "updatedAt": "2024-02-03T03:04:05Z",
                    },
                ],
            },
        },
    },
}

# GraphQL returns a FORBIDDEN error and nulls the organization for non-owners.
ORG_FORBIDDEN = {
    "data": {"organization": None},
    "errors": [
        {
            "type": "FORBIDDEN",
            "message": "simpsoncorp does not allow this credential to read domains.",
        },
    ],
}

ORG_REST = {
    "login": "simpsoncorp",
    "id": 1234,
    "html_url": "https://github.com/simpsoncorp",
    "name": "Simpson Corp",
    "is_verified": True,
    "two_factor_requirement_enabled": False,
    "default_repository_permission": "write",
    "members_can_create_repositories": True,
    "members_can_create_public_repositories": True,
    "members_can_create_private_repositories": True,
    "members_can_create_internal_repositories": False,
    "members_can_fork_private_repositories": True,
    "members_can_create_public_pages": False,
    "web_commit_signoff_required": False,
    "advanced_security_enabled_for_new_repositories": False,
    "dependabot_alerts_enabled_for_new_repositories": True,
    "dependabot_security_updates_enabled_for_new_repositories": True,
    "dependency_graph_enabled_for_new_repositories": True,
    "secret_scanning_enabled_for_new_repositories": True,
    "secret_scanning_push_protection_enabled_for_new_repositories": False,
    "secret_scanning_push_protection_custom_link_enabled": False,
}

ACTIONS_PERMISSIONS = {
    "enabled_repositories": "all",
    "allowed_actions": "selected",
    "selected_actions_url": "https://api.github.com/orgs/simpsoncorp/actions/permissions/selected-actions",
    "sha_pinning_required": False,
}

SELECTED_ACTIONS = {
    "github_owned_allowed": True,
    "verified_allowed": False,
    "patterns_allowed": ["simpsoncorp/*", "docker/login-action@*"],
}

WORKFLOW_PERMISSIONS = {
    "default_workflow_permissions": "write",
    "can_approve_pull_request_reviews": True,
}

COPILOT_BILLING = {
    "seat_breakdown": {
        "total": 12,
        "added_this_cycle": 1,
        "pending_invitation": 0,
        "pending_cancellation": 0,
        "active_this_cycle": 10,
        "inactive_this_cycle": 2,
    },
    "seat_management_setting": "assign_selected",
    "ide_chat": "enabled",
    "platform_chat": "enabled",
    "cli": "disabled",
    "public_code_suggestions": "allow",
    "plan_type": "business",
}
