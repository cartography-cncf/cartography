### Type of change
<!-- Mark the relevant option with an "x" -->
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Refactoring (no functional changes)
- [ ] Documentation update
- [ ] Other (please describe):


### Summary
<!-- Describe WHAT your changes do and WHY they are needed. -->



### Related issues or links
<!-- Include links to relevant issues or other pages. Use "Fixes #123" or "Closes #123" to auto-close issues. -->

- Fixes #


### Breaking changes
<!-- If this PR introduces breaking changes, describe the impact and migration path. Otherwise, delete this section. -->



### How was this tested?
<!-- Describe how you tested your changes. Include relevant details such as test configuration, commands run, or manual testing steps. -->



### Checklist

#### General
- [ ] I have read the [contributing guidelines](https://cartography-cncf.github.io/cartography/dev/developer-guide.html).
- [ ] The linter passes locally (`make lint`).
- [ ] I have added/updated tests that prove my fix is effective or my feature works.

#### Proof of functionality
<!-- Provide at least one of the following to help reviewers verify your changes: -->
- [ ] Screenshot showing the graph before and after changes.
- [ ] New or updated unit/integration tests.

#### If you are adding or modifying a synced entity
- [ ] Included Cartography sync logs from a real environment demonstrating successful synchronization of the new/modified entity. Logs should show:
  - The sync job starting and completing without errors
  - The number of nodes/relationships created or updated
  - Example:
    ```
    INFO:cartography.intel.aws.ec2:Loading 42 EC2 instances for region us-east-1
    INFO:cartography.intel.aws.ec2:Synced EC2 instances in 3.21 seconds
    ```

#### If you are changing a node or relationship
- [ ] Updated the [schema documentation](https://github.com/cartography-cncf/cartography/tree/master/docs/root/modules).
- [ ] Updated the [schema README](https://github.com/cartography-cncf/cartography/blob/master/docs/schema/README.md).

#### If you are implementing a new intel module
- [ ] Used the NodeSchema [data model](https://cartography-cncf.github.io/cartography/dev/writing-intel-modules.html#defining-a-node).


### Notes for reviewers
<!-- Optional: Add any context that would help reviewers, such as areas to focus on, design decisions, or open questions. -->
