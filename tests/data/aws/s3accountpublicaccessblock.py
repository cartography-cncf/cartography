"""
Mock data for S3 Account Public Access Block tests.
"""

GET_PUBLIC_ACCESS_BLOCK = {
    "PublicAccessBlockConfiguration": {
        "BlockPublicAcls": True,
        "IgnorePublicAcls": True,
        "BlockPublicPolicy": True,
        "RestrictPublicBuckets": True,
    }
}

GET_PUBLIC_ACCESS_BLOCK_NONE = None


GET_PUBLIC_ACCESS_BLOCK_PARTIAL = {
    "PublicAccessBlockConfiguration": {
        "BlockPublicAcls": True,
        "IgnorePublicAcls": False,
        "BlockPublicPolicy": True,
        "RestrictPublicBuckets": False,
    }
}
