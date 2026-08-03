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
