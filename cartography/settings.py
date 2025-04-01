import warnings

from dynaconf import Dynaconf


settings = Dynaconf(
    includes=['settings.toml'],
    load_dotenv=True,
    envvar_prefix="CARTOGRAPHY",
)


def decrecated_config(argument_name: str, env_name: str):
    """ Helper to deprecate a config argument in favor of an environment variable """
    msg = f"The '{argument_name}' parameter is deprecated" \
        f"use '{env_name}' varenv instead (or define it in settings.toml)"
    warnings.warn(msg, DeprecationWarning, stacklevel=2)
