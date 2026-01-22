AIRBYTE_DESTINATIONS = [
    {
        "destinationId": "30e064ed-4211-4868-9b8f-e2bbc8f8969a",
        "name": "S3",
        "destinationType": "s3",
        "definitionId": "4816b78f-1489-44c1-9060-4b19d5fa9362",
        "workspaceId": "e4388e31-9c21-461b-9b5d-1905ca28c599",
        "configuration": {
            "format": {
                "flattening": "No flattening",
                "compression": {"compression_type": "No Compression"},
                "format_type": "CSV",
            },
            "s3_endpoint": "https://cellar-c2.services.clever-cloud.com",
            "s3_bucket_name": "bucket-cartography",
            "s3_bucket_path": "bucket-cartography/",
            "s3_bucket_region": "af-south-1",
        },
        "createdAt": 1748426507,
    }
]
