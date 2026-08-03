ANTHROPIC_SKILLS = [
    {
        "id": "skill_01Mv4Zq7Nr2Ks8Ld3Tp6Wx9B",
        "type": "skill",
        "display_title": "Reactor Runbook",
        "source": "custom",
        "latest_version": "1738240000000000",
        "created_at": "2025-01-30T12:00:00.000000Z",
        "updated_at": "2025-01-30T12:00:00.000000Z",
    },
    {
        "id": "skill_02Hb5Yn8Pq3Jt7Mc4Rd1Vz6A",
        "type": "skill",
        "display_title": "pptx",
        "source": "anthropic",
        "latest_version": "1730000000000000",
        "created_at": "2024-10-27T00:00:00.000000Z",
        "updated_at": "2024-10-27T00:00:00.000000Z",
    },
]

# Keyed by skill id, as returned by GET /skills/{id}/versions
ANTHROPIC_SKILL_VERSIONS = {
    "skill_01Mv4Zq7Nr2Ks8Ld3Tp6Wx9B": [
        {
            "id": "skillver_01Qt9Wr4Ym6Nb2Kd8Lp3Xc7F",
            "type": "skill_version",
            "name": "reactor-runbook",
            "description": "Emergency procedures for the Springfield reactor.",
            "directory": "skills/reactor-runbook",
            "version": "1738240000000000",
            "created_at": "2025-01-30T12:00:00.000000Z",
        },
    ],
    "skill_02Hb5Yn8Pq3Jt7Mc4Rd1Vz6A": [],
}
