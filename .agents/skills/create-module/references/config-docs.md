# Module configuration documentation

Every intel module must document its setup in
`docs/root/modules/<module>/config.md`. Use the canonical structure below and
omit optional sections that do not apply. Never add empty sections.

```markdown
# <Module> configuration

<!-- Briefly state what must be configured before this module can run. -->

## Prerequisites

<!-- Optional. List provider-side resources or tools that must already exist. -->

## Authentication

<!-- Required for API-backed modules. Explain how to create and supply credentials. -->

### <Authentication method>

<!-- Optional. Use subsections only when the module supports multiple methods. -->

## Required permissions

<!-- Optional. Prefer a table for permissions. -->

## Optional permissions

<!-- Optional. State which feature each permission enables. -->

## Configure Cartography

<!-- Required. Document environment variables, CLI options, and accepted values. -->

## Run Cartography

<!-- Required. Include at least one directly runnable command. -->

## Input artifacts

<!-- Optional for report- or file-backed modules. -->

### Generate input artifacts

<!-- Optional. Explain how to create the artifacts Cartography consumes. -->

### Input format

<!-- Optional. Document only setup-relevant format requirements. -->

## Advanced configuration

<!-- Optional. Cover multi-account, multi-tenant, filtering, or alternate modes. -->

## Troubleshooting

<!-- Optional. Include only configuration-specific failures and remedies. -->

## References

<!-- Optional. Link to authoritative provider and Cartography documentation. -->
```

## Conventions

- Use exactly one H1 page title: `# <Provider> configuration`.
- Start sections at H2 and authentication methods at H3.
- Order setup as prerequisites, authentication, permissions, Cartography
  configuration, and a runnable command.
- Store secrets in environment variables. Clearly document any `*-env-var`
  indirection.
- Prefer tables when documenting permissions or three or more configuration
  options.
- Separate required permissions from optional permissions. Explain graceful
  degradation when optional permissions are absent.
- Keep provider-specific detail beneath the canonical headings.
- Use MyST notes only for important security, compatibility, or deprecation
  warnings.
- Keep deprecated module pages as short compatibility notices that link to the
  replacement.

## Content placement

A module's `index.md` contains only the page title and a toctree. Don't add
prose to it. The one exception is a deprecated module: its `index.md` keeps the
deprecation notice and the link to the replacement module above the toctree.
A current module's `index.md` looks like this:

````markdown
# <Module>

```{toctree}
config
schema
```
````

Put every other piece of content on the page where it belongs:

- Put node, relationship, and property documentation in schema docstrings and
  `PropertyRef.description`. This includes graph-model narratives, ingestion
  scope, and cleanup behavior. Sphinx renders these into generated `schema.md`,
  together with the ontology mappings from `extra_node_labels`.
- Put everything needed to make the module run, such as modules that must sync
  first, in `config.md`.
- Put Cypher investigations and query walkthroughs in `queries.md` or
  `examples.md`.
- Put post-ingestion logic, risk derivation, and materialized relationship
  behavior in `analysis.md`.
- Put any other topic, such as architecture or a cross-platform integration, on
  its own page, and list that page in the toctree.
- Delete content only when it is stale or duplicated after preserving any
  necessary migration or compatibility notice.
