# GitLab Example Queries

## Projects and languages

List the programming languages detected across GitLab projects:

```cypher
MATCH (project:GitLabProject)
WHERE project.languages IS NOT NULL
WITH apoc.convert.fromJsonMap(project.languages) AS languages
UNWIND keys(languages) AS language
RETURN DISTINCT language
ORDER BY language
```

Find projects that report a specific language without requiring APOC:

```cypher
MATCH (project:GitLabProject)
WHERE project.languages CONTAINS '"Python"'
RETURN project.name, project.languages
```

The second query performs a string search. Parse `languages` with
`apoc.convert.fromJsonMap()` when exact percentages are needed.

## CI/CD security

Find runners that accept untagged jobs from unprotected refs:

```cypher
MATCH (runner:GitLabRunner)
WHERE runner.run_untagged = true
  AND runner.access_level = 'not_protected'
RETURN runner.id, runner.description, runner.runner_type
```

Find unmasked, unprotected CI/CD variables:

```cypher
MATCH (variable:GitLabCIVariable)
WHERE variable.protected = false
  AND variable.masked = false
RETURN variable.scope_type, variable.key, variable.environment_scope
```

Find environments that use unprotected variables:

```cypher
MATCH (environment:GitLabEnvironment)-[:HAS_CI_VARIABLE]->(variable:GitLabCIVariable)
WHERE variable.protected = false
RETURN environment.name, variable.key, variable.environment_scope
```

Find project includes that are not pinned to an immutable commit:

```cypher
MATCH (config:GitLabCIConfig)-[:USES_INCLUDE]->(include:GitLabCIInclude)
WHERE include.include_type = 'project'
  AND include.is_pinned = false
RETURN config.project_id, include.location, include.ref
```

Find manually triggerable pipelines that reference protected variables:

```cypher
MATCH (config:GitLabCIConfig)
WHERE 'manual' IN config.trigger_rules
  AND size(config.referenced_protected_variables) > 0
RETURN config.project_id,
       config.referenced_protected_variables,
       config.trigger_rules
```

## Container registry

List container images and their tags:

```cypher
MATCH (repository:GitLabContainerRepository)
      -[:REPO_IMAGE]->(tag:GitLabContainerRepositoryTag)
      -[:IMAGE]->(image:GitLabContainerImage)
RETURN repository.name,
       tag.name,
       image.digest,
       image.architecture,
       image.os
```

Find multi-architecture images and their platform-specific images:

```cypher
MATCH (manifest:GitLabContainerImage {type: 'manifest_list'})
      -[:CONTAINS_IMAGE]->(image:GitLabContainerImage)
RETURN manifest.digest, image.digest, image.architecture, image.os
```

Find images with signatures or provenance attestations:

```cypher
MATCH (attestation:GitLabContainerImageAttestation)
      -[:ATTESTS]->(image:GitLabContainerImage)
RETURN image.digest,
       attestation.attestation_type,
       attestation.predicate_type
```

Find layers shared by multiple GitLab images:

```cypher
MATCH (image:GitLabContainerImage)-[:HAS_LAYER]->(layer:GitLabContainerImageLayer)
WITH layer, count(DISTINCT image) AS image_count
WHERE image_count > 1
RETURN layer.diff_id, layer.size, image_count
ORDER BY image_count DESC
```

Find layers shared between GitLab Container Registry and Amazon ECR:

```cypher
MATCH (layer:ImageLayer)
MATCH (gitlab_image:GitLabContainerImage)-[:HAS_LAYER]->(layer)
MATCH (ecr_image:ECRImage)-[:HAS_LAYER]->(layer)
RETURN layer.diff_id,
       count(DISTINCT gitlab_image) AS gitlab_images,
       count(DISTINCT ecr_image) AS ecr_images
```

## Trivy integration

Find Trivy vulnerabilities that affect GitLab container images:

```cypher
MATCH (finding:TrivyImageFinding)-[:AFFECTS]->(image:GitLabContainerImage)
RETURN finding.name, finding.severity, image.uri, image.digest
ORDER BY finding.severity DESC
```

Find critical image vulnerabilities and available package fixes:

```cypher
MATCH (finding:TrivyImageFinding {severity: 'CRITICAL'})
      -[:AFFECTS]->(image:GitLabContainerImage)
MATCH (finding)-[:AFFECTS]->(package:Package)
OPTIONAL MATCH (package)-[:SHOULD_UPDATE_TO]->(fix:TrivyFix)
RETURN finding.name,
       image.uri,
       package.name,
       package.installed_version,
       fix.version AS fixed_version
```
