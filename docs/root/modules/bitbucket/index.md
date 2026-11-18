# Bitbucket Cloud

The Bitbucket Cloud module ingests workspaces, the projects and repositories within them, and current workspace members. It does not yet map which users can access which repositories.

Repositories always belong to a workspace and a project (except legacy repositories created before projects concept existed).

Not yet covered by this module: per-repository permission levels, pull requests, and branch restriction rules. These may be added in a future version.

See [configuration](config.md) for access requirements and setup, and the generated [schema](schema.md) for fields and relationships.

```{toctree}
config
schema
```
