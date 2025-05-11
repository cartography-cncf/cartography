## GSuite Schema

### GSuiteUser

Reference:
https://developers.google.com/admin-sdk/directory/v1/reference/users#resource

| Field | Description |
|-------|--------------|
| id | The unique ID for the user as a string. A user id can be used as a user request URI's userKey
| user_id | duplicate of id.
| agreed_to_terms |  This property is true if the user has completed an initial login and accepted the Terms of Service agreement.
| change_password_at_next_login | Indicates if the user is forced to change their password at next login. This setting doesn't apply when the user signs in via a third-party identity provider.
| creation_time | The time the user's account was created. The value is in ISO 8601 date and time format. The time is the complete date plus hours, minutes, and seconds in the form YYYY-MM-DDThh:mm:ssTZD. For example, 2010-04-05T17:30:04+01:00.
| customer_id | The customer ID to retrieve all account users.  You can use the alias my_customer to represent your account's customerId.  As a reseller administrator, you can use the resold customer account's customerId. To get a customerId, use the account's primary domain in the domain parameter of a users.list request.
| etag | ETag of the resource
| include_in_global_address_list | Indicates if the user's profile is visible in the G Suite global address list when the contact sharing feature is enabled for the domain. For more information about excluding user profiles, see the administration help center.
| ip_whitelisted | If true, the user's IP address is white listed.
| is_admin | Indicates a user with super admininistrator privileges. The isAdmin property can only be edited in the Make a user an administrator operation (makeAdmin method). If edited in the user insert or update methods, the edit is ignored by the API service.
| is_delegated_admin | Indicates if the user is a delegated administrator.  Delegated administrators are supported by the API but cannot create or undelete users, or make users administrators. These requests are ignored by the API service.  Roles and privileges for administrators are assigned using the Admin console.
| is_enforced_in_2_sv | Is 2-step verification enforced (Read-only)
| is_enrolled_in_2_sv | Is enrolled in 2-step verification (Read-only)
| is_mailbox_setup | Indicates if the user's Google mailbox is created. This property is only applicable if the user has been assigned a Gmail license.
| kind | The type of the API resource. For Users resources, the value is admin#directory#user.
| last_login_time | The last time the user logged into the user's account. The value is in ISO 8601 date and time format. The time is the complete date plus hours, minutes, and seconds in the form YYYY-MM-DDThh:mm:ssTZD. For example, 2010-04-05T17:30:04+01:00.
| name | First name + Last name
| family_name | The user's last name. Required when creating a user account.
| given_name | The user's first name. Required when creating a user account.
| org_unit_path | The full path of the parent organization associated with the user. If the parent organization is the top-level, it is represented as a forward slash (/).
| primary_email | The user's primary email address. This property is required in a request to create a user account. The primaryEmail must be unique and cannot be an alias of another user.
| suspended | Indicates if user is suspended
| thumbnail_photo_etag | ETag of the user's photo
| thumbnail_photo_url | Photo Url of the user
| lastupdated | Timestamp of when a sync job last updated this node
| firstseen | Timestamp of when a sync job first discovered this node

#### Node Labels

- `GSuiteUser`
- `GCPPrincipal`

#### Relationships
- GSuiteUser is an identity for a Human
    ```
    (Human)-[IDENTITY_GSUITE]->(GSuiteUser)
    ```

### GSuiteGroup

Reference:
https://developers.google.com/admin-sdk/directory/v1/reference/groups


| Field | Description |
|-------|--------------|
| id | The unique ID of a group. A group id can be used as a group request URI's groupKey.
| admin_created | Value is true if this group was created by an administrator rather than a user.
| description |  An extended description to help users determine the purpose of a group. For example, you can include information about who should join the group, the types of messages to send to the group, links to FAQs about the group, or related groups. Maximum length is 4,096 characters.
| direct_members_count | The number of users that are direct members of the group. If a group is a member (child) of this group (the parent), members of the child group are not counted in the directMembersCount property of the parent group
| email | The group's email address. If your account has multiple domains, select the appropriate domain for the email address. The email must be unique. This property is required when creating a group. Group email addresses are subject to the same character usage rules as usernames, see the administration help center for the details.
| etag | ETag of the resource
| kind | The type of the API resource. For Groups resources, the value is admin#directory#group.
| name | The group's display name.
| lastupdated | Timestamp of when a sync job last updated this node
| firstseen | Timestamp of when a sync job first discovered this node

#### Node Labels

- `GSuiteGroup`
- `GCPPrincipal`

#### Relationships

- GSuiteGroup can have members that are GSuiteUsers.

    ```
    (GSuiteUser)-[MEMBER_OF]->(GSuiteGroup)
    ```
