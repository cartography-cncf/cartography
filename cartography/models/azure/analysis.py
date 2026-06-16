from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisScope
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import PropertyEffect
from cartography.graph.analysis import RelationshipEffect

AZURE_SCOPE = AnalysisScope("AzureSubscription", "AZURE_SUBSCRIPTION_ID")

AZURE_COMPUTE_ASSET_EXPOSURE_VM = AnalysisJob(
    name="Azure VM internet exposure",
    short_name="azure_compute_asset_exposure_vm",
    effect=PropertyEffect(
        "AzureVirtualMachine",
        ("exposed_internet", "exposed_internet_type"),
    ),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            "MATCH (vm:AzureVirtualMachine)<-[:ATTACHED_TO]-(nic:AzureNetworkInterface)-[:ASSOCIATED_WITH]->(pip:AzurePublicIPAddress) WHERE pip.ip_address IS NOT NULL AND (vm.exposed_internet_type IS NULL OR NOT 'direct' IN vm.exposed_internet_type) SET vm.exposed_internet = true, vm.exposed_internet_type = CASE WHEN vm.exposed_internet_type IS NULL THEN ['direct'] WHEN NOT 'direct' IN vm.exposed_internet_type THEN vm.exposed_internet_type + ['direct'] ELSE vm.exposed_internet_type END",
        ),
        AnalysisStatement(
            "MATCH (lb:AzureLoadBalancer{exposed_internet: true})-[:CONTAINS]->(:AzureLoadBalancerBackendPool)-[:ROUTES_TO]->(nic:AzureNetworkInterface)-[:ATTACHED_TO]->(vm:AzureVirtualMachine) WITH vm WHERE vm.exposed_internet_type IS NULL OR NOT 'lb' IN vm.exposed_internet_type SET vm.exposed_internet = true, vm.exposed_internet_type = CASE WHEN vm.exposed_internet_type IS NULL THEN ['lb'] WHEN NOT 'lb' IN vm.exposed_internet_type THEN vm.exposed_internet_type + ['lb'] ELSE vm.exposed_internet_type END",
        ),
        AnalysisStatement(
            "MATCH (vm:AzureVirtualMachine) WHERE vm.exposed_internet IS NULL SET vm.exposed_internet = false",
        ),
    ),
)

AZURE_COMPUTE_ASSET_EXPOSURE_LB = AnalysisJob(
    name="Azure LoadBalancer internet exposure",
    short_name="azure_compute_asset_exposure_lb",
    effect=PropertyEffect(
        "AzureLoadBalancer",
        ("exposed_internet", "exposed_internet_type"),
    ),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            "MATCH (lb:AzureLoadBalancer)-[:CONTAINS]->(fip:AzureLoadBalancerFrontendIPConfiguration)-[:ASSOCIATED_WITH]->(pip:AzurePublicIPAddress) WHERE pip.ip_address IS NOT NULL SET lb.exposed_internet = true",
        ),
        AnalysisStatement(
            "MATCH (lb:AzureLoadBalancer) WHERE lb.exposed_internet IS NULL SET lb.exposed_internet = false",
        ),
    ),
)

AZURE_COMPUTE_ASSET_EXPOSURE_CONTAINER = AnalysisJob(
    name="Azure container instance internet exposure",
    short_name="azure_compute_asset_exposure_container",
    effect=PropertyEffect(
        "AzureGroupContainer",
        ("exposed_internet", "exposed_internet_type"),
    ),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            "MATCH (c:AzureGroupContainer) WHERE c.ip_address IS NOT NULL AND (c.ip_address_type = 'Public' OR (c.ip_address_type IS NULL AND NOT (c)-[:ATTACHED_TO]->(:AzureSubnet))) SET c.exposed_internet = true, c.exposed_internet_type = ['direct']",
        ),
        AnalysisStatement(
            "MATCH (c:AzureGroupContainer) WHERE c.exposed_internet IS NULL SET c.exposed_internet = false",
        ),
    ),
)

AZURE_COMPUTE_ASSET_EXPOSURE_JOBS = (
    AZURE_COMPUTE_ASSET_EXPOSURE_LB,
    AZURE_COMPUTE_ASSET_EXPOSURE_VM,
    AZURE_COMPUTE_ASSET_EXPOSURE_CONTAINER,
)

AZURE_LB_EXPOSURE = AnalysisJob(
    name="Azure LB EXPOSE relationships",
    short_name="azure_lb_exposure",
    scope=AZURE_SCOPE,
    effect=RelationshipEffect(
        "AzureLoadBalancer",
        "EXPOSE",
        "AzureVirtualMachine",
        properties=("exposure_type",),
    ),
    statements=(
        AnalysisStatement(
            "MATCH (s:AzureSubscription{id: $AZURE_SUBSCRIPTION_ID})-[:RESOURCE]->(lb:AzureLoadBalancer{exposed_internet: true})-[:CONTAINS]->(:AzureLoadBalancerBackendPool)-[:ROUTES_TO]->(nic:AzureNetworkInterface)-[:ATTACHED_TO]->(vm:AzureVirtualMachine) WHERE NOT (nic)-[:ASSOCIATED_WITH]->(:AzurePublicIPAddress) MERGE (lb)-[r:EXPOSE]->(vm) SET r.lastupdated = $UPDATE_TAG, r.exposure_type = 'via_lb_only'",
        ),
    ),
)

AZURE_FIREWALL_LB_PROTECTION = AnalysisJob(
    name="Azure Firewall PROTECTS LB relationships",
    short_name="azure_firewall_lb_protection",
    scope=AZURE_SCOPE,
    effect=RelationshipEffect("AzureFirewall", "PROTECTS", "AzureLoadBalancer"),
    statements=(
        AnalysisStatement(
            "MATCH (s:AzureSubscription{id: $AZURE_SUBSCRIPTION_ID})-[:RESOURCE]->(fw:AzureFirewall)-[:MEMBER_OF]->(vnet:AzureVirtualNetwork)-[:CONTAINS]->(subnet:AzureSubnet)<-[:ATTACHED_TO]-(nic:AzureNetworkInterface)<-[:ROUTES_TO]-(:AzureLoadBalancerBackendPool)<-[:CONTAINS]-(lb:AzureLoadBalancer) MERGE (fw)-[r:PROTECTS]->(lb) SET r.lastupdated = $UPDATE_TAG",
        ),
    ),
)
