# GSuite Configuration

:::{important}
The `gsuite` module is deprecated and retained only as a compatibility alias.
Use the [Google Workspace configuration guide](../googleworkspace/config.md) for
current authentication, permissions, and run instructions.
:::

Existing deployments should migrate the legacy `GSUITE_*` environment
variables and `--gsuite-*` options as described in the
[Google Workspace configuration guide](../googleworkspace/config.md).


## Legacy Options

These options configure the deprecated `gsuite` module. New deployments should
use the `--googleworkspace-*` options described in the
[Google Workspace configuration guide](../googleworkspace/config.md).

| Option | Description |
|--------|-------------|
| `--gsuite-auth-method` | GSuite authentication method: `delegated`, `oauth`, or `default`. Default: `delegated`. |
| `--gsuite-tokens-env-var` | Environment variable name containing GSuite credentials. Default: `GSUITE_GOOGLE_APPLICATION_CREDENTIALS`. |
