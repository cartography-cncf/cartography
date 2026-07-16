from cartography.models.core.nodes import ExtraNodeLabel

DEPENDENCY = ExtraNodeLabel(
    label="Dependency",
    description="A node participating in the shared Dependency graph interface.",
)


FIX = ExtraNodeLabel(
    label="Fix",
    description="A node participating in the shared Fix graph interface.",
)


GCP_PRINCIPAL = ExtraNodeLabel(
    label="GCPPrincipal",
    description="A node participating in the shared GCPPrincipal graph interface.",
)


IP_PERMISSION_EGRESS = ExtraNodeLabel(
    label="IpPermissionEgress",
    description="A node participating in the shared IpPermissionEgress graph interface.",
)


IP_PERMISSION_INBOUND = ExtraNodeLabel(
    label="IpPermissionInbound",
    description="A node participating in the shared IpPermissionInbound graph interface.",
)


IP_RANGE = ExtraNodeLabel(
    label="IpRange",
    description="A node participating in the shared IpRange graph interface.",
)


IP_RULE = ExtraNodeLabel(
    label="IpRule",
    description="A node participating in the shared IpRule graph interface.",
)


RISK = ExtraNodeLabel(
    label="Risk",
    description="A node participating in the shared Risk graph interface.",
)
