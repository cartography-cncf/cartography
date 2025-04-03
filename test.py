from dynaconf import Dynaconf


settings = Dynaconf(
    includes=['settings.toml'],
    load_dotenv=True,
    envvar_prefix="CARTOGRAPHY",
)


settings.update({
    'aws': {
        'access_key': 'foo',
        'secret_key': 'bar',
        'region': 'eu',
    }
})
