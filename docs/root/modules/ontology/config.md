## Ontology Configuration

Ontology does not require any specific configuration parameters. However, to enable a more controlled creation of ontology nodes, you can specify sources of truth for certain ontology node types.

### Semantic Labels (Automatic)

For modules that use semantic labels (like `UserAccount`), ontology properties are added automatically during node creation. No additional configuration is required - the ontology mappings define which properties are added to nodes.

### Canonical Ontology Nodes (Optional)

For modules that create canonical `User` and `Device` nodes, you can control which modules serve as sources of truth:

1. Use the `--ontology-users-source` parameter to define a comma-separated list of modules that will serve as sources of truth for `User` nodes. Only users found in these modules will have corresponding `User` nodes created in the ontology. (basically you should specify your identity provider module here, e.g., `okta,duo`)
2. Use the `--ontology-devices-source` parameter to define a comma-separated list of modules that will serve as sources of truth for `Device` nodes. Only devices found in these modules will have corresponding `Device` nodes created in the ontology. (for example, you might specify `jamf,tailscale` here)
