## Keycloak Built-In Analysis

Cartography includes several automatic analyses for Keycloak that help identify inheritance relationships and derived permissions in a Keycloak realm. These analyses are defined in `cartography/data/jobs/analysis/keycloak_inheritance.json`.

### 1. Group Membership Inheritance

**Description**: Propagates user memberships to parent groups when a user is a member of a subgroup.

**Query**:
```cypher
MATCH (u:KeycloakUser)-[:MEMBER_OF|INHERITED_MEMBER_OF]->(g:KeycloakGroup)-[:SUBGROUP_OF]->(pg:KeycloakGroup)
MERGE (u)-[r:INHERITED_MEMBER_OF]->(pg)
ON CREATE SET r.firstseen = $UPDATE_TAG
SET r.lastupdated = $UPDATE_TAG
```

**Configuration**: Iterative (iteration size: 100)

**Graph result**:

```mermaid
graph LR
    U(KeycloakUser) -- MEMBER_OF --> SG(KeycloakGroup)
    SG -- SUBGROUP_OF --> PG(KeycloakGroup)
    U == INHERITED_MEMBER_OF ==> PG
```

### 2. Group-Based Role Assignment

**Description**: Automatically assigns roles to users based on their group membership (direct or inherited).

**Query**:
```cypher
MATCH (u:KeycloakUser)-[:MEMBER_OF|INHERITED_MEMBER_OF]->(g:KeycloakGroup)-[:GRANTS]->(r:KeycloakRole)
MERGE (u)-[r0:ASSUME_ROLE]->(r)
ON CREATE SET r0.firstseen = $UPDATE_TAG
SET r0.lastupdated = $UPDATE_TAG
```

**Configuration**: Non-iterative

**Graph result**:

```mermaid
graph LR
    U(KeycloakUser) -- MEMBER_OF --> G[KeycloakGroup]
    G -- GRANTS --> R(KeycloakRole)
    U == ASSUME_ROLE ==> R
```

### 3. Composite Role Grants Propagation

**Description**: Propagates scope permissions from included roles to composite roles.

**Query**:
```cypher
MATCH (r:KeycloakRole)-[:INCLUDES]->(c:KeycloakRole)-[:GRANTS|INDIRECT_GRANTS]->(s:KeycloakScope)
MERGE (r)-[r0:INDIRECT_GRANTS]->(s)
ON CREATE SET r0.firstseen = $UPDATE_TAG
SET r0.lastupdated = $UPDATE_TAG
```

**Configuration**: Iterative (iteration size: 100)

**Graph result**:

```mermaid
graph LR
    R(KeycloakRole) -- INCLUDES --> CR(KeycloakRole)
    CR -- GRANTS --> S(KeycloakScope)
    R == INDIRECT_GRANTS ==> S
```

### 4. Legitimate User Scope Assignment

**Description**: Identifies all scopes that a user can legitimately use based on the roles they assume.

**Query**:
```cypher
MATCH (u:KeycloakUser)-[:ASSUME_ROLE]->(:KeycloakRole)-[:GRANTS|INDIRECT_GRANTS]->(s:KeycloakScope)
MERGE (u)-[r:ASSUME_SCOPE]->(s)
ON CREATE SET r.firstseen = $UPDATE_TAG
SET r.lastupdated = $UPDATE_TAG
```

**Configuration**: Non-iterative

**Graph result**:

```mermaid
graph LR
    U(KeycloakUser) -- ASSUME_ROLE --> R(KeycloakRole)
    R -- GRANTS --> S(KeycloakScope)
    U == ASSUME_SCOPE ==> S
```

### 5. Orphan Scope Assignment

**Description**: Automatically assigns "orphan" scopes (not granted by any role) to all users in the realm.

```{info}
This analysis reflect the following Keycloak statement:
If there is no role scope mapping defined, each user is permitted to use this client scope. If there are role scope mappings defined, the user must be a member of at least one of the roles.
```

**Query**:
```cypher
MATCH (s:KeycloakScope)<-[:RESOURCE]-(r:KeycloakRealm)
MATCH (u:KeycloakUser)<-[:RESOURCE]-(r)
WHERE NOT (s)<-[:GRANTS|INDIRECT_GRANTS]-(:KeycloakRole)
MERGE (u)-[r0:ASSUME_SCOPE]->(s)
SET r0.firstseen = $UPDATE_TAG
SET r0.lastupdated = $UPDATE_TAG
```

**Configuration**: Non-iterative

**Graph result**:

```mermaid
graph LR
    R(KeycloakRealm) -- RESOURCE --> U(KeycloakUser)
    R -- RESOURCE --> S(KeycloakScope)
    R -- RESOURCE --> ROLE(KeycloakRole)
    subgraph "No relationship"
        S
        ROLE
    end
    U == ASSUME_SCOPE ==> S
```
