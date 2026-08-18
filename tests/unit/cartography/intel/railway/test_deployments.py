import copy

from cartography.intel.railway.deployments import transform
from tests.data.railway.bundles import RAILWAY_PROJECT_BUNDLE

PROJECT_ID = "33333333-3333-3333-3333-333333333333"
WEB_DEPLOYMENT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
POSTGRES_DEPLOYMENT_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def _deployments_by_id(bundle):
    deployments, _ = transform({PROJECT_ID: bundle})
    return {d["id"]: d for d in deployments[PROJECT_ID]}


def test_current_deployment_copies_registry_image_from_instance():
    by_id = _deployments_by_id(copy.deepcopy(RAILWAY_PROJECT_BUNDLE))

    # The web instance runs a registry image, so its current deployment gets it.
    web = by_id[WEB_DEPLOYMENT_ID]
    assert web["lifecycle"] == "current"
    assert web["image_uri"] == "nginxdemos/hello"
    # A bare tag reference is not digest-pinned.
    assert web["image_digest"] is None


def test_git_backed_deployment_has_no_image():
    by_id = _deployments_by_id(copy.deepcopy(RAILWAY_PROJECT_BUNDLE))

    # The Postgres instance is deployed from git (source.image is null), so no image ref.
    postgres = by_id[POSTGRES_DEPLOYMENT_ID]
    assert postgres["lifecycle"] == "current"
    assert postgres["image_uri"] is None
    assert postgres["image_digest"] is None


def test_digest_pinned_image_is_parsed():
    bundle = copy.deepcopy(RAILWAY_PROJECT_BUNDLE)
    digest = "sha256:" + "a" * 64
    for env_edge in bundle["environments"]["edges"]:
        for inst_edge in env_edge["node"]["serviceInstances"]["edges"]:
            source = inst_edge["node"].get("source") or {}
            if source.get("image") == "nginxdemos/hello":
                source["image"] = f"nginxdemos/hello@{digest}"

    web = _deployments_by_id(bundle)[WEB_DEPLOYMENT_ID]
    assert web["image_uri"] == f"nginxdemos/hello@{digest}"
    assert web["image_digest"] == digest


def test_superseded_deployment_has_no_image():
    bundle = copy.deepcopy(RAILWAY_PROJECT_BUNDLE)
    for env_edge in bundle["environments"]["edges"]:
        if env_edge["node"]["name"] != "production":
            continue
        env_edge["node"]["deployments"]["edges"].append(
            {
                "node": {
                    "id": "cccc0000-cccc-cccc-cccc-cccccccccccc",
                    "status": "CRASHED",
                    "statusUpdatedAt": "2026-07-27T17:00:00.000Z",
                    "createdAt": "2026-07-27T17:00:00.000Z",
                    "projectId": PROJECT_ID,
                    "environmentId": "44444444-4444-4444-4444-444444444444",
                    "serviceId": "66666666-6666-6666-6666-666666666666",
                    "url": None,
                    "staticUrl": None,
                    "canRedeploy": True,
                },
            },
        )

    superseded = _deployments_by_id(bundle)["cccc0000-cccc-cccc-cccc-cccccccccccc"]
    assert superseded["lifecycle"] == "historical"
    assert superseded["image_uri"] is None
    assert superseded["image_digest"] is None
