from setuptools import setup, find_packages


ORKO_VERSION = "0.0.0"
ORKO_URL = "https://github.com/johnboxall/orko/"
ORKO_DOWNLOAD_URL = (ORKO_URL + "tarball/" + ORKO_VERSION)

setup(
    name="orko",
    version=ORKO_VERSION,
    description="Analyzer for GitHub Pull Request metadata.",
    long_description=open('README.md').read(),
    packages=find_packages(),
    author="John Boxall",
    author_email="john@mobify.com",
    url=ORKO_URL,
    license="MIT",
    install_requires=open("requirements.pip").read(),
    entry_points={
        'console_scripts': [
            'orko = orko.cli:main',
        ],
    },
)