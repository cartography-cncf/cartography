TEST_ECR_IMAGE_DIGEST = (
    "sha256:ecr0000000000000000000000000000000000000000000000000000000000000"
)
TEST_GITLAB_IMAGE_DIGEST = (
    "sha256:gl00000000000000000000000000000000000000000000000000000000000000"
)
TEST_UPDATE_TAG = 123456789

MOCK_ECR_RECOMMENDATION_RAW = """
  Target   │  registry.example.test/example/app:1.2.3
    digest │  ecr000000000000

## Recommended fixes

  Base image is  node:25-alpine

  Name            │  25-alpine
  Digest          │  sha256:e75468deb6a0d82fc49a7c566d016862dbdb9bd90e7ef31aee95c547c8e591ef
  Vulnerabilities │    0C     6H     2M     1L
  Pushed          │ 4 weeks ago
  Size            │ 59 MB
  Packages        │ 184
  Flavor          │ alpine
  OS              │ 3.23
  Runtime         │ 22

  │ The base image is also available under the supported tag(s) `25-alpine3.23`, `alpine`, `alpine3.23`, `current-alpine`, `current-alpine3.23`. If you want to display recommendations specifically for a different tag, please re-run the command using the `--tag` flag.

Refresh base image
  Rebuild the image using a newer base image version. Updating this may result in breaking changes.

            Tag            │                        Details                        │   Pushed   │       Vulnerabilities
───────────────────────────┼───────────────────────────────────────────────────────┼────────────┼──────────────────────────────
   25-alpine               │ Benefits:                                             │ 2 days ago │    0C     4H     2M     1L
  Newer image for same tag │ • Same OS detected                                    │            │           -2
  Also known as:           │ • Minor runtime version update                        │            │
  • 25.8.1-alpine          │ • Newer image for same tag                            │            │
  • 25.8.1-alpine3.23      │ • Image contains 9 fewer packages                     │            │
  • 25.8-alpine            │ • Tag was pushed more recently                        │            │
  • 25.8-alpine3.23        │ • Image has similar size                              │            │
  • 25-alpine3.23          │ • Image introduces no new vulnerability but removes 2 │            │
                           │                                                       │            │
                           │ Image details:                                        │            │
                           │ • Size: 60 MB                                         │            │
                           │ • Flavor: alpine                                      │            │
                           │ • OS: 3.23                                            │            │
                           │ • Runtime: 25.8.1                                     │            │

Change base image
  The list displays new recommended tags in descending order, where the top results are rated as most suitable.

                          Tag                         │                        Details                        │   Pushed    │       Vulnerabilities
──────────────────────────────────────────────────────┼───────────────────────────────────────────────────────┼─────────────┼──────────────────────────────
   current-alpine3.23                                 │ Benefits:                                             │ 1 week ago  │    0C     4H     2M     1L
  Image introduces no new vulnerability but removes 2 │ • Same OS detected                                    │             │           -2
  Also known as:                                      │ • Image contains 9 fewer packages                     │             │
  • alpine3.23                                        │ • Tag was pushed more recently                        │             │
                                                      │ • Image has similar size                              │             │
                                                      │ • Image introduces no new vulnerability but removes 2 │             │
                                                      │                                                       │             │
                                                      │ Image details:                                        │             │
                                                      │ • Size: 60 MB                                         │             │
                                                      │ • Flavor: alpine                                      │             │
                                                      │ • OS: 3.23                                            │             │
                                                      │ • Runtime: 22                                         │             │
   current-alpine                                     │ Benefits:                                             │ 2 weeks ago │    0C     4H     2M     1L
  Image introduces no new vulnerability but removes 2 │ • Same OS detected                                    │             │           -2
                                                      │ • Image contains 10 fewer packages                    │             │
                                                      │ • Tag was pushed more recently                        │             │
                                                      │ • Image has similar size                              │             │
                                                      │ • Image introduces no new vulnerability but removes 2 │             │
                                                      │ • current-alpine was pulled 21K times last month      │             │
                                                      │                                                       │             │
                                                      │ Image details:                                        │             │
                                                      │ • Size: 60 MB                                         │             │
                                                      │ • Flavor: alpine                                      │             │
                                                      │ • Runtime: 22                                         │             │
   slim                                               │ Benefits:                                             │ 2 days ago  │    0C     4H     1M    10L
  Tag is preferred tag                                │ • Tag is preferred tag                                │             │           -2     -1     +9
  Also known as:                                      │ • Tag was pushed more recently                        │             │
  • 25.8.1-slim                                       │ • Tag is using slim variant                           │             │
  • 25.8-slim                                         │ • slim was pulled 17K times last month                │             │
  • current-slim                                      │                                                       │             │
  • 25-slim                                           │ Image details:                                        │             │
  • bookworm-slim                                     │ • Size: 79 MB                                         │             │
  • 25-bookworm-slim                                  │ • Runtime: 22                                         │             │
  • 25.8-bookworm-slim                                │                                                       │             │
  • 25.8.1-bookworm-slim                              │                                                       │             │
  • current-bookworm-slim                             │                                                       │             │
"""

MOCK_GITLAB_RECOMMENDATION_RAW = MOCK_ECR_RECOMMENDATION_RAW.replace(
    "ecr000000000000",
    "gl00000000000000",
)
