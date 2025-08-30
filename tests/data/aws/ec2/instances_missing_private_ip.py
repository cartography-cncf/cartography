DESCRIBE_INSTANCES_MISSING_PRIVATE_IP = {
    "Reservations": [
        {
            "ReservationId": "r-1",
            "OwnerId": "123456789012",
            "Instances": [
                {
                    "InstanceId": "i-missing",
                    "NetworkInterfaces": [
                        {
                            "NetworkInterfaceId": "eni-1",
                            "Status": "in-use",
                            "MacAddress": "00:00:00:00:00:00",
                            "Description": "",
                            "Groups": [
                                {"GroupId": "sg-1", "GroupName": "group1"},
                            ],
                            # PrivateIpAddress intentionally missing
                        }
                    ],
                    "BlockDeviceMappings": [],
                }
            ],
        }
    ]
}
