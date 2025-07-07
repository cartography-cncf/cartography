## Cloudflare Schema

```mermaid
graph LR
A(CloudflareAccount) -- RESOURCE --> Z(CloudflareZone)
A(CloudflareAccount) -- RESOURCE --> M(CloudflareMember)
A(CloudflareAccount) -- RESOURCE --> R(CloudflareRole)
M -- HAS_ROLE --> R
Z -- RESOURCE --> CloudflareDNSRecord
```

### CloudflareAccount

Represents the Cloudflare Account (aka Tenant)

| Field | Description |
|-------|-------------|
| id | Identifier |
| lastupdated |  Timestamp of the last time the node was updated |
| firstseen| Timestamp of when a sync job first created this node  |
| created_on | Timestamp for the creation of the account |
| name | Account name |
| abuse_contact_email | Abuse contact email to notify for abuse reports. |
| default_nameservers | Specifies the default nameservers to be used for new zones added to this account.<br/><br/>- `cloudflare.standard` for Cloudflare-branded nameservers<br/>- `custom.account` for account custom nameservers<br/>- `custom.tenant` for tenant custom nameservers<br/><br/>See [Custom Nameservers](https://developers.cloudflare.com/dns/additional-options/custom-nameservers/)<br/>for more information.<br/><br/>Deprecated in favor of [DNS Settings](https://developers.cloudflare.com/api/operations/dns-settings-for-an-account-update-dns-settings). |
| enforce_twofactor | Indicates whether membership in this account requires that<br/>Two-Factor Authentication is enabled |
| use_account_custom_ns_by_default | Indicates whether new zones should use the account-level custom<br/>nameservers by default.<br/><br/>Deprecated in favor of [DNS Settings](https://developers.cloudflare.com/api/operations/dns-settings-for-an-account-update-dns-settings). |


#### Relationships
- `CloudflareRole`, `CloudflareMember`, `CloudflareZone` belong to an `CloudflareAccount`.
    ```
    (:CloudflareAccount)-[:RESOURCE]->(
        :CloudflareRole,
        :CloudflareMember,
        :CloudflareZone
    )
    ```


### CloudflareRole

Represents a user role in Cloudflare

| Field | Description |
|-------|-------------|
| id | Role identifier tag. |
| lastupdated |  Timestamp of the last time the node was updated |
| description | Description of role's permissions. |
| name | Role name. |


#### CloudflareRelationships
- `CloudflareRole` belongs to a `CloudflareAccount`
    ```
    (:CloudflareRole)<-[:RESOURCE]-(:CloudflareAccount)
    ```
- `CloudflareMember` has a `CloudflareRole`
    ```
    (:CloudflareRole)<-[:HAS_ROLE]-(:CloudflareMember)
    ```

### CloudflareMember

Represents a membership in a Cloudflare account.

| Field | Description |
|-------|-------------|
| id | Membership identifier tag. |
| lastupdated |  Timestamp of the last time the node was updated |
| firstseen| Timestamp of when a sync job first created this node  |
| status | A member's status in the account. |
| email | Related user email |
| firstname | Related user first name |
| user_id | Related user id |
| lastname | Related user last name  |
| two_factor_authentication_enabled | Related user MFA status |

#### Relationships
- `CloudflareMember` belongs to a `CloudflareAccount`
    ```
    (:CloudflareMember)<-[:RESOURCE]-(:CloudflareAccount)
    ```
- `CloudflareMember` has a `CloudflareRole`
    ```
    (:CloudflareRole)<-[:HAS_ROLE]-(:CloudflareMember)
    ```

### CloudflareZone

Represents a DNS Zone in Cloudflare.

| Field | Description |
|-------|-------------|
| id | Identifier |
| lastupdated |  Timestamp of the last time the node was updated |
| firstseen| Timestamp of when a sync job first created this node  |
| activated_on | The last time proof of ownership was detected and the zone was made<br/>active |
| created_on | When the zone was created |
| development_mode | The interval (in seconds) from when development mode expires<br/>(positive integer) or last expired (negative integer) for the<br/>domain. If development mode has never been enabled, this value is 0. |
| cdn_only | The zone is only configured for CDN |
| custom_certificate_quota | Number of Custom Certificates the zone can have |
| dns_only | The zone is only configured for DNS |
| foundation_dns | The zone is setup with Foundation DNS |
| page_rule_quota | Number of Page Rules a zone can have |
| phishing_detected | The zone has been flagged for phishing |
| modified_on | When the zone was last modified |
| name | The domain name |
| original_dnshost | DNS host at the time of switching to Cloudflare |
| original_registrar | Registrar for the domain at the time of switching to Cloudflare |
| status | The zone status on Cloudflare. |
| verification_key | Verification key for partial zone setup. |
| paused | Indicates whether the zone is only using Cloudflare DNS services. A
true value means the zone will not receive security or performance
benefits. |
| type | A full zone implies that DNS is hosted with Cloudflare. A partial zone is
typically a partner-hosted zone or a CNAME setup. |

#### Relationships
- `CloudflareDNSRecord` belongs to an `CloudflareZone`.
    ```
    (:CloudflareZone)-[:RESOURCE]->(:CloudflareDNSRecord)
    ```


### CloudflareDNSRecord

Represents a DNS entry in Cloudflare.

| Field | Description |
|-------|-------------|
| id | Identifier. |
| lastupdated |  Timestamp of the last time the node was updated |
| name | The name of the DNSRecord |
| value | The IP address that the DNSRecord points to |
| type | The record type of the DNS record |
| comment | Comment for the DNS record |
| proxied | Whether the record is proxied by Cloudflare or not |
| ttl | DNS record TTL (1 indicate automatic TTL, refer to Cloudflare documentation) |
| created_on | When the record was created. |
| modified_on | When the record was last modified. |
| proxiable | Whether the record can be proxied by Cloudflare or not. |


#### Relationships
- `CloudflareDNSRecord` belongs to a `CloudflareZone`
    ```
    (:CloudflareDNSRecord)<-[:RESOURCE]-(:CloudflareZone)
    ```
