from typing import Optional


def extract_bucket_name_from_s3_uri(s3_uri: str) -> Optional[str]:
    """
    Extract bucket name from S3 URI.

    Example: s3://my-bucket/path/to/data -> my-bucket
    """
    if not s3_uri or not s3_uri.startswith("s3://"):
        return None
    # Remove s3:// prefix and split on /
    bucket_name = s3_uri[5:].split("/")[0]
    return bucket_name if bucket_name else None
