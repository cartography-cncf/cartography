## Trivy Configuration

[Trivy](https://aquasecurity.github.io/trivy/latest/) is a vulnerability scanner that can be used to scan images for vulnerabilities.

Currently, Cartography allows you to use Trivy to scan the following resources:


| Resource name in Cartography CLI | Cartography Node label | Cloud permissions required to scan with Trivy |
|---|---|---|
| `aws.ecr` | [ECRRepositoryImage](https://cartography-cncf.github.io/cartography/modules/aws/schema.html#ecrrepositoryimage) | `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer` |


To use Trivy with Cartography, first ensure that your graph is populated with the resources that you want Trivy to scan.

You can also configure Cartography to load images and then scan them with Trivy in the same job. For example you can use the CLI to run an aws:ecr sync and then a trivy sync job like this:

```bash
cartography --selected-modules aws,trivy --aws-requested-syncs ecr --trivy-path `which trivy` --trivy-resource-type aws.ecr
```

See Cartography [CLI](https://github.com/cartography-cncf/cartography/blob/master/cartography/cli.py) docstrings for reference.

With that in mind,

1. Install Trivy
    1. Follow the [official Trivy installation guide](https://aquasecurity.github.io/trivy/latest/getting-started/installation/) for your operating system
    1. Verify the installation by running `trivy --version` in your terminal
    1. Take note of the path to your Trivy binary. You can probably get this by running `which trivy` in your terminal.

1. Configure Cartography with Trivy
    1. Ensure that the machine running Cartography has the necessary permissions to scan your desired resources. For example, if you want to scan AWS ECR images, you need to ensure that the machine running Cartography has the permissions listed in the table above.
    1. Set the path to your Trivy binary using the `--trivy-path` parameter. This should be the absolute path to the Trivy executable.
        ```bash
        cartography --trivy-path /usr/local/bin/trivy
        ```

1. Optional Configuration
    1. If you want to use [custom OPA policies](https://trivy.dev/latest/docs/configuration/filtering/#by-rego) with Trivy, specify the path to your policy file using `--trivy-opa-policy-file-path`
        ```bash
        cartography --trivy-path /usr/local/bin/trivy --trivy-opa-policy-file-path /path/to/policy.rego
        ```
    1. To scan specific resource types, use the `--trivy-resource-type` parameter. For example, to scan AWS ECR repositories:
        ```bash
        cartography --trivy-path /usr/local/bin/trivy --trivy-resource-type aws.ecr
        ```

Note: Make sure the Trivy binary has the necessary permissions to execute and access the resources you want to scan.
