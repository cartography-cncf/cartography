# Module configuration documentation

Every intel module must document its setup in
`docs/root/modules/<module>/config.md`. Use the canonical structure below and
omit optional sections that do not apply. Never add empty sections.

```markdown
# <Module> Configuration

<!-- Briefly state what must be configured before this module can run. -->

## Prerequisites

<!-- Optional. List provider-side resources or tools that must already exist. -->

## Authentication

<!-- Required for API-backed modules. Explain how to create and supply credentials. -->

### <Authentication method>

<!-- Optional. Use subsections only when the module supports multiple methods. -->

## Required Permissions

<!-- Optional. Prefer a table for permissions. -->

## Optional Permissions

<!-- Optional. State which feature each permission enables. -->

## Configure Cartography

<!-- Required. Document environment variables, CLI options, and accepted values. -->

## Run Cartography

<!-- Required. Include at least one directly runnable command. -->

## Input Artifacts

<!-- Optional for report- or file-backed modules. -->

### Generate Input Artifacts

<!-- Optional. Explain how to create the artifacts Cartography consumes. -->

### Input Format

<!-- Optional. Document only setup-relevant format requirements. -->

## Advanced Configuration

<!-- Optional. Cover multi-account, multi-tenant, filtering, or alternate modes. -->

## Troubleshooting

<!-- Optional. Include only configuration-specific failures and remedies. -->

## References

<!-- Optional. Link to authoritative provider and Cartography documentation. -->
```

## Conventions

- Use exactly one H1 page title: `# <Provider> Configuration`.
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

Keep `config.md` focused on making the module run:

- Put module purpose, feature inventories, architecture, graph-model
  narratives, broad ingestion behavior, and ontology integration in
  `index.md`.
- Put Cypher investigations and query walkthroughs in `queries.md` or
  `examples.md`.
- Put post-ingestion logic, risk derivation, and materialized relationship
  behavior in `analysis.md`.
- Put node, relationship, and property documentation in schema docstrings and
  `PropertyRef.description`; Sphinx renders these into generated `schema.md`.
- Delete content only when it is stale or duplicated after preserving any
  necessary migration or compatibility notice.
