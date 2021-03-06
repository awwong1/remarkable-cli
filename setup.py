from setuptools import setup, find_packages
from remarkable_cli import __version__


setup(
    name="remarkable-cli",
    version=__version__,
    author="Alexander Wong",
    author_email="alex@udia.ca",
    description="An unofficial CLI for interacting with the Remarkable tablet.",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/awwong1/remarkable-cli",
    license="Apache-2.0",
    packages=find_packages(),
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Environment :: Console",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Topic :: Utilities",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
    ],
    entry_points={"console_scripts": ["remarkable-cli=remarkable_cli:main"]},
    install_requires=["paramiko"],
)
