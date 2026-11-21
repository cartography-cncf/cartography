# Google GSuite

:::{important} Deprecated Module
The `gsuite` module is a standalone legacy ingestion pipeline, not an alias for
`googleworkspace`. It no longer receives updates and is scheduled for removal
in Cartography v1.0.0.
:::

Selecting `gsuite` still runs its own authentication, user ingestion, group
ingestion, cleanup, legacy relationship migration, and Human identity analysis.
It ingests only Google Workspace users and groups.

New deployments should use the [Google Workspace](../googleworkspace/index.md)
module, which has a separate data model and broader resource coverage. Existing
deployments should follow the migration steps in the
[Google Workspace configuration guide](../googleworkspace/config.md).

```{toctree}
config
schema
```
