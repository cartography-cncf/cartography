SECRETS_FINDING_ID = "691234"
SECRETS_RESPONSE = {
    "findings": [
        {
            "id": SECRETS_FINDING_ID,
            "confidence": "CONFIDENCE_HIGH",
            "severity": "SEVERITY_HIGH",
            "status": "FINDING_STATUS_OPEN",
            "validationState": "VALIDATION_STATE_CONFIRMED_VALID",
            "type": "OpenAI",
            "findingPath": "src/ai.py:232",
            "findingPathUrl": "https://github.com/simpsoncorp/sample_repo/blob/6ad16b240d4b6ae5bd6e326dd71053c21344e311/src/ai.py#L232",
            "ref": "main",
            "refUrl": "https://github.com/simpsoncorp/sample_repo/tree/main",
            "mode": "MODE_MONITOR",
            "ruleHashId": "lBU41LA",
            "createdAt": "2024-06-17T17:23:01.901204Z",
            "updatedAt": "2024-06-20T17:33:00.669343Z",
            "repository": {
                "name": "simpsoncorp/sample_repo",
                "url": "https://github.com/simpsoncorp/sample_repo",
                "visibility": "REPOSITORY_VISIBILITY_PRIVATE",
                "scmType": "SCM_TYPE_GITHUB",
            },
        },
    ],
    "cursor": "",
}
RAW_SECRETS = SECRETS_RESPONSE["findings"]
