# AWS Analysis

## ECS tasks with no modeled internet path

`exposed_internet` is only ever written as `true`, so a container without it may
be private, or may sit behind a path the exposure rules do not model. The
`aws_ecs_no_modeled_internet_path` analysis job records the other case. It sets
`no_modeled_internet_path = true` and `no_modeled_internet_path_checked_at` (the
run's update tag) on an `AWSECSTask` and its `AWSECSContainer` nodes when all of
these hold:

- the task definition uses `awsvpc` networking. Bridge and host tasks share
  their instance's network and are never marked;
- every network interface of the task is in the graph, has no public IPv4
  address on any of its private IPs, no Elastic IP linked to it, and no IPv6
  address. The Elastic IP sync can link one in a run that does not sync the
  interfaces, which is when their public IPv4 addresses are refreshed;
- the task's account was checked for unmodeled internet paths in the run that
  synced the task, and none were found;
- every `AWSLoadBalancerV2` that reaches the task is `internal`, its account
  was checked at or after the load balancer was synced, with none found, and no
  load balancer targets one of that account's load balancer interfaces, as
  described below. That covers IP targets, a target group on the task's
  service, and a load balancer chained in front of either through an `alb`
  target group, such as an internet-facing NLB that forwards to an internal
  ALB;
- no container of the task is marked `exposed_internet`.

The property describes the graph, not the network: no internet path that
Cartography models reaches the task. The paths it does not see are listed
below.

The job runs at the end of every AWS sync, whatever modules were synced. It
checks every task in the graph, not only the tasks this run synced, because a
load balancer in one account can reach a task in another, accounts can be
synced by separate runs, and a run that syncs only some modules can change what
an earlier result relied on. Its properties are replaced at the end of the run
instead of being cleared first, so a run that fails part-way leaves the previous
values in place.

A result is current when `no_modeled_internet_path_checked_at` is at least the
node's `lastupdated`. The two are equal when the same run synced the task and
checked it. A later run that checks a task it did not sync writes its own,
newer tag. After a failed run, a task that the run synced keeps the older tag.
A failed run does not re-check the tasks it did not sync either, so their
results can predate what it changed, such as a load balancer in another account
or an entry point in their own account. The next successful run corrects them,
whichever accounts it syncs, because a run removes an account's check before it
syncs any of the check's inputs, as described below.

```cypher
MATCH (account:AWSAccount)-[:RESOURCE]->(task:AWSECSTask)
OPTIONAL MATCH (container:AWSECSContainer)-[:WORKLOAD_PARENT]->(task)
RETURN account.id, account.unmodeled_internet_paths,
       task.arn, container.name, container.exposed_internet,
       coalesce(task.no_modeled_internet_path, false)
         AND task.no_modeled_internet_path_checked_at >= task.lastupdated
         AS no_modeled_internet_path
ORDER BY account.id, task.arn
```

## Unmodeled internet paths

Some internet entry points terminate on private addresses, so the internal
load balancer or task behind them looks private from the graph. The
`aws_unmodeled_internet_paths` job checks one account at the end of its sync and
records on the `AWSAccount`:

- `unmodeled_internet_paths`: up to 10 IDs of the entry points it found. Unset
  when there are none.
- `unmodeled_internet_path_count`: how many it found, `0` when there are none.
- `unmodeled_internet_paths_checked_at`: the update tag of the run that checked
  the account.

It finds:

- CloudFront distributions with a VPC origin;
- API Gateway REST integrations over a VPC link;
- every API Gateway v2 (HTTP or WebSocket) API, because v2 VPC link
  integrations are not ingested.

The IDs are the distribution ARN, the integration ID
(`apiId/resourceId/httpMethod`) and the v2 API ID.

The check also vouches for the account's load balancers, their IP targets and
its network interfaces, which the ECS and Kubernetes analyses read. It runs only
when `cloudfront`, `apigateway`, `apigatewayv2`, `ec2:load_balancer_v2`,
`ec2:load_balancer_v2:expose`, `ec2:network_interface` and `ec2:subnet` were all
synced. IP targets resolve through the VPC of the target's subnet, which only
the subnet sync records. A run that syncs any of them removes the account's
previous result before the account's syncs start, and writes a new one after
them only when it synced all of them. A run that syncs some of them, or that
fails part-way, leaves the account unchecked, so an older check never vouches
for newer data.

An account counts as clear for a task only when its count is `0` and it was
checked in the run that synced the task, and for a load balancer only when its
check is at least as recent as the load balancer. An account that was never
checked, or whose check does not meet that bar, counts as unknown, and the tasks
that rely on it are not marked. The Kubernetes analysis reads the same
properties for the AWS load balancers in front of pods.

## Load balancers in front of load balancer interfaces

A load balancer can list another load balancer's private IPs as IP targets. This
is the static IP pattern for an ALB, where an NLB's IP target group lists the
private IPs of the ALB's interfaces. The graph does not link a load balancer's
interfaces to it, so the ALB and its targets would look private. The ECS and
Kubernetes analyses therefore treat every `internal` load balancer in an account
as one that may face the internet when a load balancer interface of that
account (an `AWSNetworkInterface` with `requester_id` `amazon-elb`) is reached,
as an IP target or through an `alb` target group chained in front of one, by a
load balancer that:

- is not `internal`, or
- belongs to another account, whatever its scheme. Judging an internal one
  there would take the same rule for its own account's interfaces, and so on.

An `internal` one in the same account does not count: whatever reaches it is one
of the account's entry points, one of its load balancer interfaces, or a load
balancer chained in front of it, which the rules above already cover.

The rule spans accounts, so it is evaluated each time the ECS and Kubernetes
jobs run, not in the account check, and nothing about it is recorded on the
account. A load balancer synced with another account counts as soon as its IP
target is linked, whichever account synced first.

## Paths the checks do not see

The checks read the graph, so they only see what the syncs loaded.

- Global Accelerator, App Runner VPC ingress, VPC Lattice and Verified Access
  are not ingested.
- PrivateLink endpoint services, which let other AWS accounts, and anything
  those accounts expose, reach an internal NLB.
- A CloudFront VPC origin or API Gateway VPC link that reaches a load balancer
  or task in another account, for example through a shared VPC. Only the entry
  point's own account is checked.
- Load balancers in accounts that are not synced into the same graph, and IP
  targets that do not resolve to exactly one private IP in the graph.
- A load balancer in another account whose target is newer than one of the two
  accounts' syncs. An IP target is linked only when the load balancer's account
  syncs after the target interface, a task's or another load balancer's, is in
  the graph, and a target group is linked to a service only when the task's
  account syncs after the target group is in the graph. When both accounts sync
  in the same run, one after the other, a task whose service is registered with
  the target group is caught by one of the two links. A task that is an IP
  target in some other way, such as a standalone task registered by hand, and a
  load balancer interface that is one, are missed when the load balancer's
  account syncs first, until that account syncs again.
- Resources a sync skipped. Cartography skips a region, without failing the
  run, when an API call is denied or times out, and the module's cleanup then
  removes what it had loaded from there. A missing CloudFront, API Gateway,
  ELBv2 or EC2 read permission, or a timeout, can hide an entry point or a load
  balancer and leave the account looking clear. After a transient ELBv2 failure,
  the previous load balancers are kept, and new ones are missing.
- Application-layer forwarding, such as a proxy task that relays internet
  traffic to another service.
