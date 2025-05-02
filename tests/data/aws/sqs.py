GET_SQS_QUEUE_ATTRIBUTES = [
    (
        "https://us-east-1.queue.amazonaws.com/000000000000/test-queue-1",
        {
            "QueueArn": "arn:aws:secretsmanager:us-east-1:000000000000:test-queue-1",
            "CreatedTimestamp": "1627539901900",
            "LastModifiedTimestamp": "1627539901900",
            "RedrivePolicy": '{"deadLetterTargetArn": "arn:aws:secretsmanager:us-east-1:000000000000:test-queue-2", "maxReceiveCount": "1"}',  # noqa: E501
            "VisibilityTimeout": "10",
        },
    ),
    (
        "https://us-east-1.queue.amazonaws.com/000000000000/test-queue-2",
        {
            "QueueArn": "arn:aws:secretsmanager:us-east-1:000000000000:test-queue-2",
            "CreatedTimestamp": "1627539901900",
            "LastModifiedTimestamp": "1627539901900",
            "VisibilityTimeout": "10",
        },
    ),
]
