# Azure Modeling Notes

## Azure Container Instances

`AzureGroupContainer` represents an Azure Container Instances container group,
which is a co-scheduled group of one or more containers. It carries the
`ComputePod` ontology label because its semantics are closer to an ECS task or
Kubernetes pod than to an individual container.

Each container in the group is represented separately as an
`AzureContainerInstance` with the `Container` ontology label. Azure Container
Instances does not expose host architecture, so Cartography records `amd64`.
Image relationships are created only for digest-pinned references such as
`image@sha256:...`; tag-only references do not produce `HAS_IMAGE`.

## Load Balancer Exposure

Analysis jobs connect internet-facing Azure load balancers to private virtual
machines through `EXPOSE`. Azure Firewall protection is inferred through
virtual network topology. This is an approximation and does not validate the
effective route path or evaluate firewall rules.

## Application Gateway Routing

Application Gateway uses a parent gateway with frontend IP, backend pool, and
routing rule sub-resources. Listener and backend HTTP settings are folded onto
each `AzureApplicationGatewayRule`.

For basic rules, the routing rule connects its frontend IP to a backend pool.
Path-based rules expose `url_path_map_id`, but Cartography does not create a
single `ROUTES_TO` edge or populate folded backend properties because
individual path rules can target different backend pools.

Backend pools can route to Azure network interfaces, public IP addresses, and
nodes carrying the cross-provider `DNSRecord` ontology label.

## Azure Tags

Azure resources with the same subscription, key, and value share one
`AzureTag` node. Azure tags also carry the cross-provider `Tag` ontology label
for queries across Azure, AWS, GCP, Tenable, and other providers.
