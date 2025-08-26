## SnipeIT Schema

```mermaid
graph LR
T(SnipeitTenant) -- RESOURCE --> U(SnipeitUser)
T -- RESOURCE --> A(SnipeitAsset)
U -- HAS_CHECKED_OUT --> A
```



### SnipeitTenant

Representation of a SnipeIT Tenant.

|Field | Description|
|-------|-------------|
|id | SnipeIT Tenant ID e.g. "company name"|

#### Relationships

- All SnipeIT users and asset are linked to a SnipeIT Tenant

    ```cypher
    (:SnipeitUser)<-[:RESOURCE]-(:SnipeitTenant)
    ```

    ```cypher
    (:SnipeitAsset)<-[:RESOURCE]-(:SnipeitTenant)
    ```

### SnipeitUser

Representation of a SnipeIT User.

|Field | Description|
|-------|-------------|
|id | same as device_id|
|company | Company the SnipeIT user is linked to|
|username | Username of the user |
|email | Email of the user |

#### Relationships

- All SnipeIT users are linked to a SnipeIT Tenant

    ```cypher
    (:SnipeitUser)<-[:RESOURCE]-(:SnipeitTenant)
    ```

- A SnipeIT user can check-out one or more assets

    ```cypher
    (:SnipeitAsset)<-[:HAS_CHECKED_OUT]-(:SnipeitUser)
    ```


### SnipeitAsset

Representation of a SnipeIT asset.

|Field | Description|
|-------|-------------|
|id | Asset id|
|asset_tag | Asset tag|
|assigned_to | Email of the SnipeIT user the asset is checked out to|
|category | Category of the asset |
|company | The company the asset belongs to |
|manufacturer | Manufacturer of the asset |
|model | Model of the device|
|serial | Serial number of the asset|
|status | Status label of the asset |

#### Relationships

- All SnipeIT users and asset are linked to a SnipeIT Tenant

    ```cypher
    (:SnipeitUser)<-[:RESOURCE]-(:SnipeitTenant)
    ```

    ```cypher
    (:SnipeitAsset)<-[:RESOURCE]-(:SnipeitTenant)
    ```

- A SnipeIT user can check-out one or more assets

    ```cypher
    (:SnipeitAsset)<-[:HAS_CHECKED_OUT]-(:SnipeitUser)
    ```
