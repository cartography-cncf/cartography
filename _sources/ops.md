# Cartography Production Operations

This document contains tips for running Cartography in production.

## Deployments

### Simple

The simplest production deployment involving Cartography looks something like this:

![basic-dataflow.png](images/basic-dataflow.png)

- Configure a Neo4j database. Specifics on this are out of scope of this document; refer to Neo4j's resources on how to
  do this.
- Configure a scheduled task (e.g. a cron job) to be able to access one or more data providers. See the
  [modules](module-list.md) section for specifics on each. We recommend that you run the cron job on a separate machine
  from the Neo4j database.

### Parallel jobs
If a single Cartography job takes longer than you would like, an orchestrator
can split ingestion into jobs that sync different resource families.

![parallel-crons.png](images/parallel-crons.png)

Cartography does not provide a distributed lock for concurrent syncs. Never run
the same resource type for the same account, project, or tenant concurrently.
Its cleanup can treat data written by the other job as stale and delete it.

The diagram shows AWS and GitHub in separate jobs because their node schemas and
cleanup scopes are independent. More granular parallelism is an advanced
deployment pattern, not a general guarantee. Before splitting one provider,
verify that the jobs do not manage the same nodes, relationships, sub-resource
cleanup scope, or analysis output.

Each process creates its own update tag. Keep each job's ingestion and cleanup
under that same tag, and do not pass one job's tag into another independently
scheduled run. Run cross-resource analysis only after all of its required
ingestion jobs complete.

## Maintaining a up-to-date picture of your infrastructure

Running `cartography` ensures that your Neo4j instance contains the most recent snapshot of your infrastructure. Here's
how that process works.

### Update tags

Each sync run has an `update_tag` associated with it,
which is the [Unix timestamp of when the sync started](https://github.com/cartography-cncf/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/sync.py#L131-L134).
See our [docs for more details](https://docs.cartography.dev/dev/writing-intel-modules.html#handling-cartographys-update_tag).

### Cleanup jobs

Each node and relationship created or updated during the sync will have their `lastupdated` field set to the
`update_tag`. At the end of a sync run, nodes and relationships with out-of-date `lastupdated` fields are considered
stale and will be deleted via a [cleanup job](https://docs.cartography.dev/dev/writing-intel-modules.html#cleanup).

### Sync frequency

To keep data updated, you can run `cartography` as part of a periodic script (cronjobs in Linux, scheduled tasks in
Windows). Determine your needs for data freshness and adjust accordingly.

## Performance

### Faster Neo4j driver

Neo4j publishes [neo4j-rust-ext](https://github.com/neo4j/neo4j-python-driver-rust-ext), a Rust implementation of the
Bolt protocol codec used by the Python driver. Because a Cartography sync spends a lot of its time serializing large
batches of nodes and relationships over Bolt, this is one of the cheapest wins available: measured sync speedups are in
the 20-30% range, and Neo4j reports up to 10x on workloads dominated by driver overhead.

Install it through the `neo4j-rust` extra:

```bash
uv tool install 'cartography[neo4j-rust]'
```

or, with pip:

```bash
pip install 'cartography[neo4j-rust]'
```

Nothing else changes: the extension registers itself where the Neo4j driver looks for it, so there is no flag to set
and no code path specific to it. Cartography logs which codec it picked up at the start of every sync:

```
Using the Rust Bolt codec from neo4j-rust-ext.
```

Pre-built wheels cover Linux, macOS and Windows on x86-64 and arm64. On a platform with no matching wheel, pip falls
back to building from source, which needs a Rust toolchain; installing plain `cartography` avoids that entirely.

If you hit a driver-level bug, reinstall without the extra before reporting it, so the pure-Python codec can confirm
the behavior.

The published Docker image already installs the extra, so containers get the Rust codec with no action on your part.

## Observability

### statsd

Cartography can be configured to send metrics to a [statsd](https://github.com/statsd/statsd) server. Specify the
`--statsd-enabled` flag when running `cartography` for sync execution times to be recorded and sent to
`127.0.0.1:8125` by default (these options are also configurable with the `--statsd-host` and `--statsd-port` options).
You can also provide your own `--statsd-prefix` to make these metrics easier to find in your own environment.

## Docker image

A production-ready docker image is available in [GitHub Container Registry](https://github.com/cartography-cncf/cartography/pkgs/container/cartography). We recommend that you avoid using the `:latest` tag and instead
use the tag or digest associated with your desired release version, e.g.

```bash
docker pull ghcr.io/cartography-cncf/cartography:0.96.1
```

This image can then be run with any of your desired command line flags:

```bash
docker run --rm ghcr.io/cartography-cncf/cartography:0.96.1 --help
```
