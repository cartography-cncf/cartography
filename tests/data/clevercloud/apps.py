CLEVERCLOUD_APPS = [
    {
        "id": "app_6cb7fded-72d8-4994-b813-c7caa2208019",
        "name": "dummy-api-production",
        "description": "dummy-api-production",
        "zone": "par",
        "instance": {
            "type": "java",
            "version": "20221027",
            "variant": {
              "id": "5163834d-b343-4006-bfdb-ece9d30fbb51",
              "slug": "gradle",
              "name": "Java or Groovy + Gradle",
              "deployType": "java",
              "logo": "https://assets.clever-cloud.com/logos/gradle.svg",
            },
            "minInstances": 2,
            "maxInstances": 2,
            "maxAllowedInstances": 40,
            "minFlavor": {
                "name": "XS",
                "mem": 1024,
                "cpus": 1,
                "gpus": 0,
                "disk": 0,
                "price": 0.3436,
                "available": True,
                "microservice": False,
                "machine_learning": False,
                "nice": 0,
                "price_id": "apps.XS",
                "memory": {
                    "unit": "B",
                    "value": 1073741824,
                    "formatted": "1024 MiB",
                },
            },
            "maxFlavor": {
                "name": "XS",
                "mem": 1024,
                "cpus": 1,
                "gpus": 0,
                "disk": 0,
                "price": 0.3436,
                "available": True,
                "microservice": False,
                "machine_learning": False,
                "nice": 0,
                "price_id": "apps.XS",
                "memory": {
                    "unit": "B",
                    "value": 1073741824,
                    "formatted": "1024 MiB",
                },
            },
            "flavors": [
                {
                    "name": "pico",
                    "mem": 256,
                    "cpus": 1,
                    "gpus": 0,
                    "disk": 0,
                    "price": 0.1073883162,
                    "available": True,
                    "microservice": True,
                    "machine_learning": False,
                    "nice": 5,
                    "price_id": "apps.pico",
                    "memory": {
                        "unit": "B",
                        "value": 268435456,
                        "formatted": "256 MiB",
                    },
                },
                {
                    "name": "nano",
                    "mem": 512,
                    "cpus": 1,
                    "gpus": 0,
                    "disk": 0,
                    "price": 0.1431844215,
                    "available": True,
                    "microservice": True,
                    "machine_learning": False,
                    "nice": 5,
                    "price_id": "apps.nano",
                    "memory": {
                        "unit": "B",
                        "value": 536870912,
                        "formatted": "512 MiB",
                    },
                },
                {
                    "name": "XS",
                    "mem": 1024,
                    "cpus": 1,
                    "gpus": 0,
                    "disk": 0,
                    "price": 0.3436,
                    "available": True,
                    "microservice": False,
                    "machine_learning": False,
                    "nice": 0,
                    "price_id": "apps.XS",
                    "memory": {
                        "unit": "B",
                        "value": 1073741824,
                        "formatted": "1024 MiB",
                    },
                },
                {
                    "name": "S",
                    "mem": 2048,
                    "cpus": 2,
                    "gpus": 0,
                    "disk": 0,
                    "price": 0.6873,
                    "available": True,
                    "microservice": False,
                    "machine_learning": False,
                    "nice": 0,
                    "price_id": "apps.S",
                    "memory": {
                        "unit": "B",
                        "value": 2147483648,
                        "formatted": "2048 MiB",
                    },
                },
                {
                    "name": "M",
                    "mem": 4096,
                    "cpus": 4,
                    "gpus": 0,
                    "disk": 0,
                    "price": 1.7182,
                    "available": True,
                    "microservice": False,
                    "machine_learning": False,
                    "nice": 0,
                    "price_id": "apps.M",
                    "memory": {
                        "unit": "B",
                        "value": 4294967296,
                        "formatted": "4096 MiB",
                    },
                },
                {
                    "name": "L",
                    "mem": 8192,
                    "cpus": 6,
                    "gpus": 0,
                    "disk": 0,
                    "price": 3.4364,
                    "available": True,
                    "microservice": False,
                    "machine_learning": False,
                    "nice": 0,
                    "price_id": "apps.L",
                    "memory": {
                        "unit": "B",
                        "value": 8589934592,
                        "formatted": "8192 MiB",
                    },
                },
                {
                    "name": "XL",
                    "mem": 16384,
                    "cpus": 8,
                    "gpus": 0,
                    "disk": 0,
                    "price": 6.8729,
                    "available": True,
                    "microservice": False,
                    "machine_learning": False,
                    "nice": 0,
                    "price_id": "apps.XL",
                    "memory": {
                        "unit": "B",
                        "value": 17179869184,
                        "formatted": "16384 MiB",
                    },
                },
                {
                    "name": "2XL",
                    "mem": 24576,
                    "cpus": 12,
                    "gpus": 0,
                    "disk": 0,
                    "price": 13.7458,
                    "available": True,
                    "microservice": False,
                    "machine_learning": False,
                    "nice": 0,
                    "price_id": "apps.2XL",
                    "memory": {
                        "unit": "B",
                        "value": 25769803776,
                        "formatted": "24576 MiB",
                    },
                },
                {
                    "name": "3XL",
                    "mem": 32768,
                    "cpus": 16,
                    "gpus": 0,
                    "disk": 0,
                    "price": 27.4915,
                    "available": True,
                    "microservice": False,
                    "machine_learning": False,
                    "nice": 0,
                    "price_id": "apps.3XL",
                    "memory": {
                        "unit": "B",
                        "value": 34359738368,
                        "formatted": "32768 MiB",
                    },
                },
            ],
            "defaultEnv": {
                "CC_JAVA_VERSION": "11",
            },
            "lifetime": "REGULAR",
            "instanceAndVersion": "java-20221027",
        },
        "deployment": {
            "shutdownable": False,
            "type": "GIT",
            "repoState": "CREATED",
        },
        "vhosts": [
            {
                "fqdn": "google.com",
            },
        ],
        "creationDate": 1647960575254,
        "last_deploy": 80,
        "archived": False,
        "stickySessions": False,
        "homogeneous": False,
        "favourite": False,
        "cancelOnPush": True,
        "webhookUrl": None,
        "webhookSecret": None,
        "separateBuild": True,
        "buildFlavor": {
            "name": "XL",
            "mem": 16384,
            "cpus": 8,
            "gpus": 0,
            "disk": None,
            "price": 6.8729,
            "available": True,
            "microservice": False,
            "machine_learning": False,
            "nice": 0,
            "price_id": "apps.XL",
            "memory": {
                "unit": "B",
                "value": 17179869184,
                "formatted": "16384 MiB",
            },
        },
        "ownerId": "orga_f3b3bb57-db31-4dff-8708-0dd91cc31826",
        "state": "SHOULD_BE_UP",
        "commitId": "a8e599c7067e126ddd1885d6eee9be5aebd8a99e",
        "appliance": None,
        "branch": "master",
        "forceHttps": "DISABLED",
        "addons": [
            "addon_f9deff34-d8cc-4bfb-995b-c1d0db37067c",
        ],
    },
]
