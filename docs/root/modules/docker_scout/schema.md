## Docker Scout Schema

### DockerScoutPublicImage
Representation of the current public base image identified by a Docker Scout recommendations report.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier for the public image (format: `name:tag`) |
| name | Name of the public image |
| tag | Tag of the public image |
| alternative_tags | Alternative tags reported for the current public image |
| version | Runtime version reported by Docker Scout when available |
| digest | Digest of the current public image |

#### Relationships

- An ontology `Image` is built on a `DockerScoutPublicImage`.

  Matching is done from the Docker Scout `Target` digest to `Image._ont_digest`.

    ```
    (Image)-[BUILT_ON]->(DockerScoutPublicImage)
    ```

### DockerScoutPublicImageTag
Representation of the current and recommended base image tags parsed from Docker Scout recommendations.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier for the public image tag (format: `name:tag`) |
| name | Name of the public image |
| tag | Tag of the public image |
| alternative_tags | Alternative tags suggested by Docker Scout for this public image tag |
| size | Size of the public image |
| flavor | Flavor of the public image |
| os | Operating system family inferred from the report |
| runtime | Runtime version reported by Docker Scout |
| is_slim | Whether the public image tag is a slim variant |

#### Relationships

- A DockerScoutPublicImage is built from a DockerScoutPublicImageTag.

    ```
    (DockerScoutPublicImage)-[BUILT_FROM]->(DockerScoutPublicImageTag)
    ```

- A DockerScoutPublicImage should update to a DockerScoutPublicImageTag.

  Relationship properties:
  `benefits` stores the recommendation bullet list.
  `fix_critical`, `fix_high`, `fix_medium`, and `fix_low` store the vulnerability delta by severity.

    ```
    (DockerScoutPublicImage)-[SHOULD_UPDATE_TO]->(DockerScoutPublicImageTag)
    ```
