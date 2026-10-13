import cartography.intel.railway.storage.volumes


def test_volume_instance_size_gb_is_none_when_size_missing():
    bundle = {
        "volumes": {"edges": []},
        "environments": {
            "edges": [
                {
                    "node": {
                        "volumeInstances": {
                            "edges": [{"node": {"id": "vi-1", "sizeMB": None}}],
                        },
                    },
                },
            ],
        },
    }

    _, instances = cartography.intel.railway.storage.volumes.transform(
        {"project-1": bundle},
    )

    assert instances["project-1"][0]["size_gb"] is None
