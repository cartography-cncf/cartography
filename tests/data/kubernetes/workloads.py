"""Raw (kubernetes-client-like) fixtures for the workload-controller sync.

Each object mimics the attributes of the typed ``V1*`` models that the intel
transforms read (``metadata`` / ``spec`` / ``status``), so tests can monkeypatch
the ``get_*`` functions and exercise ``sync_workloads`` / ``sync_pods``
end-to-end.

Scenario (cluster 1, namespace ``my-namespace``):

- Deployment ``web`` -> ReplicaSet ``web-rs`` -> Pod ``web-pod``
- StatefulSet ``db`` -> Pod ``db-pod``
- DaemonSet ``agent`` -> Pod ``agent-pod``
- CronJob ``report`` -> Job ``report-123`` -> Pod ``report-pod``
- standalone Job ``migrate`` -> Pod ``migrate-pod``
- bare Pod ``bare-pod`` (no controller)
"""

from types import SimpleNamespace

NAMESPACE = "my-namespace"

DEPLOYMENT_UID = "dep-web-uid"
REPLICASET_UID = "rs-web-uid"
STATEFULSET_UID = "ss-db-uid"
DAEMONSET_UID = "ds-agent-uid"
CRONJOB_UID = "cj-report-uid"
JOB_CRON_UID = "job-report-uid"
JOB_STANDALONE_UID = "job-migrate-uid"

POD_WEB_UID = "pod-web-uid"
POD_DB_UID = "pod-db-uid"
POD_AGENT_UID = "pod-agent-uid"
POD_REPORT_UID = "pod-report-uid"
POD_MIGRATE_UID = "pod-migrate-uid"
POD_BARE_UID = "pod-bare-uid"


def _owner_ref(
    kind: str, uid: str, name: str, controller: bool = True
) -> SimpleNamespace:
    return SimpleNamespace(
        kind=kind,
        uid=uid,
        name=name,
        api_version="apps/v1",
        controller=controller,
    )


def _meta(
    uid: str,
    name: str,
    owner_references: list | None = None,
    labels: dict | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        uid=uid,
        name=name,
        namespace=NAMESPACE,
        creation_timestamp=None,
        deletion_timestamp=None,
        labels=labels or {},
        owner_references=owner_references or [],
    )


def get_raw_deployments() -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            metadata=_meta(DEPLOYMENT_UID, "web"),
            spec=SimpleNamespace(replicas=3),
            status=SimpleNamespace(ready_replicas=3, available_replicas=3),
        ),
    ]


def get_raw_replicasets() -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            metadata=_meta(
                REPLICASET_UID,
                "web-rs",
                owner_references=[_owner_ref("Deployment", DEPLOYMENT_UID, "web")],
            ),
            spec=SimpleNamespace(replicas=3),
            status=SimpleNamespace(ready_replicas=3),
        ),
    ]


def get_raw_statefulsets() -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            metadata=_meta(STATEFULSET_UID, "db"),
            spec=SimpleNamespace(replicas=2, service_name="db"),
            status=SimpleNamespace(ready_replicas=2),
        ),
    ]


def get_raw_daemonsets() -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            metadata=_meta(DAEMONSET_UID, "agent"),
            spec=SimpleNamespace(),
            status=SimpleNamespace(desired_number_scheduled=5, number_ready=5),
        ),
    ]


def get_raw_cronjobs() -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            metadata=_meta(CRONJOB_UID, "report"),
            spec=SimpleNamespace(schedule="*/5 * * * *", suspend=False),
            status=SimpleNamespace(),
        ),
    ]


def get_raw_jobs() -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            metadata=_meta(
                JOB_CRON_UID,
                "report-123",
                owner_references=[_owner_ref("CronJob", CRONJOB_UID, "report")],
            ),
            spec=SimpleNamespace(completions=1, parallelism=1),
            status=SimpleNamespace(active=0, succeeded=1, failed=0),
        ),
        SimpleNamespace(
            metadata=_meta(JOB_STANDALONE_UID, "migrate"),
            spec=SimpleNamespace(completions=1, parallelism=1),
            status=SimpleNamespace(active=1, succeeded=0, failed=0),
        ),
    ]


def _raw_pod(
    uid: str,
    name: str,
    owner_references: list | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        metadata=SimpleNamespace(
            uid=uid,
            name=name,
            namespace=NAMESPACE,
            creation_timestamp=None,
            deletion_timestamp=None,
            labels={},
            owner_references=owner_references or [],
        ),
        spec=SimpleNamespace(
            containers=[],
            volumes=[],
            node_name="my-node",
            service_account_name="default",
        ),
        status=SimpleNamespace(phase="Running", container_statuses=[]),
    )


def get_raw_pods() -> list[SimpleNamespace]:
    return [
        _raw_pod(
            POD_WEB_UID,
            "web-pod",
            owner_references=[_owner_ref("ReplicaSet", REPLICASET_UID, "web-rs")],
        ),
        _raw_pod(
            POD_DB_UID,
            "db-pod",
            owner_references=[_owner_ref("StatefulSet", STATEFULSET_UID, "db")],
        ),
        _raw_pod(
            POD_AGENT_UID,
            "agent-pod",
            owner_references=[_owner_ref("DaemonSet", DAEMONSET_UID, "agent")],
        ),
        _raw_pod(
            POD_REPORT_UID,
            "report-pod",
            owner_references=[_owner_ref("Job", JOB_CRON_UID, "report-123")],
        ),
        _raw_pod(
            POD_MIGRATE_UID,
            "migrate-pod",
            owner_references=[_owner_ref("Job", JOB_STANDALONE_UID, "migrate")],
        ),
        _raw_pod(POD_BARE_UID, "bare-pod"),
    ]
