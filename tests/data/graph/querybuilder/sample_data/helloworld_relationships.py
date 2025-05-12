MERGE_SUB_RESOURCE_QUERY = """
MERGE (s:SubResource{id: "sub-resource-id"})
ON CREATE SET s.lastupdated = 1
"""


MERGE_HELLO_ASSET_QUERY = """
MERGE (h:HelloAsset{id: "the-helloasset-id-1"})
ON CREATE SET h.lastupdated = 1
"""


MERGE_WORLD_ASSET_QUERY = """
MERGE (w:WorldAsset{id: "the-worldasset-id-1"})
ON CREATE SET w.lastupdated = 1
"""


# This dataset shows an InterestingNode attached to a WorldAsset but no other relationships.
INTERESTING_NODE_WITH_PARTIAL_RELS = [
    {
        "Id": "interesting-node-id",
        "property1": "b",
        "property2": "c",
        "AnotherField": "d",
        "YetAnotherRelField": "e",
        "world_asset_id": "the-worldasset-id-1",
    },
]

# This dataset shows an InterestingNode attached to a SubResource and a HelloAsset, but no WorldAsset.
INTERESTING_NODE_NO_WORLD_ASSET = [
    {
        "Id": "interesting-node-id",
        "property1": "b",
        "property2": "c",
        "AnotherField": "d",
        "YetAnotherRelField": "e",
        "hello_asset_id": "the-helloasset-id-1",
        "sub_resource_id": "sub-resource-id",
    },
]

# This dataset shows an InterestingNode attached to a HelloAsset and a WorldAsset.
INTERESTING_NODE_WITH_ALL_RELS = [
    {
        "Id": "interesting-node-id",
        "property1": "b",
        "property2": "c",
        "AnotherField": "d",
        "YetAnotherRelField": "e",
        "world_asset_id": "the-worldasset-id-1",
        "hello_asset_id": "the-helloasset-id-1",
        "sub_resource_id": "sub-resource-id",
    },
]

INTERESTING_NODE_SUB_RES_ONLY = [
    {
        "Id": "interesting-node-id",
        "property1": "b",
        "property2": "c",
        "AnotherField": "d",
        "YetAnotherRelField": "e",
        "sub_resource_id": "sub-resource-id",
    },
]
