from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AddToSet
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import ScopeById
from cartography.graph.analysis import SetProperties
from cartography.graph.analysis import SetProperty

AZURE_COMPUTE_ASSET_EXPOSURE_VM = AnalysisJob(
    name="Azure VM internet exposure",
    short_name="azure_compute_asset_exposure_vm",
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="MATCH (vm:AzureVirtualMachine)<-[:ATTACHED_TO]-(nic:AzureNetworkInterface)-[:ASSOCIATED_WITH]->(pip:AzurePublicIPAddress) WHERE pip.ip_address IS NOT NULL",
            effects=(
                SetProperty(
                    "vm", "exposed_internet", True, label="AzureVirtualMachine"
                ),
                AddToSet(
                    "vm", "exposed_internet_type", "direct", label="AzureVirtualMachine"
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (lb:AzureLoadBalancer{exposed_internet: true})-[:CONTAINS]->(:AzureLoadBalancerBackendPool)-[:ROUTES_TO]->(nic:AzureNetworkInterface)-[:ATTACHED_TO]->(vm:AzureVirtualMachine)",
            effects=(
                SetProperty(
                    "vm", "exposed_internet", True, label="AzureVirtualMachine"
                ),
                AddToSet(
                    "vm", "exposed_internet_type", "lb", label="AzureVirtualMachine"
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (vm:AzureVirtualMachine) WHERE vm.exposed_internet IS NULL",
            effects=(
                SetProperty(
                    "vm", "exposed_internet", False, label="AzureVirtualMachine"
                ),
            ),
        ),
    ),
)
AZURE_COMPUTE_ASSET_EXPOSURE_LB = AnalysisJob(
    name="Azure LoadBalancer internet exposure",
    short_name="azure_compute_asset_exposure_lb",
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="MATCH (lb:AzureLoadBalancer)-[:CONTAINS]->(fip:AzureLoadBalancerFrontendIPConfiguration)-[:ASSOCIATED_WITH]->(pip:AzurePublicIPAddress) WHERE pip.ip_address IS NOT NULL",
            effects=(
                SetProperty("lb", "exposed_internet", True, label="AzureLoadBalancer"),
            ),
        ),
        AnalysisStatement(
            match="MATCH (lb:AzureLoadBalancer) WHERE lb.exposed_internet IS NULL",
            effects=(
                SetProperty("lb", "exposed_internet", False, label="AzureLoadBalancer"),
            ),
        ),
    ),
)
AZURE_COMPUTE_ASSET_EXPOSURE_CONTAINER = AnalysisJob(
    name="Azure container instance internet exposure",
    short_name="azure_compute_asset_exposure_container",
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="MATCH (c:AzureGroupContainer) WHERE c.ip_address IS NOT NULL AND (c.ip_address_type = 'Public' OR (c.ip_address_type IS NULL AND NOT (c)-[:ATTACHED_TO]->(:AzureSubnet)))",
            effects=(
                SetProperties(
                    "c",
                    {"exposed_internet": True, "exposed_internet_type": ["direct"]},
                    label="AzureGroupContainer",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (c:AzureGroupContainer) WHERE c.exposed_internet IS NULL",
            effects=(
                SetProperty(
                    "c", "exposed_internet", False, label="AzureGroupContainer"
                ),
            ),
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
    scope=ScopeById(
        "AzureSubscription",
        "AZURE_SUBSCRIPTION_ID",
        scope_on="lb",
    ),
    statements=(
        AnalysisStatement(
            match="MATCH (lb:AzureLoadBalancer{exposed_internet: true})-[:CONTAINS]->(:AzureLoadBalancerBackendPool)-[:ROUTES_TO]->(nic:AzureNetworkInterface)-[:ATTACHED_TO]->(vm:AzureVirtualMachine) WHERE NOT (nic)-[:ASSOCIATED_WITH]->(:AzurePublicIPAddress)",
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "vm",
                    properties={"exposure_type": "via_lb_only"},
                    source_label="AzureLoadBalancer",
                    target_label="AzureVirtualMachine",
                ),
            ),
        ),
    ),
)
AZURE_FIREWALL_LB_PROTECTION = AnalysisJob(
    name="Azure Firewall PROTECTS LB relationships",
    short_name="azure_firewall_lb_protection",
    scope=ScopeById(
        "AzureSubscription",
        "AZURE_SUBSCRIPTION_ID",
        scope_on="fw",
    ),
    statements=(
        AnalysisStatement(
            match="MATCH (fw:AzureFirewall)-[:MEMBER_OF]->(vnet:AzureVirtualNetwork)-[:CONTAINS]->(subnet:AzureSubnet)<-[:ATTACHED_TO]-(nic:AzureNetworkInterface)<-[:ROUTES_TO]-(:AzureLoadBalancerBackendPool)<-[:CONTAINS]-(lb:AzureLoadBalancer)",
            effects=(
                AddRelationship(
                    "fw",
                    "PROTECTS",
                    "lb",
                    source_label="AzureFirewall",
                    target_label="AzureLoadBalancer",
                ),
            ),
        ),
    ),
)
