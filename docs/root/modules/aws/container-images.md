## AWS Container Images

Cartography models ECR image identity, tags, multi-platform manifests,
attestations, and layers separately. This makes digest identity stable while
preserving repository-specific names and tags.

### Repository and image identity

An `AWSECRRepository` is identified by its ARN. An
`AWSECRRepositoryImage` represents a repository reference and is identified by
its URI, which preserves the tag and repository context. It points to an
`AWSECRImage`, whose identity is the content digest.

```cypher
(:AWSECRRepository)-[:REPO_IMAGE]->(:AWSECRRepositoryImage)
(:AWSECRRepositoryImage)-[:IMAGE]->(:AWSECRImage)
```

This indirection allows multiple tags and repositories to reference the same
digest without creating duplicate image nodes.

List all repository references for a digest:

```cypher
MATCH (repository:AWSECRRepository)-[:REPO_IMAGE]->
      (reference:AWSECRRepositoryImage)-[:IMAGE]->
      (image:AWSECRImage {digest: $digest})
RETURN repository.arn, reference.uri, reference.tag,
       reference.image_pushed_at, image.type
ORDER BY repository.arn, reference.tag
```

### Manifest lists and attestations

`AWSECRImage.type` distinguishes:

- `image`: a single-platform image with architecture, OS, and ordered layers.
- `manifest_list`: a multi-platform OCI index or Docker manifest list.
- `attestation`: an attestation manifest, with `attests_digest` and optional
  provenance metadata.

Manifest lists contain platform images but exclude attestations from
`CONTAINS_IMAGE`:

```cypher
(:AWSECRImage {type: "manifest_list"})-[:CONTAINS_IMAGE]->
(:AWSECRImage {type: "image"})
```

Attestations use a separate edge:

```cypher
(:AWSECRImage {type: "attestation"})-[:ATTESTS]->(:AWSECRImage)
```

Inspect the platforms in a manifest list:

```cypher
MATCH (index:AWSECRImage {digest: $digest, type: "manifest_list"})
      -[:CONTAINS_IMAGE]->(image:AWSECRImage {type: "image"})
RETURN image.architecture, image.os, image.variant, image.digest
ORDER BY image.os, image.architecture, image.variant
```

Inspect attestations for an image:

```cypher
MATCH (attestation:AWSECRImage {type: "attestation"})
      -[:ATTESTS]->(image:AWSECRImage {digest: $digest})
RETURN attestation.digest, attestation.attestation_type,
       attestation.source_uri, attestation.source_revision,
       attestation.invocation_uri, attestation.invocation_workflow,
       attestation.invocation_run_number
```

SLSA provenance can also create `BUILT_FROM` relationships with
`parent_image_uri`, `from_attestation=true`, and `confidence="explicit"`.
Provenance may link an image to the `GitHubWorkflow` that packaged it.

### Ordered layers

Image layers are de-duplicated globally by their uncompressed DiffID. The
`layer_diff_ids` property retains manifest order, while `HEAD`, `NEXT`, `TAIL`,
and `HAS_LAYER` expose the same sequence as graph relationships.

Docker's canonical empty layer has DiffID
`sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef`
and is marked `is_empty=true`. This is the uncompressed DiffID, not the
compressed registry blob digest.

Read the stored manifest order:

```cypher
MATCH (image:AWSECRImage {digest: $digest, type: "image"})
UNWIND range(0, size(image.layer_diff_ids) - 1) AS position
RETURN position, image.layer_diff_ids[position] AS diff_id
ORDER BY position
```

Traverse the graph representation while constraining shared `NEXT` edges to
layers that belong to the image:

```cypher
MATCH (image:AWSECRImage {digest: $digest, type: "image"})-[:HEAD]->
      (head:AWSECRImageLayer)
MATCH (image)-[:TAIL]->(tail:AWSECRImageLayer)
MATCH path = (head)-[:NEXT*0..]->(tail)
WHERE ALL(layer IN nodes(path) WHERE (image)-[:HAS_LAYER]->(layer))
WITH path
ORDER BY length(path) DESC
LIMIT 1
UNWIND range(0, length(path)) AS position
RETURN position, nodes(path)[position].diff_id AS diff_id
ORDER BY position
```

Because layers are shared, repeated layers can produce multiple valid `NEXT`
successors. Detect image-local branching with:

```cypher
MATCH (image:AWSECRImage {type: "image"})-[:HAS_LAYER]->
      (layer:AWSECRImageLayer)-[:NEXT]->(successor:AWSECRImageLayer)
WHERE (image)-[:HAS_LAYER]->(successor)
WITH image, layer, collect(DISTINCT successor.diff_id) AS successors
WHERE size(successors) > 1
RETURN image.digest, layer.diff_id AS branching_layer, successors
ORDER BY image.digest, branching_layer
```

### Parent-image detection

An explicit `BUILT_FROM` relationship derived from provenance is the strongest
parent-image signal. When provenance is unavailable, a candidate base image
can be inferred when all of its ordered layers are a prefix of the target
image's layers:

```cypher
MATCH (target:AWSECRImage {digest: $target_digest, type: "image"})
MATCH (repository:AWSECRRepository {name: $base_repository})
      -[:REPO_IMAGE]->(reference:AWSECRRepositoryImage)
      -[:IMAGE]->(base:AWSECRImage {type: "image"})
WHERE target.layer_diff_ids IS NOT NULL
  AND base.layer_diff_ids IS NOT NULL
  AND size(base.layer_diff_ids) <= size(target.layer_diff_ids)
  AND ALL(position IN range(0, size(base.layer_diff_ids) - 1)
          WHERE base.layer_diff_ids[position] = target.layer_diff_ids[position])
RETURN base.digest, reference.uri, reference.tag,
       reference.image_pushed_at, size(base.layer_diff_ids) AS matched_layers
ORDER BY matched_layers DESC, reference.image_pushed_at DESC
LIMIT 1
```

Layer-prefix inference is a heuristic. Restrict the candidate repository and
prefer explicit provenance when available.

### Build provenance from CodeBuild

CodeBuild does not write provenance onto the images it builds: no attestations,
annotations or labels. Cartography links a CodeBuild-built ECR image to its
GitHub or GitLab repository with the first of these signals that applies.

1. **CodeBuild variables passed as image labels.** When the buildspec labels
   the image with the variables CodeBuild exposes to every build, the ECR layer
   sync reads them as provenance, the same way it reads CircleCI labels. The
   GitHub and GitLab supply-chain syncs then create `PACKAGED_FROM` with
   `match_method` `provenance`. The label key may be namespaced, for example
   `com.example.CODEBUILD_SOURCE_REPO_URL`.

   ```bash
   docker build \
     --label CODEBUILD_SOURCE_REPO_URL="$CODEBUILD_SOURCE_REPO_URL" \
     --label CODEBUILD_RESOLVED_SOURCE_VERSION="$CODEBUILD_RESOLVED_SOURCE_VERSION" \
     -t "$REPOSITORY_URI:$IMAGE_TAG" .
   ```

2. **A build ID tag.** A common buildspec convention tags images with the UUID
   part of `CODEBUILD_BUILD_ID` (`<project>:<uuid>`), for example
   `build-<uuid>`. The CodeBuild sync pairs that UUID with the ECR repository's
   name, confirms the build with `BatchGetBuilds`, and creates a `PACKAGED_BY`
   edge carrying the build ID, the resolved commit and the repository URL.

3. **A same-named CodeBuild project.** Without a confirmed build, an image in an
   ECR repository named after a CodeBuild project in the same account and
   region is linked to that project's source repository. This rung needs no
   build history and gives no commit.

| match_method | Signal | Confidence |
|--------------|--------|------------|
| `codebuild_build_id_tag` | A tag carries the UUID of a build of the same-named project, confirmed by `BatchGetBuilds`. | high (`0.9`) |
| `codebuild_project_name` | The ECR repository and a GitHub- or GitLab-sourced CodeBuild project share a name, account and region. | low (`0.4`) |

```cypher
(:AWSECRImage)-[:PACKAGED_BY]->(:AWSCodeBuildProject)
(:Image)-[:PACKAGED_FROM]->(:GitHubRepository)
(:Image)-[:PACKAGED_FROM]->(:GitLabProject)
```

The ontology stage derives the second and third rungs' `PACKAGED_FROM` edges,
for the tagged image and, when it is a manifest list, its platform images. An
image that already has a `PACKAGED_FROM` edge from provenance, Dockerfile
analysis or another matcher keeps it. Builds are read on every sync and never
stored as nodes. When some region's builds cannot be read, `PACKAGED_BY` edges
from earlier syncs are kept. See the optional CodeBuild permission in the AWS
configuration guide.

### Lambda container images

For Lambda functions with `packagetype="Image"`, `image_uri` stores the
container reference and `image_digest` stores the digest when the URI is
digest-pinned. `HAS_IMAGE` links the function to the matching registry object.

`RESOLVED_IMAGE` has narrower runtime semantics: it points to the concrete
single-platform `Image` that the function runs. For a multi-architecture
manifest list, Cartography uses `architecture_normalized` (`amd64` or `arm64`)
to select the matching child image.

```cypher
(:AWSLambda)-[:HAS_IMAGE]->(:AWSECRImage)
(:AWSLambda)-[:HAS_IMAGE]->(:GitLabContainerImage)
(:AWSLambda)-[:HAS_IMAGE]->(:GCPArtifactRegistryImage)
(:AWSLambda)-[:HAS_IMAGE]->(:GitHubContainerImage)
(:AWSLambda)-[:RESOLVED_IMAGE]->(:Image)
```

Use `HAS_IMAGE` when investigating the configured artifact or tag. Use
`RESOLVED_IMAGE` when investigating runtime packages, layers,
vulnerabilities, attestations, or provenance for the platform that executes.

```cypher
MATCH (function:AWSLambda)-[:RESOLVED_IMAGE]->(image:Image)
RETURN function.arn, function.architecture_normalized,
       image.digest, image.architecture, image.os
ORDER BY function.arn
```
