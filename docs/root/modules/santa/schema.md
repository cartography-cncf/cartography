## Santa Schema

### SantaMachine

Represents a machine observed by Zentral inventory snapshots for a Santa source.

> **Ontology Mapping**: This node maps into the ontology `Device` model via hostname.

| Field | Description |
|-------|-------------|
| **id** | Stable machine identifier (usually serial number) |
| **hostname** | Machine hostname |
| **serial_number** | Hardware serial number |
| platform | Platform from inventory snapshot |
| model | Hardware model |
| os_version | Formatted OS version |
| source_name | Zentral inventory source used for export |
| last_seen | Last seen timestamp from inventory export |

#### Relationships

- Machine primary user attribution:

  ```
  (SantaMachine)-[:PRIMARY_USER]->(SantaUser)
  ```

- Observed executions on machine:

  ```
  (SantaMachine)-[:OBSERVED_EXECUTION]->(SantaObservedApplicationVersion)
  ```

### SantaUser

Represents the principal user observed from Zentral machine snapshots.

> **Ontology Mapping**: This node has the extra label `UserAccount` to enable ontology `User` joins.

| Field | Description |
|-------|-------------|
| **id** | Stable principal identifier (unique_id or principal_name) |
| **email** | Principal email when available |
| principal_name | Principal account name |
| display_name | Principal display name |
| source_name | Zentral inventory source used for export |

#### Relationships

- User observed as machine primary user:

  ```
  (SantaMachine)-[:PRIMARY_USER]->(SantaUser)
  ```

- User executed observed app versions:

  ```
  (SantaUser)-[:EXECUTED]->(SantaObservedApplicationVersion)
  ```

### SantaObservedApplication

Represents a normalized application identifier observed in Santa events.

| Field | Description |
|-------|-------------|
| **id** | Normalized application identifier |
| name | Display name of the application |
| identifier | Original identifier value from Santa event payload |
| source_name | Zentral source used for export |

#### Relationships

- Application to version:

  ```
  (SantaObservedApplication)-[:VERSION]->(SantaObservedApplicationVersion)
  ```

### SantaObservedApplicationVersion

Represents a version of an observed application from Santa execution events.

| Field | Description |
|-------|-------------|
| **id** | Normalized application-version identifier |
| version | Version string from Santa event payload |
| source_name | Zentral source used for export |
| last_seen | Event timestamp used to represent last observation |

#### Relationships

- Version belongs to an application:

  ```
  (SantaObservedApplication)-[:VERSION]->(SantaObservedApplicationVersion)
  ```

- Version observed on machine execution:

  ```
  (SantaMachine)-[:OBSERVED_EXECUTION]->(SantaObservedApplicationVersion)
  ```

- Version executed by user:

  ```
  (SantaUser)-[:EXECUTED]->(SantaObservedApplicationVersion)
  ```

## Observed Execution Semantics

`OBSERVED_EXECUTION` captures that at least one Santa event associated a machine with an application version. It is not a process timeline and does not preserve every individual execution event.
