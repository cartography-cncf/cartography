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

### DockerScoutBaseImage
Representation of the current and recommended base image tags parsed from Docker Scout recommendations.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier for the base image (format: `name:tag`) |
| name | Name of the base image |
| tag | Tag of the base image |
| alternative_tags | Alternative tags suggested by Docker Scout for this base image |
| digest | Digest of the base image when Docker Scout reports it |
| size | Size of the base image |
| flavor | Flavor of the base image |
| os | Operating system family inferred from the report |
| runtime | Runtime version reported by Docker Scout |
| is_slim | Whether the base image is a slim variant |

#### Relationships

- A DockerScoutPublicImage is built from a DockerScoutBaseImage.

    ```
    (DockerScoutPublicImage)-[BUILT_FROM]->(DockerScoutBaseImage)
    ```

- A DockerScoutPublicImage should update to a DockerScoutBaseImage.

  Relationship properties:
  `benefits` stores the recommendation bullet list.
  `fix` stores the Docker Scout vulnerability delta as a JSON string.

    ```
    (DockerScoutPublicImage)-[SHOULD_UPDATE_TO]->(DockerScoutBaseImage)
    ```
