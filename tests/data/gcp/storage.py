# flake8: noqa
STORAGE_RESPONSE = {
    "kind": "storage#buckets",
    "items": [
        {
            "kind": "storage#bucket",
            "id": "bucket_name",
            "selfLink": "https://www.googleapis.com/storage/v1/b/bucket_name",
            "projectNumber": 9999,
            "name": "bucket_name",
            "timeCreated": "some_time",
            "updated": "some_time",
            "metageneration": "1",
            "iamConfiguration": {
                "bucketPolicyOnly": {
                    "enabled": False,
                },
                "uniformBucketLevelAccess": {
                    "enabled": False,
                },
            },
            "location": "US",
            "locationType": "multi-region",
            "defaultEventBasedHold": False,
            "storageClass": "STANDARD",
            "etag": "CAE=",
            "labels": {
                "label_key_1": "label_value_1",
                "label_key_2": "label_value_2",
            },
        },
    ],
}
