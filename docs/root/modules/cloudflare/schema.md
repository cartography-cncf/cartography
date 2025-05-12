## Cloudflare Schema



### Account

# CHANGEME: Add a short description of the node and complete fields description

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| created_on | Timestamp for the creation of the account |
| name | Account name |
| settings_abuse_contact_email | Sets an abuse contact email to notify for abuse reports. |
| settings_default_nameservers | Specifies the default nameservers to be used for new zones added to this account.<br/><br/>- `cloudflare.standard` for Cloudflare-branded nameservers<br/>- `custom.account` for account custom nameservers<br/>- `custom.tenant` for tenant custom nameservers<br/><br/>See [Custom Nameservers](https://developers.cloudflare.com/dns/additional-options/custom-nameservers/)<br/>for more information.<br/><br/>Deprecated in favor of [DNS Settings](https://developers.cloudflare.com/api/operations/dns-settings-for-an-account-update-dns-settings). |
| settings_enforce_twofactor | Indicates whether membership in this account requires that<br/>Two-Factor Authentication is enabled |
| settings_use_account_custom_ns_by_default | Indicates whether new zones should use the account-level custom<br/>nameservers by default.<br/><br/>Deprecated in favor of [DNS Settings](https://developers.cloudflare.com/api/operations/dns-settings-for-an-account-update-dns-settings). |
| id | Identifier |

#### Relationships
- Some node types belong to an `CloudflareAccount`.
    ```
    (:CloudflareAccount)<-[:RESOURCE]-(
        :CloudflareRole,
        :CloudflareMember,
    )


### Role

# CHANGEME: Add a short description of the node and complete fields description

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| description | Description of role's permissions. |
| name | Role name. |
| permissions |  |
| id | Role identifier tag. |

#### Relationships
- `CloudflareRole` belongs to a `CloudflareAccount`
    ```
    (:CloudflareRole)-[:RESOURCE]->(:CloudflareAccount)
    ```


### Member

# CHANGEME: Add a short description of the node and complete fields description

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| status | A member's status in the account. |
| user_email |  |
| user_first_name |  |
| user_id |  |
| user_last_name |  |
| user_two_factor_authentication_enabled |  |
| id | Membership identifier tag. |
| policies_id | ID of the iam_list_member_policy entity |

#### Relationships
- `CloudflareMember` belongs to a `CloudflareAccount`
    ```
    (:CloudflareMember)-[:RESOURCE]->(:CloudflareAccount)
    ```


### Zone

# CHANGEME: Add a short description of the node and complete fields description

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| account_id |  |
| account_name | The name of the account |
| activated_on | The last time proof of ownership was detected and the zone was made<br/>active |
| created_on | When the zone was created |
| development_mode | The interval (in seconds) from when development mode expires<br/>(positive integer) or last expired (negative integer) for the<br/>domain. If development mode has never been enabled, this value is 0. |
| meta_cdn_only | The zone is only configured for CDN |
| meta_custom_certificate_quota | Number of Custom Certificates the zone can have |
| meta_dns_only | The zone is only configured for DNS |
| meta_foundation_dns | The zone is setup with Foundation DNS |
| meta_page_rule_quota | Number of Page Rules a zone can have |
| meta_phishing_detected | The zone has been flagged for phishing |
| meta_step |  |
| modified_on | When the zone was last modified |
| name | The domain name |
| original_dnshost | DNS host at the time of switching to Cloudflare |
| original_registrar | Registrar for the domain at the time of switching to Cloudflare |
| owner_id |  |
| owner_name | Name of the owner |
| owner_type | The type of owner |
| status | The zone status on Cloudflare. |
| verification_key | Verification key for partial zone setup. |
| id | Identifier |
| paused | Indicates whether the zone is only using Cloudflare DNS services. A
true value means the zone will not receive security or performance
benefits.
 |
| type | A full zone implies that DNS is hosted with Cloudflare. A partial zone is
typically a partner-hosted zone or a CNAME setup.
 |

#### Relationships
- Some node types belong to an `CloudflareZone`.
    ```
    (:CloudflareZone)<-[:RESOURCE]-(
        :CloudflareDNSRecord,
    )


### DNSRecord

# CHANGEME: Add a short description of the node and complete fields description

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| comment_modified_on | When the record comment was last modified. Omitted if there is no comment. |
| created_on | When the record was created. |
| modified_on | When the record was last modified. |
| proxiable | Whether the record can be proxied by Cloudflare or not. |
| tags_modified_on | When the record tags were last modified. Omitted if there are no tags. |
| id | Identifier. |

#### Relationships
- `CloudflareDNSRecord` belongs to a `CloudflareZone`
    ```
    (:CloudflareDNSRecord)-[:RESOURCE]->(:CloudflareZone)
    ```
