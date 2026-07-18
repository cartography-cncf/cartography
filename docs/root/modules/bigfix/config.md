## BigFix Configuration

Follow these steps to analyze BigFix objects with Cartography.

1. Prepare a read-only BigFix username and password.
1. Pass the BigFix API URL to the `--bigfix-root-url` CLI arg.
1. Pass the BigFix username to the `--bigfix-username` CLI arg.
1. Populate an environment variable with the password.
1. Pass that env var name to the `--bigfix-password-env-var` CLI arg.
