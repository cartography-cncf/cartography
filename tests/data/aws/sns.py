LIST_TOPICS = {
    "Topics": [
        {"TopicArn": "arn:aws:sns:us-east-1:123456789012:test-topic"},
    ]
}

TEST_RDS_EVENT_SUBSCRIPTION_TOPICS = [
    "arn:aws:sns:us-east-1:000000000000:rds_event_instance_sub",
    "arn:aws:sns:us-east-1:000000000000:rds_event_cluster_sub",
    "arn:aws:sns:us-east-1:000000000000:rds_event_snapshot_sub",
]

GET_TOPIC_ATTRIBUTES = {
    "Attributes": {
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:test-topic",
        "Owner": "123456789012",
        "DisplayName": "Test Topic",
        "SubscriptionsPending": "0",
        "SubscriptionsConfirmed": "1",
        "SubscriptionsDeleted": "0",
        "DeliveryPolicy": "{}",
        "EffectiveDeliveryPolicy": "{}",
        "KmsMasterKeyId": "arn:aws:kms:us-east-1:123456789012:key/test-key",
    }
}

LIST_SUBSCRIPTIONS = [
    {
        "SubscriptionArn": "arn:aws:sns:us-east-1:123456789012:test-topic:1111aaaa-2222-bbbb-3333-cccc4444dddd",
        "Owner": "123456789012",
        "Protocol": "email",
        "Endpoint": "example1@example.com",
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:test-topic",
    }
]
