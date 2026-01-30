from digitalocean import Project

PROJECTS_RESPONSE = [
    Project(
        id="project_1",
        name="project_1_awesome",
        owner_uuid="12345-12345-12345-12345",
        description="my awesome project",
        is_default=True,
        created_at="2021-03-03T21:29:35Z",
        updated_at="2021-03-04T21:29:35Z",
    ),
]

PROJECT_RESOURCES_RESPONSE = [
    "do:droplet:12345678",
]
