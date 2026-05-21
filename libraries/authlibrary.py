# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sts.html
# https://docs.aws.amazon.com/STS/latest/APIReference/CommonErrors.html
import boto3
from boto3.session import Session
from botocore.exceptions import ClientError

from utils.errors import classify_error


class AuthLibrary:
    def __init__(self, context):
        self.context = context

    def _get_cross_account_session(self) -> Session:
        """Assume the cross-account role using the execution role's default credentials."""
        sts_client = boto3.client("sts", region_name="us-east-1")
        response = sts_client.assume_role(
            RoleArn=self.context.cross_account_role_arn,
            RoleSessionName="cdx-cross-account-session",
        )
        return Session(
            aws_access_key_id=response["Credentials"]["AccessKeyId"],
            aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
            aws_session_token=response["Credentials"]["SessionToken"],
        )

    def assume_role(self, args):
        # Use cross-account role session to assume customer role
        session = self._get_cross_account_session()

        try:
            sts_client = session.client(
                "sts",
                region_name="us-east-1",
                # endpoint_url=f"https://sts.{region_name}.amazonaws.com",
            )
        except ClientError as e:
            raise classify_error(self.context.logger, e, "Failed to create STS client")

        try:
            response = sts_client.assume_role(
                ExternalId=args["external_id"],
                RoleArn=args["role_arn"],
                RoleSessionName=args["role_session_name"],
                DurationSeconds=3600 * 4,
            )

        except ClientError:
            try:
                response = sts_client.assume_role(
                    ExternalId=args["external_id"],
                    RoleArn=args["role_arn"],
                    RoleSessionName=args["role_session_name"],
                    DurationSeconds=3600,
                )

            except ClientError as e:
                # TODO: Check if the error is related to Duration, if yes, retry with 1 hour
                raise classify_error(self.context.logger, e, "Failed to assume role")

        return {
            "aws_access_key_id": response["Credentials"]["AccessKeyId"],
            "aws_secret_access_key": response["Credentials"]["SecretAccessKey"],
            "session_token": response["Credentials"]["SessionToken"],
            "expiration": response["Credentials"]["Expiration"],
        }

    def get_session(self, creds):
        # Create a Session with the credentials passed
        if creds["type"] == "credentials":
            return Session(
                aws_access_key_id=creds["aws_access_key_id"],
                aws_secret_access_key=creds["aws_secret_access_key"],
            )

        elif creds["type"] == "assumerole":
            return Session(
                aws_access_key_id=creds["aws_access_key_id"],
                aws_secret_access_key=creds["aws_secret_access_key"],
                aws_session_token=creds["session_token"],
            )
