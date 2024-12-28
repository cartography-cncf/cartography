from setuptools import find_packages
from setuptools import setup

__version__ = '0.97.1'


setup(
    name='cartography',
    version=__version__,
    description='Explore assets and their relationships across your technical infrastructure.',
    long_description='file: README.md',
    long_description_content_type='text/markdown',
    url='https://www.github.com/cartography-cncf/cartography',
    maintainer='Cartography Contributors',
    license='apache2',
    packages=find_packages(exclude=['tests*']),
    package_data={
        'cartography': ['py.typed'],
        'cartography.data': [
            '*.cypher',
            '*.yaml',
        ],
        'cartography.data.jobs.analysis': [
            '*.json',
        ],
        'cartography.data.jobs.scoped_analysis': [
            '*.json',
        ],
        'cartography.data.jobs.cleanup': [
            '*.json',
        ],
    },
    dependency_links=[],
    install_requires=[
        "backoff>=2.1.2",
        "boto3>=1.15.1",
        "botocore>=1.18.1",
        "dnspython>=1.15.0",
        "neo4j>=4.4.4,<5.0.0",
        "policyuniverse>=1.1.0.0",
        "google-api-python-client>=1.7.8",
        "oauth2client>=4.1.3",
        "marshmallow>=3.0.0rc7",
        "oci>=2.71.0",
        "okta<1.0.0",
        "pyyaml>=5.3.1",
        "requests>=2.22.0",
        "statsd",
        "packaging",
        "python-digitalocean>=1.16.0",
        "adal>=1.2.4",
        "azure-cli-core>=2.26.0",
        "azure-mgmt-compute>=5.0.0",
        "azure-mgmt-resource>=10.2.0",
        "azure-mgmt-cosmosdb>=6.0.0",
        "msrestazure >= 0.6.4",
        "azure-mgmt-storage>=16.0.0",
        "azure-mgmt-sql<=1.0.0",
        "azure-identity>=1.5.0",
        "kubernetes>=22.6.0",
        "pdpyras>=4.3.0",
        "crowdstrike-falconpy>=0.5.1",
        "python-dateutil",
        "xmltodict",
        "duo-client",
    ],
    extras_require={
        ':python_version<"3.7"': [
            "importlib-resources",
        ],
    },
    entry_points={
        'console_scripts': [
            'cartography = cartography.cli:main',
            'cartography-detectdrift = cartography.driftdetect.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Topic :: Security',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
