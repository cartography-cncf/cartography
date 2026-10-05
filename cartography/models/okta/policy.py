from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class OktaPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Unique Okta policy identifier.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    name: PropertyRef = PropertyRef("name", description="Policy name.")
    description: PropertyRef = PropertyRef(
        "description", description="Policy description."
    )
    type: PropertyRef = PropertyRef(
        "type",
        extra_index=True,
        description=(
            "Policy type: `OKTA_SIGN_ON` (global session), `PASSWORD`, "
            "`ACCESS_POLICY` (app authentication), `MFA_ENROLL` (authenticator "
            "enrollment), or `PROFILE_ENROLLMENT`."
        ),
    )
    status: PropertyRef = PropertyRef(
        "status", description="Policy status, `ACTIVE` or `INACTIVE`."
    )
    priority: PropertyRef = PropertyRef(
        "priority",
        description="Evaluation order among policies of the same type; 1 is evaluated first.",
    )
    system: PropertyRef = PropertyRef(
        "system",
        description="Whether Okta created the policy, such as the default policy of each type.",
    )
    created: PropertyRef = PropertyRef(
        "created", description="Time when the policy was created."
    )
    okta_last_updated: PropertyRef = PropertyRef(
        "okta_last_updated", description="Time when Okta last updated the policy."
    )
    group_include_ids: PropertyRef = PropertyRef(
        "group_include_ids",
        description="IDs of the Okta groups the policy applies to.",
    )
    group_exclude_ids: PropertyRef = PropertyRef(
        "group_exclude_ids",
        description="IDs of the Okta groups excluded from the policy.",
    )
    auth_provider: PropertyRef = PropertyRef(
        "auth_provider",
        description=(
            "`PASSWORD` policies only. Credential provider the policy governs: `OKTA`, "
            "`ACTIVE_DIRECTORY`, or `LDAP`."
        ),
    )
    application_ids: PropertyRef = PropertyRef(
        "application_ids",
        description=(
            "`ACCESS_POLICY` only. IDs of every app the authentication policy is assigned "
            "to, including first-party apps that have no `OktaApplication` node."
        ),
    )
    first_party_app_names: PropertyRef = PropertyRef(
        "first_party_app_names",
        description=(
            "`ACCESS_POLICY` only. Okta first-party apps the authentication policy is "
            "assigned to, for example `saasure` (Okta Admin Console) and `okta_enduser` "
            "(Okta Dashboard). The Applications API does not list these apps, so they "
            "have no `OktaApplication` node."
        ),
    )
    password_min_length: PropertyRef = PropertyRef(
        "password_min_length",
        description="`PASSWORD` policies only. Minimum password length.",
    )
    password_min_lowercase: PropertyRef = PropertyRef(
        "password_min_lowercase",
        description="`PASSWORD` policies only. Minimum number of lowercase characters.",
    )
    password_min_uppercase: PropertyRef = PropertyRef(
        "password_min_uppercase",
        description="`PASSWORD` policies only. Minimum number of uppercase characters.",
    )
    password_min_number: PropertyRef = PropertyRef(
        "password_min_number",
        description="`PASSWORD` policies only. Minimum number of numeric characters.",
    )
    password_min_symbol: PropertyRef = PropertyRef(
        "password_min_symbol",
        description="`PASSWORD` policies only. Minimum number of symbol characters.",
    )
    password_exclude_username: PropertyRef = PropertyRef(
        "password_exclude_username",
        description="`PASSWORD` policies only. Whether the password may not contain the username.",
    )
    password_exclude_attributes: PropertyRef = PropertyRef(
        "password_exclude_attributes",
        description="`PASSWORD` policies only. User profile attributes the password may not contain.",
    )
    password_common_password_check: PropertyRef = PropertyRef(
        "password_common_password_check",
        description=(
            "`PASSWORD` policies only. Whether passwords are checked against Okta's "
            "common password dictionary."
        ),
    )
    password_max_age_days: PropertyRef = PropertyRef(
        "password_max_age_days",
        description="`PASSWORD` policies only. Days until a password expires; 0 means never.",
    )
    password_expire_warn_days: PropertyRef = PropertyRef(
        "password_expire_warn_days",
        description="`PASSWORD` policies only. Days before expiry that users are warned.",
    )
    password_min_age_minutes: PropertyRef = PropertyRef(
        "password_min_age_minutes",
        description="`PASSWORD` policies only. Minimum minutes between password changes.",
    )
    password_history_count: PropertyRef = PropertyRef(
        "password_history_count",
        description="`PASSWORD` policies only. Number of previous passwords that cannot be reused.",
    )
    lockout_max_attempts: PropertyRef = PropertyRef(
        "lockout_max_attempts",
        description=(
            "`PASSWORD` policies only. Failed sign-in attempts before the account is "
            "locked; 0 disables lockout. Okta counts consecutive failures and has no "
            "configurable observation window."
        ),
    )
    lockout_auto_unlock_minutes: PropertyRef = PropertyRef(
        "lockout_auto_unlock_minutes",
        description=(
            "`PASSWORD` policies only. Minutes before a locked account unlocks "
            "automatically; 0 or null means an administrator must unlock it."
        ),
    )
    lockout_show_failures: PropertyRef = PropertyRef(
        "lockout_show_failures",
        description="`PASSWORD` policies only. Whether users are told their account is locked.",
    )
    lockout_notification_channels: PropertyRef = PropertyRef(
        "lockout_notification_channels",
        description="`PASSWORD` policies only. Channels that notify users of a lockout.",
    )
    enrollment_required_authenticators: PropertyRef = PropertyRef(
        "enrollment_required_authenticators",
        description="`MFA_ENROLL` policies only. Keys of the authenticators users must enroll.",
    )
    enrollment_optional_authenticators: PropertyRef = PropertyRef(
        "enrollment_optional_authenticators",
        description="`MFA_ENROLL` policies only. Keys of the authenticators users may enroll.",
    )
    enrollment_disabled_authenticators: PropertyRef = PropertyRef(
        "enrollment_disabled_authenticators",
        description="`MFA_ENROLL` policies only. Keys of the authenticators users cannot enroll.",
    )
    conditions: PropertyRef = PropertyRef(
        "conditions", description="Full policy conditions as JSON."
    )
    settings: PropertyRef = PropertyRef(
        "settings", description="Full policy settings as JSON."
    )


@dataclass(frozen=True)
class OktaPolicyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this relationship.",
    )


@dataclass(frozen=True)
class OktaPolicyToOrganizationRel(CartographyRelSchema):
    """An Okta organization contains a policy."""

    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaPolicyRelProperties = OktaPolicyRelProperties()


@dataclass(frozen=True)
class OktaPolicyAppliesToGroupRel(CartographyRelSchema):
    """An Okta policy applies to the members of a group."""

    target_node_label: str = "OktaGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_include_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: OktaPolicyRelProperties = OktaPolicyRelProperties()


@dataclass(frozen=True)
class OktaPolicyExcludesGroupRel(CartographyRelSchema):
    """An Okta policy excludes the members of a group."""

    target_node_label: str = "OktaGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_exclude_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXCLUDES"
    properties: OktaPolicyRelProperties = OktaPolicyRelProperties()


@dataclass(frozen=True)
class OktaPolicyAppliesToApplicationRel(CartographyRelSchema):
    """An Okta authentication policy governs sign-in to an application."""

    target_node_label: str = "OktaApplication"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("application_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: OktaPolicyRelProperties = OktaPolicyRelProperties()


@dataclass(frozen=True)
class OktaPolicySchema(CartographyNodeSchema):
    """
    An Okta policy: global session (`OKTA_SIGN_ON`), password, app
    authentication (`ACCESS_POLICY`), authenticator enrollment (`MFA_ENROLL`),
    or profile enrollment. Requires the `okta.policies.read` scope.
    """

    label: str = "OktaPolicy"
    properties: OktaPolicyNodeProperties = OktaPolicyNodeProperties()
    sub_resource_relationship: OktaPolicyToOrganizationRel = (
        OktaPolicyToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OktaPolicyAppliesToGroupRel(),
            OktaPolicyExcludesGroupRel(),
            OktaPolicyAppliesToApplicationRel(),
        ],
    )


@dataclass(frozen=True)
class OktaPolicyRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Unique Okta policy rule identifier."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    policy_id: PropertyRef = PropertyRef(
        "policy_id", description="ID of the policy that contains the rule."
    )
    name: PropertyRef = PropertyRef("name", description="Rule name.")
    type: PropertyRef = PropertyRef(
        "type",
        description=(
            "Rule type: `SIGN_ON`, `PASSWORD`, `ACCESS_POLICY`, `MFA_ENROLL`, or "
            "`PROFILE_ENROLLMENT`."
        ),
    )
    status: PropertyRef = PropertyRef(
        "status", description="Rule status, `ACTIVE` or `INACTIVE`."
    )
    priority: PropertyRef = PropertyRef(
        "priority",
        description="Evaluation order within the policy; the lowest value is evaluated first.",
    )
    system: PropertyRef = PropertyRef(
        "system",
        description="Whether Okta created the rule, such as a policy's default or catch-all rule.",
    )
    created: PropertyRef = PropertyRef(
        "created", description="Time when the rule was created."
    )
    okta_last_updated: PropertyRef = PropertyRef(
        "okta_last_updated", description="Time when Okta last updated the rule."
    )
    user_include_ids: PropertyRef = PropertyRef(
        "user_include_ids", description="IDs of the Okta users the rule applies to."
    )
    user_exclude_ids: PropertyRef = PropertyRef(
        "user_exclude_ids", description="IDs of the Okta users excluded from the rule."
    )
    group_include_ids: PropertyRef = PropertyRef(
        "group_include_ids", description="IDs of the Okta groups the rule applies to."
    )
    group_exclude_ids: PropertyRef = PropertyRef(
        "group_exclude_ids",
        description="IDs of the Okta groups excluded from the rule.",
    )
    network_connection: PropertyRef = PropertyRef(
        "network_connection",
        description=(
            "Network condition: `ANYWHERE`, or `ZONE` when the rule only matches "
            "requests from (or outside) specific network zones. Null when the rule "
            "has no network condition."
        ),
    )
    network_include_zone_ids: PropertyRef = PropertyRef(
        "network_include_zone_ids",
        description="IDs of the network zones the rule matches.",
    )
    network_exclude_zone_ids: PropertyRef = PropertyRef(
        "network_exclude_zone_ids",
        description="IDs of the network zones the rule does not match.",
    )
    risk_score_level: PropertyRef = PropertyRef(
        "risk_score_level",
        description="Risk score condition: `ANY`, `LOW`, `MEDIUM`, or `HIGH`.",
    )
    access: PropertyRef = PropertyRef(
        "access",
        description=(
            "`SIGN_ON`, `ACCESS_POLICY`, and `PROFILE_ENROLLMENT` rules. Whether "
            "matching requests are allowed (`ALLOW`) or denied (`DENY`)."
        ),
    )
    require_factor: PropertyRef = PropertyRef(
        "require_factor",
        description="`SIGN_ON` rules only. Whether a second factor is required.",
    )
    primary_factor: PropertyRef = PropertyRef(
        "primary_factor",
        description=(
            "`SIGN_ON` rules only. Factor that establishes the session, "
            "`PASSWORD_IDP` or `PASSWORD_IDP_ANY_FACTOR`."
        ),
    )
    factor_prompt_mode: PropertyRef = PropertyRef(
        "factor_prompt_mode",
        description="`SIGN_ON` rules only. When the second factor is prompted: `ALWAYS`, `DEVICE`, or `SESSION`.",
    )
    factor_lifetime_minutes: PropertyRef = PropertyRef(
        "factor_lifetime_minutes",
        description="`SIGN_ON` rules only. Minutes before the second factor is prompted again.",
    )
    remember_device_by_default: PropertyRef = PropertyRef(
        "remember_device_by_default",
        description="`SIGN_ON` rules only. Whether the device is remembered by default.",
    )
    session_max_idle_minutes: PropertyRef = PropertyRef(
        "session_max_idle_minutes",
        description="`SIGN_ON` rules only. Maximum Okta global session idle time, in minutes.",
    )
    session_max_lifetime_minutes: PropertyRef = PropertyRef(
        "session_max_lifetime_minutes",
        description=(
            "`SIGN_ON` rules only. Maximum Okta global session lifetime, in minutes; "
            "0 means no limit."
        ),
    )
    session_use_persistent_cookie: PropertyRef = PropertyRef(
        "session_use_persistent_cookie",
        description="`SIGN_ON` rules only. Whether global session cookies persist across browser sessions.",
    )
    factor_mode: PropertyRef = PropertyRef(
        "factor_mode",
        description=(
            "`ACCESS_POLICY` rules only. Number of factor types the user must "
            "authenticate with: `1FA` or `2FA`."
        ),
    )
    verification_method_type: PropertyRef = PropertyRef(
        "verification_method_type",
        description="`ACCESS_POLICY` rules only. Verification method type, such as `ASSURANCE` or `AUTH_METHOD_CHAIN`.",
    )
    reauthenticate_in: PropertyRef = PropertyRef(
        "reauthenticate_in",
        description="`ACCESS_POLICY` rules only. ISO 8601 duration after which users must re-authenticate.",
    )
    phishing_resistant_required: PropertyRef = PropertyRef(
        "phishing_resistant_required",
        description=(
            "`ACCESS_POLICY` rules only. True when every authenticator constraint "
            "requires a phishing-resistant possession factor. False when any "
            "constraint allows another factor or there are no constraints."
        ),
    )
    hardware_protection_required: PropertyRef = PropertyRef(
        "hardware_protection_required",
        description=(
            "`ACCESS_POLICY` rules only. True when every authenticator constraint "
            "requires a hardware-protected possession factor."
        ),
    )
    device_bound_required: PropertyRef = PropertyRef(
        "device_bound_required",
        description=(
            "`ACCESS_POLICY` rules only. True when every authenticator constraint "
            "requires a device-bound possession factor."
        ),
    )
    verification_constraints: PropertyRef = PropertyRef(
        "verification_constraints",
        description="`ACCESS_POLICY` rules only. Authenticator constraints as JSON.",
    )
    enroll_self: PropertyRef = PropertyRef(
        "enroll_self",
        description=(
            "`MFA_ENROLL` rules only. When users are asked to enroll authenticators: "
            "`CHALLENGE`, `LOGIN`, or `NEVER`."
        ),
    )
    password_change_access: PropertyRef = PropertyRef(
        "password_change_access",
        description="`PASSWORD` rules only. Whether users can change their password.",
    )
    self_service_password_reset_access: PropertyRef = PropertyRef(
        "self_service_password_reset_access",
        description="`PASSWORD` rules only. Whether users can reset a forgotten password.",
    )
    self_service_unlock_access: PropertyRef = PropertyRef(
        "self_service_unlock_access",
        description="`PASSWORD` rules only. Whether users can unlock their own account.",
    )
    conditions: PropertyRef = PropertyRef(
        "conditions", description="Full rule conditions as JSON."
    )
    actions: PropertyRef = PropertyRef(
        "actions", description="Full rule actions as JSON."
    )


@dataclass(frozen=True)
class OktaPolicyRuleToOrganizationRel(CartographyRelSchema):
    """An Okta organization contains a policy rule."""

    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaPolicyRelProperties = OktaPolicyRelProperties()


@dataclass(frozen=True)
class OktaPolicyHasRuleRel(CartographyRelSchema):
    """An Okta policy contains a rule."""

    target_node_label: str = "OktaPolicy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("policy_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_RULE"
    properties: OktaPolicyRelProperties = OktaPolicyRelProperties()


@dataclass(frozen=True)
class OktaPolicyRuleAppliesToGroupRel(CartographyRelSchema):
    """An Okta policy rule applies to the members of a group."""

    target_node_label: str = "OktaGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_include_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: OktaPolicyRelProperties = OktaPolicyRelProperties()


@dataclass(frozen=True)
class OktaPolicyRuleExcludesGroupRel(CartographyRelSchema):
    """An Okta policy rule excludes the members of a group."""

    target_node_label: str = "OktaGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_exclude_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXCLUDES"
    properties: OktaPolicyRelProperties = OktaPolicyRelProperties()


@dataclass(frozen=True)
class OktaPolicyRuleAppliesToUserRel(CartographyRelSchema):
    """An Okta policy rule applies to a user."""

    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_include_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: OktaPolicyRelProperties = OktaPolicyRelProperties()


@dataclass(frozen=True)
class OktaPolicyRuleExcludesUserRel(CartographyRelSchema):
    """An Okta policy rule excludes a user."""

    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_exclude_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXCLUDES"
    properties: OktaPolicyRelProperties = OktaPolicyRelProperties()


@dataclass(frozen=True)
class OktaPolicyRuleAppliesToNetworkZoneRel(CartographyRelSchema):
    """An Okta policy rule matches requests from a network zone."""

    target_node_label: str = "OktaNetworkZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("network_include_zone_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: OktaPolicyRelProperties = OktaPolicyRelProperties()


@dataclass(frozen=True)
class OktaPolicyRuleExcludesNetworkZoneRel(CartographyRelSchema):
    """An Okta policy rule does not match requests from a network zone."""

    target_node_label: str = "OktaNetworkZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("network_exclude_zone_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXCLUDES"
    properties: OktaPolicyRelProperties = OktaPolicyRelProperties()


@dataclass(frozen=True)
class OktaPolicyRuleSchema(CartographyNodeSchema):
    """
    A rule in an Okta policy. Rules are evaluated in priority order and carry
    the conditions and actions that enforce the policy, such as global session
    timeouts or the factors an app requires. Requires the `okta.policies.read`
    scope.
    """

    label: str = "OktaPolicyRule"
    properties: OktaPolicyRuleNodeProperties = OktaPolicyRuleNodeProperties()
    sub_resource_relationship: OktaPolicyRuleToOrganizationRel = (
        OktaPolicyRuleToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OktaPolicyHasRuleRel(),
            OktaPolicyRuleAppliesToGroupRel(),
            OktaPolicyRuleExcludesGroupRel(),
            OktaPolicyRuleAppliesToUserRel(),
            OktaPolicyRuleExcludesUserRel(),
            OktaPolicyRuleAppliesToNetworkZoneRel(),
            OktaPolicyRuleExcludesNetworkZoneRel(),
        ],
    )
