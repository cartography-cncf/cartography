#!/usr/bin/env bash

# Reference - https://medium.com/better-programming/how-to-store-your-aws-lambda-secrets-cheaply-without-compromising-scalability-or-security-d3e8a250f12c

echo "Begin Set Environment Variables"

# Parse Arguments
# Parse Arguments
ENV=${1-}
file_name="env.${ENV}.json"

if [[ $ENV == "" ]]
then
	echo "Environment name is required, supported values: dev, prod"

	exit
fi

region=$(cat $file_name | jq -r '.region')
export CDX_DEFAULT_REGION=$region

log_level=$(cat $file_name | jq -r '.logLevel')
export CDX_DEFAULT_LOG_LEVEL=$log_level

app_env=$(cat $file_name | jq -r '.appEnv')
export CDX_APP_ENV=$app_env

cross_account_role_arn=$(cat $file_name | jq -r '.crossAccountRoleARN')
export CDX_CROSS_ACCOUNT_ROLE_ARN=$cross_account_role_arn

neo4j_uri=$(cat $file_name | jq -r '.neo4jURI')
export CDX_APP_NEO4J_URI=$neo4j_uri

neo4j_user=$(cat $file_name | jq -r '.neo4jUser')
export CDX_APP_NEO4J_USER=$neo4j_user

neo4j_pwd=$(cat $file_name | jq -r '.neo4jPWD')
export CDX_APP_NEO4J_PWD=$neo4j_pwd

echo "End Set Environment Variables"

echo "Begin deployment for AWS Service Worker"

sls deploy --force --verbose

echo "End deployment for AWS Service Worker"
