import os
from dotenv import load_dotenv
from logging import getLogger

logger = getLogger(__name__)


class CartographyConfigException(Exception):
    pass

class Config:
    ENV_PREFIX = 'CARTOGRAPHY_'
    ENABLE_ENV_VARS = True
    ENABLE_DOTENV = True

    def __init__(self, **kwargs):
        # Set attributes from kwargs
        for k, v in kwargs.items():
            setattr(self, k, v)
        # Override with .env file
        if self.ENABLE_DOTENV:
            load_dotenv()
        # Override with environment variables
        if self.ENABLE_ENV_VARS:
            for k, v in os.environ.items():
                if k.startswith(self.ENV_PREFIX):
                    setattr(self, k[len(self.ENV_PREFIX):].lower(), v)

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        raise CartographyConfigException(f"Configuration attribute {name} not found")


import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--foo", type=str, default="bar")
args = parser.parse_args()

# TEST
os.environ['CARTOGRAPHY_TEST'] = 'test'
config = Config(**vars(args))
print(config.test)
print(config.foo)
print(config.baz)

