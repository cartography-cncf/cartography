import cartography.intel.railway.serviceinstances


def test_unverified_custom_domain_alone_is_not_exposure():
    # A custom domain that has not passed DNS verification does not resolve yet.
    bundle = {
        "environments": {
            "edges": [
                {
                    "node": {
                        "serviceInstances": {
                            "edges": [
                                {
                                    "node": {
                                        "id": "instance-1",
                                        "source": {},
                                        "latestDeployment": None,
                                        "domains": {
                                            "serviceDomains": [],
                                            "customDomains": [
                                                {
                                                    "id": "cd-1",
                                                    # Live, so only `verified` decides.
                                                    "syncStatus": "ACTIVE",
                                                    "status": {"verified": False},
                                                },
                                            ],
                                        },
                                    },
                                },
                            ],
                        },
                    },
                },
            ],
        },
    }

    result = cartography.intel.railway.serviceinstances.transform(
        {"project-1": bundle},
        {},
    )

    assert result["project-1"][0]["exposed_internet"] is False
    assert result["project-1"][0]["exposed_internet_type"] is None
    assert result["project-1"][0]["is_publicly_exposed"] is False
