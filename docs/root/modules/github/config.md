## Github Configuration

Follow these steps to analyze GitHub repos and other objects with Cartography.

1. Prepare your GitHub credentials.

    1. Make a GitHub user. Prepare a token on that user with the following scopes at minimum: `repo`, `read:org`, `read:user`, `user:email`

    1. GitHub ingest supports multiple endpoints, such as a public instance and an enterprise instance by taking a base64-encoded config object structured as

        ```python
        data = {
          "organization": [
            {
              "token": "faketoken",
              "url": "https://api.github.com/graphql",
              "name": "fakeorg",
            },
            {
              "token": "stillfake",
              "url": "https://github.example.com/api/graphql",
              "name": "fakeorg",
            }
          ]
        }
        ```

    1. For each GitHub instance you want to ingest, generate an API token as documented in the [API reference](https://developer.github.com/v3/auth/)

    1. Create your auth config as shown above using the token obtained in the previous step. If you are configuring only the public GitHub instance, you can just use the first config block and delete the second. The name field is for the organization name you want to ingest.

    1. Base64 encode the auth object. You can encode the above sample in Python using

       ```python
       import json
       import base64
       auth_json = json.dumps(data)
       base64.b64encode(auth_json.encode())
       ```

       and the resulting environment variable would be ```eyJvcmdhbml6YXRpb24iOiBbeyJ0b2tlbiI6ICJmYWtldG9rZW4iLCAidXJsIjogImh0dHBzOi8vYXBpLmdpdGh1Yi5jb20vZ3JhcGhxbCIsICJuYW1lIjogImZha2VvcmcifSwgeyJ0b2tlbiI6ICJzdGlsbGZha2UiLCAidXJsIjogImh0dHBzOi8vZ2l0aHViLmV4YW1wbGUuY29tL2FwaS9ncmFwaHFsIiwgIm5hbWUiOiAiZmFrZW9yZyJ9XX0=```

1. Populate an environment variable of your choice with the contents of the base64 output from the previous step.

1. Call the `cartography` CLI with `--github-config-env-var YOUR_ENV_VAR_HERE`.

1. `cartography` will then load your graph with data from all the organizations you specified.
