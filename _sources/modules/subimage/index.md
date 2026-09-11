# SubImage

```{toctree}
config
schema
```

The SubImage module ingests data from [SubImage](https://subimage.io), a managed
and enriched version of Cartography built by the same team.

## What is SubImage?

SubImage takes Cartography's infrastructure graph and adds a managed layer on top:
automated data collection, attack path analysis, vulnerability management,
compliance frameworks, and a natural language chatbot to query your graph.

It is fully managed, no infrastructure to maintain, no updates to handle.

## What does this module provide?

This module syncs SubImage metadata into your Cartography graph:

- **Tenant** information
- **Team members** configured in SubImage
- **API keys** provisioned in SubImage
- **Neo4j users** with access to the graph database
- **Enabled modules** (which integrations are active)
- **Compliance frameworks** being tracked

This allows you to measure the **coverage** of your current SubImage configuration
directly from your graph and identify gaps in your integration setup.

## References

- [SubImage website](https://subimage.io)
- [What's the difference between Cartography and SubImage?](https://subimage.io/#faq)
