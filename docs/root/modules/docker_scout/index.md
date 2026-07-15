# Docker Scout

[Docker Scout](https://docs.docker.com/scout/) analyzes container images for
security issues in base image packages. Cartography ingests pre-generated
Docker Scout recommendation reports for images originating from AWS ECR, GCP
Artifact Registry, and GitLab Container Registry.

For each report, Cartography creates:

- One `DockerScoutPublicImage` node for the current public base image.
- One or more `DockerScoutPublicImageTag` nodes for current and recommended
  tags.
- A `BUILT_FROM` relationship to the current base image entry.
- `SHOULD_UPDATE_TO` relationships to recommended base image tags.
- A `BUILT_ON` relationship from the ontology `Image` node to the
  `DockerScoutPublicImage` node.

```{toctree}
config
schema
```
