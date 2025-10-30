# Date constants
DEVICE_1_CREATE_TIME = "2025-10-28T00:31:28.806Z"
DEVICE_2_CREATE_TIME = "2025-10-23T18:37:43.331Z"
DEVICE_2_LAST_SYNC_TIME = "2025-10-27T23:50:48.789Z"

MOCK_DEVICES_RESPONSE = [
    {
        "name": "devices/EiRlNzYzZjYyNC1lNWMyLTQ3NmItODI4Yi03ZThiMGIyNjVjZjM%3D",
        "createTime": DEVICE_1_CREATE_TIME,
        "lastSyncTime": DEVICE_1_CREATE_TIME,
        "ownerType": "BYOD",
        "model": "KB2005",
        "deviceType": "ANDROID",
        "androidSpecificAttributes": {},
        "deviceId": "3aac7e1206db9d26",
    },
    {
        "name": "devices/EiQ4Mzk2Y2YxMS1lODhjLTRhM2ItYmQ1Zi1kZWYwMjQ2NTdhNGU%3D",
        "createTime": DEVICE_2_CREATE_TIME,
        "lastSyncTime": DEVICE_2_LAST_SYNC_TIME,
        "ownerType": "BYOD",
        "model": "Mac16,5",
        "osVersion": "MacOS 26.0.1",
        "deviceType": "MAC_OS",
        "manufacturer": "Apple Inc.",
        "androidSpecificAttributes": {},
        "deviceId": "8396cf11-e88c-4a3b-bd5f-def024657a4e",
        "encryptionState": "ENCRYPTED",
    },
]

MOCK_DEVICE_USERS_RESPONSE = [
    {
        "name": "devices/EiRlNzYzZjYyNC1lNWMyLTQ3NmItODI4Yi03ZThiMGIyNjVjZjM%3D/deviceUsers/e763f624-e5c2-476b-828b-7e8b0b265cf3",
        "userEmail": "dana.dinesh@goodenoughlabs.ai",
        "managementState": "APPROVED",
        "firstSyncTime": DEVICE_1_CREATE_TIME,
        "lastSyncTime": DEVICE_1_CREATE_TIME,
        "passwordState": "PASSWORD_SET",
        "createTime": DEVICE_1_CREATE_TIME,
    },
    {
        "name": "devices/EiQ4Mzk2Y2YxMS1lODhjLTRhM2ItYmQ1Zi1kZWYwMjQ2NTdhNGU%3D/deviceUsers/8396cf11-e88c-4a3b-bd5f-def024657a4e",
        "userEmail": "gil.fowler@goodenoughlabs.ai",
        "managementState": "APPROVED",
        "firstSyncTime": DEVICE_2_CREATE_TIME,
        "lastSyncTime": DEVICE_2_LAST_SYNC_TIME,
        "passwordState": "PASSWORD_SET",
        "createTime": DEVICE_2_CREATE_TIME,
    },
]