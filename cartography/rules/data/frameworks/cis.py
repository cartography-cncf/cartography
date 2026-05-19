"""CIS benchmark framework helpers."""

from cartography.rules.spec.model import Framework

CIS_FRAMEWORK_SHORT_NAME = "CIS"

CIS_AWS_FRAMEWORK_NAME = "CIS AWS Foundations Benchmark"
CIS_AWS_SCOPE = "aws"
CIS_AWS_REVISION = "6.0.0"

CIS_GCP_FRAMEWORK_NAME = "CIS GCP Foundations Benchmark"
CIS_GCP_SCOPE = "gcp"
CIS_GCP_REVISION = "4.0"

CIS_KUBERNETES_FRAMEWORK_NAME = "CIS Kubernetes Benchmark"
CIS_KUBERNETES_SCOPE = "kubernetes"
CIS_KUBERNETES_REVISION = "1.12"

CIS_GOOGLE_WORKSPACE_FRAMEWORK_NAME = "CIS Google Workspace Foundations Benchmark"
CIS_GOOGLE_WORKSPACE_SCOPE = "googleworkspace"
CIS_GOOGLE_WORKSPACE_REVISION = "1.3"


def cis_aws(requirement: str) -> Framework:
    return Framework(
        name=CIS_AWS_FRAMEWORK_NAME,
        short_name=CIS_FRAMEWORK_SHORT_NAME,
        scope=CIS_AWS_SCOPE,
        revision=CIS_AWS_REVISION,
        requirement=requirement,
    )


def cis_gcp(requirement: str) -> Framework:
    return Framework(
        name=CIS_GCP_FRAMEWORK_NAME,
        short_name=CIS_FRAMEWORK_SHORT_NAME,
        requirement=requirement,
        scope=CIS_GCP_SCOPE,
        revision=CIS_GCP_REVISION,
    )


def cis_kubernetes(requirement: str) -> Framework:
    return Framework(
        name=CIS_KUBERNETES_FRAMEWORK_NAME,
        short_name=CIS_FRAMEWORK_SHORT_NAME,
        scope=CIS_KUBERNETES_SCOPE,
        revision=CIS_KUBERNETES_REVISION,
        requirement=requirement,
    )


def cis_google_workspace(requirement: str) -> Framework:
    return Framework(
        name=CIS_GOOGLE_WORKSPACE_FRAMEWORK_NAME,
        short_name=CIS_FRAMEWORK_SHORT_NAME,
        scope=CIS_GOOGLE_WORKSPACE_SCOPE,
        revision=CIS_GOOGLE_WORKSPACE_REVISION,
        requirement=requirement,
    )
