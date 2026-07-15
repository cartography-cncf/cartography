from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class AWSIpRuleLabel(ExtraNodeLabel):
    """A aws node participating in the shared AWSIpRule graph interface."""

    label: str = "AWSIpRule"


@dataclass(frozen=True)
class AWSIpv4CidrBlockLabel(ExtraNodeLabel):
    """A aws node participating in the shared AWSIpv4CidrBlock graph interface."""

    label: str = "AWSIpv4CidrBlock"


@dataclass(frozen=True)
class AWSIpv6CidrBlockLabel(ExtraNodeLabel):
    """A aws node participating in the shared AWSIpv6CidrBlock graph interface."""

    label: str = "AWSIpv6CidrBlock"


@dataclass(frozen=True)
class AWSPolicyLabel(ExtraNodeLabel):
    """A aws node participating in the shared AWSPolicy graph interface."""

    label: str = "AWSPolicy"


@dataclass(frozen=True)
class AWSPrincipalLabel(ExtraNodeLabel):
    """A aws node participating in the shared AWSPrincipal graph interface."""

    label: str = "AWSPrincipal"


@dataclass(frozen=True)
class EndpointLabel(ExtraNodeLabel):
    """A aws node participating in the shared Endpoint graph interface."""

    label: str = "Endpoint"


@dataclass(frozen=True)
class IpLabel(ExtraNodeLabel):
    """A aws node participating in the shared Ip graph interface."""

    label: str = "Ip"


@dataclass(frozen=True)
class KeyPairLabel(ExtraNodeLabel):
    """A aws node participating in the shared KeyPair graph interface."""

    label: str = "KeyPair"


@dataclass(frozen=True)
class MfaDeviceLabel(ExtraNodeLabel):
    """A aws node participating in the shared MfaDevice graph interface."""

    label: str = "MfaDevice"


@dataclass(frozen=True)
class SSMParameterLabel(ExtraNodeLabel):
    """A aws node participating in the shared SSMParameter graph interface."""

    label: str = "SSMParameter"


@dataclass(frozen=True)
class LoadBalancerV2Label(ExtraNodeLabel):
    """A aws node participating in the shared LoadBalancerV2 graph interface."""

    label: str = "LoadBalancerV2"
