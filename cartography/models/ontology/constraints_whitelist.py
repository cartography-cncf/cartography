from cartography.models.anthropic.apikey import AnthropicApiKeyToUserRel
from cartography.models.aws.cloudtrail.management_events import (
    AssumedRoleWithSAMLMatchLink,
)

# Raw ingest-time (:Container|:Function)-[:HAS_IMAGE]->(:Image) references,
# whitelisted below as distinct from the analysis-derived RESOLVED_IMAGE edge.
from cartography.models.aws.ecs.containers import ECSContainerToECRImageRel
from cartography.models.aws.ecs.containers import (
    ECSContainerToGCPArtifactRegistryImageRel,
)
from cartography.models.aws.ecs.containers import ECSContainerToGitHubContainerImageRel
from cartography.models.aws.ecs.containers import ECSContainerToGitLabContainerImageRel
from cartography.models.aws.ecs.containers import ECSContainerToTaskRel
from cartography.models.aws.ecs.services import ECSServiceToECSClusterRel
from cartography.models.aws.ecs.services import ECSServiceToECSTaskRel
from cartography.models.aws.ecs.tasks import ECSTaskToECSClusterRel
from cartography.models.aws.iam.access_key import AccountAccessKeyToAWSUserRel
from cartography.models.aws.iam.group_membership import AWSGroupToAWSUserRel
from cartography.models.aws.identitycenter.awspermissionset import (
    AWSRoleToSSOGroupMatchLink,
)
from cartography.models.aws.identitycenter.awspermissionset import (
    AWSRoleToSSOUserMatchLink,
)
from cartography.models.aws.identitycenter.awspermissionset import (
    PermissionSetToAWSRoleRel,
)
from cartography.models.aws.identitycenter.awssogroup import (
    AWSSSOGroupToPermissionSetRel,
)
from cartography.models.aws.identitycenter.awsssouser import (
    AWSSSOUserToPermissionSetRel,
)
from cartography.models.aws.identitycenter.awsssouser import AWSSSOUserToSSOGroupRel
from cartography.models.aws.lambda_function.lambda_function import (
    AWSLambdaToECRImageRel,
)
from cartography.models.aws.lambda_function.lambda_function import (
    AWSLambdaToGCPArtifactRegistryImageRel,
)
from cartography.models.aws.lambda_function.lambda_function import (
    AWSLambdaToGitHubContainerImageRel,
)
from cartography.models.aws.lambda_function.lambda_function import (
    AWSLambdaToGitLabContainerImageRel,
)
from cartography.models.aws.lambda_function.lambda_function import (
    AWSLambdaToPrincipalRel,
)
from cartography.models.azure.container_instance import (
    AzureContainerInstanceToECRImageRel,
)
from cartography.models.azure.container_instance import (
    AzureContainerInstanceToGCPArtifactRegistryImageRel,
)
from cartography.models.azure.container_instance import (
    AzureContainerInstanceToGitHubContainerImageRel,
)
from cartography.models.azure.container_instance import (
    AzureContainerInstanceToGitLabContainerImageRel,
)
from cartography.models.azure.container_instance import (
    AzureGroupContainerToContainerInstanceRel,
)
from cartography.models.azure.function_app import AzureFunctionAppToECRImageRel
from cartography.models.azure.function_app import (
    AzureFunctionAppToGCPArtifactRegistryImageRel,
)
from cartography.models.azure.function_app import (
    AzureFunctionAppToGitHubContainerImageRel,
)
from cartography.models.azure.function_app import (
    AzureFunctionAppToGitLabContainerImageRel,
)
from cartography.models.duo.user import DuoGroupToDuoUserRel
from cartography.models.gcp.cloudrun.job import CloudRunJobToServiceAccountRel
from cartography.models.gcp.cloudrun.job_container import (
    CloudRunJobContainerToArtifactRegistryImageRel,
)
from cartography.models.gcp.cloudrun.job_container import (
    CloudRunJobContainerToECRImageRel,
)
from cartography.models.gcp.cloudrun.job_container import (
    CloudRunJobContainerToGitHubContainerImageRel,
)
from cartography.models.gcp.cloudrun.job_container import (
    CloudRunJobContainerToGitLabContainerImageRel,
)
from cartography.models.gcp.cloudrun.job_container import CloudRunJobToContainerRel
from cartography.models.gcp.cloudrun.service import CloudRunServiceToServiceAccountRel
from cartography.models.gcp.cloudrun.service_container import (
    CloudRunServiceContainerToArtifactRegistryImageRel,
)
from cartography.models.gcp.cloudrun.service_container import (
    CloudRunServiceContainerToECRImageRel,
)
from cartography.models.gcp.cloudrun.service_container import (
    CloudRunServiceContainerToGitHubContainerImageRel,
)
from cartography.models.gcp.cloudrun.service_container import (
    CloudRunServiceContainerToGitLabContainerImageRel,
)
from cartography.models.gcp.cloudrun.service_container import (
    CloudRunServiceToContainerRel,
)
from cartography.models.gcp.iam_keys import GCPServiceAccountKeyToServiceAccountRel
from cartography.models.github.personal_access_tokens import (
    GitHubPersonalAccessTokenToOwnerUserRel,
)
from cartography.models.github.teams import GitHubTeamChildTeamRel
from cartography.models.github.teams import GitHubTeamMaintainerUserRel
from cartography.models.github.teams import GitHubTeamMemberUserRel
from cartography.models.googleworkspace.group import (
    GoogleWorkspaceGroupToGroupInheritedMemberRel,
)
from cartography.models.googleworkspace.group import (
    GoogleWorkspaceGroupToGroupInheritedOwnerRel,
)
from cartography.models.googleworkspace.group import GoogleWorkspaceGroupToGroupOwnerRel
from cartography.models.googleworkspace.group import GoogleWorkspaceGroupToOwnerRel
from cartography.models.googleworkspace.group import (
    GoogleWorkspaceUserToGroupInheritedMemberRel,
)
from cartography.models.googleworkspace.group import (
    GoogleWorkspaceUserToGroupInheritedOwnerRel,
)
from cartography.models.gsuite.group import GSuiteGroupToGroupMemberRel
from cartography.models.gsuite.group import GSuiteGroupToGroupOwnerRel
from cartography.models.gsuite.group import GSuiteGroupToMemberRel
from cartography.models.gsuite.group import GSuiteGroupToOwnerRel
from cartography.models.keycloak.group import KeycloakGroupToGroupRel
from cartography.models.keycloak.group import KeycloakGroupToRoleRel
from cartography.models.keycloak.inheritance import KeycloakUserAssumeRoleMatchLink
from cartography.models.keycloak.inheritance import (
    KeycloakUserInheritedMemberOfGroupMatchLink,
)
from cartography.models.keycloak.role import KeycloakRoleToUserRel
from cartography.models.kubernetes.containers import KubernetesContainerToECRImageRel
from cartography.models.kubernetes.containers import (
    KubernetesContainerToGCPArtifactRegistryImageRel,
)
from cartography.models.kubernetes.containers import (
    KubernetesContainerToGitHubContainerImageRel,
)
from cartography.models.kubernetes.containers import (
    KubernetesContainerToGitLabContainerImageRel,
)
from cartography.models.kubernetes.containers import (
    KubernetesContainerToKubernetesPodRel,
)
from cartography.models.kubernetes.groups import KubernetesGroupToAWSRoleRel
from cartography.models.kubernetes.groups import KubernetesGroupToAWSUserRel
from cartography.models.kubernetes.namespaces import (
    KubernetesNamespaceToKubernetesClusterRel,
)
from cartography.models.kubernetes.pods import KubernetesPodToKubernetesClusterRel
from cartography.models.kubernetes.pods import KubernetesPodToKubernetesNamespaceRel
from cartography.models.kubernetes.pods import KubernetesPodToSecretEnvRel
from cartography.models.kubernetes.pods import KubernetesPodToSecretVolumeRel
from cartography.models.kubernetes.pods import KubernetesPodToServiceAccountRel
from cartography.models.kubernetes.serviceaccounts import (
    KubernetesServiceAccountToAWSRoleRel,
)
from cartography.models.kubernetes.users import KubernetesUserToAWSRoleRel
from cartography.models.oci.group import OCIGroupToOCIUserRel
from cartography.models.oci.policy import OCIPolicyToGroupRefRel
from cartography.models.openai.adminapikey import OpenAIAdminApiKeyToSARel
from cartography.models.openai.adminapikey import OpenAIAdminApiKeyToUserRel
from cartography.models.openai.apikey import OpenAIApiKeyToSARel
from cartography.models.openai.apikey import OpenAIApiKeyToUserRel
from cartography.models.scaleway.iam.apikey import ScalewayApiKeyToApplicationRel
from cartography.models.scaleway.iam.apikey import ScalewayApiKeyToUserRel
from cartography.models.scaleway.serverless.container import (
    ScalewayServerlessContainerToImageRel,
)
from cartography.models.sentry.member import SentryUserToTeamAdminOfRel
from cartography.models.slack.group import SlackGroupToCreatorRel
from cartography.models.tailscale.group import (
    TailscaleUserToGroupInheritedMemberMatchLink,
)


# DEPRECATED: pre-V1 rel classes tolerated until they are removed in v1.0.0.
LEGACY_REL_WHITELIST: frozenset[type] = frozenset(
    {
        # DEPRECATED: replaced by WORKLOAD_PARENT, will be removed in v1.0.0.
        AzureGroupContainerToContainerInstanceRel,
        CloudRunJobToContainerRel,
        CloudRunServiceToContainerRel,
        ECSContainerToTaskRel,
        ECSServiceToECSClusterRel,
        ECSServiceToECSTaskRel,
        ECSTaskToECSClusterRel,
        KubernetesContainerToKubernetesPodRel,
        KubernetesPodToKubernetesNamespaceRel,
        # Kubernetes models its cluster as the tenant, so the pod's and
        # namespace's sub_resource_relationship uses RESOURCE on a pair that
        # the ontology also constrains as WORKLOAD_PARENT. Whitelisted until
        # tenant scoping and the workload chain are reconciled.
        KubernetesNamespaceToKubernetesClusterRel,
        KubernetesPodToKubernetesClusterRel,
        # DEPRECATED: replaced by HAS_ROLE, will be removed in v1.0.0.
        AWSSSOUserToPermissionSetRel,
        KeycloakRoleToUserRel,
        KeycloakUserAssumeRoleMatchLink,
        AWSSSOGroupToPermissionSetRel,
        KeycloakGroupToRoleRel,
        # ALLOWED_BY is a distinct "this role is assumable by that SSO user"
        # semantic (PermissionRole->UserAccount), not a role assignment, so it
        # intentionally runs counter to the HAS_ROLE (UserAccount->PermissionRole)
        # direction. Whitelisted so the constraint does not flag it.
        AWSRoleToSSOUserMatchLink,
        # MAPS_TO is an identity-federation mapping (a Kubernetes user authenticates
        # as an AWS role/user), not a role grant. Distinct from HAS_ROLE.
        KubernetesUserToAWSRoleRel,
        # ASSUMED_ROLE_WITH_SAML records a CloudTrail-observed runtime assumption
        # event, not a static role assignment. Distinct from HAS_ROLE.
        AssumedRoleWithSAMLMatchLink,
        # ASSUMES_ROLE is workload-identity federation (a Kubernetes service
        # account assumes an AWS IAM role, IRSA-style). This is the canonical
        # ASSUMES semantic, not a static role grant. Distinct from HAS_ROLE.
        KubernetesServiceAccountToAWSRoleRel,
        # STS_ASSUMEROLE_ALLOW models the AWS IAM trust-policy graph (which
        # principals a role permits to assume it) and spans User/Role/Group/
        # EC2/Lambda principals; it is consumed by the privilege-escalation
        # rules. The canonical ontology ASSUMES edge (Function/ComputeInstance
        # -> PermissionRole) now coexists on AWSLambda. This rel declares its
        # target as the generic AWSPrincipal, but at runtime the matched
        # execution-role node also carries :PermissionRole, so it is a
        # deliberate Function->PermissionRole overlap. Whitelisted to make that
        # intent explicit (the guard resolves AWSPrincipal atomically and would
        # not otherwise surface it). Distinct from the canonical ASSUMES edge.
        AWSLambdaToPrincipalRel,
        # ALLOWED_BY (PermissionRole->UserGroup) is "this role is assumable by
        # that SSO group", the reverse of a group role grant. Distinct from the
        # UserGroup->PermissionRole HAS_ROLE edge.
        AWSRoleToSSOGroupMatchLink,
        # MAPS_TO is identity federation (an AWS role maps to a Kubernetes
        # group), not a group role grant. Distinct from HAS_ROLE.
        KubernetesGroupToAWSRoleRel,
        # OCI_POLICY_REFERENCE records that a policy statement textually
        # references a group, not that the group holds the policy. Distinct
        # from HAS_ROLE.
        OCIPolicyToGroupRefRel,
        # ASSIGNED_TO_ROLE provisions an AWS permission set as a concrete IAM
        # role in a target account (implementation link), not a composite-role
        # hierarchy. Distinct from the INCLUDES role->role edge.
        PermissionSetToAWSRoleRel,
        # DEPRECATED: replaced by USES_SECRET (mount method captured as the
        # mount_method property), will be removed in v1.0.0.
        KubernetesPodToSecretVolumeRel,
        KubernetesPodToSecretEnvRel,
        # DEPRECATED: replaced by MEMBER_OF, will be removed in v1.0.0.
        AWSGroupToAWSUserRel,
        AWSSSOUserToSSOGroupRel,
        DuoGroupToDuoUserRel,
        GSuiteGroupToMemberRel,
        GSuiteGroupToGroupMemberRel,
        GitHubTeamMemberUserRel,
        GitHubTeamChildTeamRel,
        KeycloakGroupToGroupRel,
        OCIGroupToOCIUserRel,
        # Group "owner"/"maintainer"/"admin" edges mark a privileged role held
        # within the group, a distinct semantic from plain membership. The
        # principals remain reachable through these edges; MEMBER_OF is reserved
        # for generic membership.
        GSuiteGroupToOwnerRel,
        GSuiteGroupToGroupOwnerRel,
        GoogleWorkspaceGroupToOwnerRel,
        GoogleWorkspaceGroupToGroupOwnerRel,
        GitHubTeamMaintainerUserRel,
        SentryUserToTeamAdminOfRel,
        # CREATED records who created a Slack usergroup, a historical fact rather
        # than current membership. Distinct from MEMBER_OF.
        SlackGroupToCreatorRel,
        # MAPS_TO is identity federation (a Kubernetes group maps to an AWS
        # user), not group membership. Distinct from MEMBER_OF.
        KubernetesGroupToAWSUserRel,
        # DEPRECATED: replaced by OWNED_BY (the canonical APIKey->identity
        # direction), will be removed in v1.0.0. These edges express the same
        # ownership in the reverse (identity->key) direction under provider
        # labels (OWNS / HAS / HAS_KEY / AWS_ACCESS_KEY).
        AccountAccessKeyToAWSUserRel,
        AnthropicApiKeyToUserRel,
        GCPServiceAccountKeyToServiceAccountRel,
        GitHubPersonalAccessTokenToOwnerUserRel,
        OpenAIApiKeyToUserRel,
        OpenAIApiKeyToSARel,
        OpenAIAdminApiKeyToUserRel,
        OpenAIAdminApiKeyToSARel,
        ScalewayApiKeyToUserRel,
        ScalewayApiKeyToApplicationRel,
        # DEPRECATED: replaced by RUNS_AS (the canonical workload->service
        # account edge), will be removed in v1.0.0.
        KubernetesPodToServiceAccountRel,
        CloudRunServiceToServiceAccountRel,
        CloudRunJobToServiceAccountRel,
        # INHERITED_MEMBER_OF / INHERITED_OWNER_OF are transitive memberships
        # computed across nested groups, intentionally kept separate from the
        # direct MEMBER_OF edge.
        GoogleWorkspaceGroupToGroupInheritedMemberRel,
        GoogleWorkspaceGroupToGroupInheritedOwnerRel,
        GoogleWorkspaceUserToGroupInheritedMemberRel,
        GoogleWorkspaceUserToGroupInheritedOwnerRel,
        KeycloakUserInheritedMemberOfGroupMatchLink,
        TailscaleUserToGroupInheritedMemberMatchLink,
        # HAS_IMAGE is the raw ingest-time (:Container|:Function)->(:Image)
        # reference, matched by runtime digest at load time and possibly pointing
        # at a manifest list. The canonical RESOLVED_IMAGE edge is derived from it
        # by resolved_image_analysis.json (resolving manifest lists to the concrete
        # single-platform image). Both coexist, so HAS_IMAGE is whitelisted as a
        # distinct semantic rather than a violation of RESOLVED_IMAGE.
        KubernetesContainerToECRImageRel,
        KubernetesContainerToGitLabContainerImageRel,
        KubernetesContainerToGCPArtifactRegistryImageRel,
        KubernetesContainerToGitHubContainerImageRel,
        ECSContainerToECRImageRel,
        ECSContainerToGitLabContainerImageRel,
        ECSContainerToGCPArtifactRegistryImageRel,
        ECSContainerToGitHubContainerImageRel,
        CloudRunServiceContainerToECRImageRel,
        CloudRunServiceContainerToGitLabContainerImageRel,
        CloudRunServiceContainerToArtifactRegistryImageRel,
        CloudRunServiceContainerToGitHubContainerImageRel,
        CloudRunJobContainerToECRImageRel,
        CloudRunJobContainerToGitLabContainerImageRel,
        CloudRunJobContainerToArtifactRegistryImageRel,
        CloudRunJobContainerToGitHubContainerImageRel,
        AzureContainerInstanceToECRImageRel,
        AzureContainerInstanceToGitLabContainerImageRel,
        AzureContainerInstanceToGCPArtifactRegistryImageRel,
        AzureContainerInstanceToGitHubContainerImageRel,
        ScalewayServerlessContainerToImageRel,
        AWSLambdaToECRImageRel,
        AWSLambdaToGitLabContainerImageRel,
        AWSLambdaToGCPArtifactRegistryImageRel,
        AWSLambdaToGitHubContainerImageRel,
        AzureFunctionAppToECRImageRel,
        AzureFunctionAppToGitLabContainerImageRel,
        AzureFunctionAppToGCPArtifactRegistryImageRel,
        AzureFunctionAppToGitHubContainerImageRel,
    }
)
