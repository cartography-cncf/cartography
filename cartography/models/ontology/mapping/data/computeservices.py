# Ontology mapping for the ComputeService semantic label.
#
# _ont_name - The display name of the service / orchestrator.
# _ont_region - The region or location where the service is deployed.
# _ont_status - Service provisioning/operational status, normalized to the shared
#   canonical set: active, creating, updating, deleting, failed, unknown.
#   The raw provider value stays on the source node's own status property.
from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# AWS ECS service status
_AWS_ECS_SERVICE_STATUS = {
    "ACTIVE": "active",
    "DRAINING": "deleting",
    "INACTIVE": "deleting",
}

# Scaleway ContainerStatus
_SCALEWAY_SERVICE_STATUS = {
    "unknown": "unknown",
    "creating": "creating",
    "pending": "creating",
    "created": "creating",
    "upgrading": "updating",
    "ready": "active",
    "deleting": "deleting",
    "error": "failed",
    "locking": "failed",
    "locked": "failed",
}

aws_ecs_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSECSService",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _AWS_ECS_SERVICE_STATUS},
                ),
            ],
        ),
    ],
)

gcp_cloudrun_service_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPCloudRunService",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="region", node_field="location"),
                # status: GCPCloudRunService does not surface a single provisioning
                # status field; revision-level state lives on GCPCloudRunRevision.
            ],
        ),
    ],
)

gcp_cloudrun_job_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPCloudRunJob",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="region", node_field="location"),
                # status: GCPCloudRunJob does not surface a single provisioning
                # status field; per-execution state lives on GCPCloudRunExecution.
            ],
        ),
    ],
)

scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayServerlessContainer",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _SCALEWAY_SERVICE_STATUS},
                ),
            ],
        ),
    ],
)

# Kubernetes workload controllers are the logical-workload peer of an ECS service
# / Cloud Run service. They carry no region and no single provisioning-status
# field, so only the display name is mapped.
kubernetes_mapping = OntologyMapping(
    module_name="kubernetes",
    nodes=[
        OntologyNodeMapping(
            node_label="KubernetesDeployment",
            fields=[OntologyFieldMapping(ontology_field="name", node_field="name")],
        ),
        OntologyNodeMapping(
            node_label="KubernetesStatefulSet",
            fields=[OntologyFieldMapping(ontology_field="name", node_field="name")],
        ),
        OntologyNodeMapping(
            node_label="KubernetesDaemonSet",
            fields=[OntologyFieldMapping(ontology_field="name", node_field="name")],
        ),
        OntologyNodeMapping(
            node_label="KubernetesJob",
            fields=[OntologyFieldMapping(ontology_field="name", node_field="name")],
        ),
        OntologyNodeMapping(
            node_label="KubernetesCronJob",
            fields=[OntologyFieldMapping(ontology_field="name", node_field="name")],
        ),
    ],
)

# Railway deployment status, as reported on the service instance's latest deployment.
_RAILWAY_SERVICE_STATUS = {
    "QUEUED": "creating",
    "INITIALIZING": "creating",
    "BUILDING": "creating",
    "DEPLOYING": "creating",
    "WAITING": "creating",
    "NEEDS_APPROVAL": "creating",
    "SUCCESS": "active",
    "SLEEPING": "active",
    "REMOVING": "deleting",
    "REMOVED": "deleting",
    "FAILED": "failed",
    "CRASHED": "failed",
    "SKIPPED": "unknown",
}

# A Railway service instance is one service deployed into one environment. That is the
# logical-workload peer of an ECS service or a Cloud Run service.
railway_mapping = OntologyMapping(
    module_name="railway",
    nodes=[
        OntologyNodeMapping(
            node_label="RailwayServiceInstance",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="service_name"),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="latest_deployment_status",
                    special_handling="mapping",
                    extra={"map": _RAILWAY_SERVICE_STATUS},
                ),
            ],
        ),
    ],
)

# Modal AppState. The shared canonical set is
# {active, creating, updating, deleting, failed, unknown}, which has no "stopped": a stopped
# Modal app collapses to "deleting", the same choice AWS ECS makes for INACTIVE. Modal has no
# update state, and the disabled / disconnected / derived variants have no equivalent at all.
_MODAL_APP_STATUS = {
    "APP_STATE_UNSPECIFIED": "unknown",
    "APP_STATE_INITIALIZING": "creating",
    "APP_STATE_EPHEMERAL": "active",
    "APP_STATE_DETACHED": "active",
    "APP_STATE_DEPLOYED": "active",
    "APP_STATE_STOPPING": "deleting",
    "APP_STATE_STOPPED": "deleting",
    "APP_STATE_DISABLED": "unknown",
    "APP_STATE_DETACHED_DISCONNECTED": "unknown",
    "APP_STATE_DERIVED": "unknown",
}

modal_mapping = OntologyMapping(
    module_name="modal",
    nodes=[
        OntologyNodeMapping(
            node_label="ModalApp",
            fields=[
                # Ephemeral apps have no name; the description is then the only human label.
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="name",
                    required=True,
                    special_handling="coalesce",
                    extra={"fields": ["description"]},
                ),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="state",
                    special_handling="mapping",
                    extra={"map": _MODAL_APP_STATUS},
                ),
                # region: a Modal app is multi-region; no single region is exposed.
            ],
        ),
    ],
)


# Netlify site state. "current" is the state of a site serving its latest production deploy;
# the rest are the states a site moves through while building or after being taken offline.
# `disabled` and `suspended` fall back to "unknown" because the canonical set has no member for
# "provisioned but deliberately not serving"; the raw value stays on NetlifySite.state, and
# NetlifySite.disabled / .disabled_reason carry the detail.
_NETLIFY_SITE_STATUS = {
    "current": "active",
    "building": "creating",
    "enqueued": "creating",
    "new": "creating",
    "error": "failed",
    "disabled": "unknown",
    "suspended": "unknown",
}

netlify_mapping = OntologyMapping(
    module_name="netlify",
    nodes=[
        OntologyNodeMapping(
            node_label="NetlifySite",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                # A Netlify site is served from the global edge, so it has no single region.
                # `functions_region` is where its serverless functions run, which is already on
                # NetlifyFunction, so mapping it here would misreport the site's own placement.
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="state",
                    special_handling="mapping",
                    extra={"map": _NETLIFY_SITE_STATUS},
                ),
            ],
        ),
    ],
)

COMPUTESERVICES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws_ecs": aws_ecs_mapping,
    "gcp_cloudrun_service": gcp_cloudrun_service_mapping,
    "gcp_cloudrun_job": gcp_cloudrun_job_mapping,
    "scaleway": scaleway_mapping,
    "kubernetes": kubernetes_mapping,
    "railway": railway_mapping,
    "modal": modal_mapping,
    "netlify": netlify_mapping,
}
