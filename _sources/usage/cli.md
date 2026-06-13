# Command Line Interface

Cartography uses [Typer](https://typer.tiangolo.com/) for its CLI, providing organized help output, shell autocompletion, and contextual help based on selected modules.

## Shell Autocompletion

Install completion for your shell:

```bash
# Detect your shell and install
cartography --install-completion

# Or show the completion script to customize
cartography --show-completion
```

After installation, restart your shell. You can then use Tab to autocomplete:

```bash
cartography --neo4j-<TAB>
# Shows: --neo4j-uri  --neo4j-user  --neo4j-password-env-var  ...
```

## Contextual Help

The `--help` output is organized into panels by category (Core, Neo4j, AWS, Azure, etc.).

When you specify `--selected-modules`, only relevant options are shown:

```bash
# Show all options
cartography --help

# Show only Core, Neo4j, AWS, StatsD, and Analysis options
cartography --selected-modules aws --help

# Show options for multiple modules
cartography --selected-modules aws,github --help
```

This makes it easier to discover relevant options without scrolling through 100+ parameters.

## Option Panels

Options are grouped into panels:

| Panel | Description |
|-------|-------------|
| Core Options | Logging, module selection, update tag |
| Neo4j Connection | Database URI, credentials, connection settings |
| AWS Options | AWS sync configuration |
| Azure Options | Azure subscription and authentication |
| GCP Options | Google Cloud Platform settings |
| GitHub Options | GitHub organization sync |
| StatsD Metrics | Metrics collection |
| Analysis Options | Post-sync analysis jobs |
| ... | 30+ more module-specific panels |

Core, Neo4j, StatsD, and Analysis panels are always shown regardless of selected modules.

## Common Options

### Core

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Enable debug logging |
| `-q, --quiet` | Only show warnings and errors |
| `--selected-modules` | Comma-separated list of modules to sync |
| `--update-tag` | Custom update tag (default: current timestamp) |

### Neo4j Connection

| Option | Description |
|--------|-------------|
| `--neo4j-uri` | Connection URI (default: `bolt://localhost:7687`) |
| `--neo4j-user` | Username |
| `--neo4j-password-env-var` | Env var containing password |
| `--neo4j-password-prompt` | Prompt for password interactively |
| `--neo4j-database` | Database name |

## Environment Variables

Sensitive credentials are passed via environment variables. Options ending in `-env-var` specify which variable to read:

```bash
export NEO4J_PASSWORD="secret"
export GITHUB_CONFIG="base64-config"

cartography \
    --neo4j-uri bolt://localhost:7687 \
    --neo4j-user neo4j \
    --neo4j-password-env-var NEO4J_PASSWORD \
    --github-config-env-var GITHUB_CONFIG
```

## Examples

### Sync specific AWS resources

```bash
cartography \
    --neo4j-uri bolt://localhost:7687 \
    --selected-modules aws \
    --aws-requested-syncs ec2:instance,s3,iam
```

### Sync multiple AWS profiles

```bash
AWS_CONFIG_FILE=/path/to/config cartography \
    --neo4j-uri bolt://localhost:7687 \
    --aws-sync-all-profiles
```

### Enable metrics

```bash
cartography \
    --neo4j-uri bolt://localhost:7687 \
    --statsd-enabled \
    --statsd-host metrics.example.com
```

## Programmatic Usage

The CLI can be used programmatically for testing:

```python
import cartography.cli
import cartography.sync

# Default sync
cli = cartography.cli.CLI(prog="cartography")
exit_code = cli.main(["--neo4j-uri", "bolt://localhost:7687"])

# Custom sync object
custom_sync = cartography.sync.build_default_sync()
cli = cartography.cli.CLI(sync=custom_sync)
exit_code = cli.main(["--neo4j-uri", "bolt://localhost:7687"])
```
