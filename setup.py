#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "Click>=7.0",
    "pyyaml>=5.3.1",
    "boto3>=1.13.9",
    "python-dateutil>=1.14.0",
]

setup_requirements = [
    "pytest-runner",
]

test_requirements = [
    "pytest>=3",
]

setup(
    author="yes",
    author_email="nathan@socialcoder.io",
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="A commandline kit to jump start your work on AWS IoT projects",
    entry_points={"console_scripts": ["aws_iot_kit=aws_iot_kit.cli:main",],},
    install_requires=requirements,
    license="Apache Software License 2.0",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="aws_iot_kit",
    name="aws_iot_kit",
    packages=find_packages(include=["aws_iot_kit", "aws_iot_kit.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/ndanielsen/aws_iot_kit",
    version="0.1.0",
    zip_safe=False,
)
