import logging
import warnings
from typing import List

from dynaconf import Dynaconf

logger = logging.getLogger(__name__)


settings = Dynaconf(
    includes=['settings.toml'],
    load_dotenv=True,
    envvar_prefix="CARTOGRAPHY",
)


def check_module_settings(module_name: str, required_settings: List[str]) -> bool:
    """
    Check if the required settings for a module are set in the configuration.

    Args:
        module_name (str): The name of the module.
        required_settings (List[str]): A list of required settings for the module.

    Returns:
        bool: True if all required settings are present, False otherwise.
    """
    module_settings = settings.get(module_name.upper(), None)
    if module_settings is None:
        logger.info('%s import is not configured - skipping this module. See docs to configure.', module_name)
        return False
    missing_settings = [setting for setting in required_settings if not settings.get(setting)]
    if missing_settings:
        logger.warning(
            '%s import is not configured - skipping this module. Missing settings: %s',
            module_name, ", ".join(missing_settings),
        )
        return False
    return True


def decrecated_config(argument_name: str, env_name: str):
    """ Helper to deprecate a config argument in favor of an environment variable """
    msg = f"The '{argument_name}' parameter is deprecated" \
        f"use '{env_name}' varenv instead (or define it in settings.toml)"
    warnings.warn(msg, DeprecationWarning, stacklevel=2)
