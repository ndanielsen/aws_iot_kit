"""Console script for aws_iot_kit."""
import sys
import click
from pathlib import Path
import yaml

from boto3.session import Session
import boto3

from aws_iot_kit import create_things

# botocore.exceptions.ProfileNotFound

DEFAULT_CERTS_FOLDER = ".thing-certs/"


def create_certs_folder(folder_name):
    Path(folder_name).mkdir(exist_ok=True)
    return folder_name


def create_config(aws_profile, region_name, folder_name, iot_endpoint):
    aws = {
        "profile_name": aws_profile,
        "region": region_name,
        "iot_endpoint": iot_endpoint["endpointAddress"],
    }

    config = {"certs_folder": folder_name, "aws": aws}

    with open("aws-iot.yaml", "w") as f:
        data = yaml.dump(config, f)


def get_session(aws_profile):
    session = Session(profile_name=aws_profile)
    return session


def get_endpoint(client):
    client = client.client("iot")
    return client.describe_endpoint(endpointType="iot:Data-ATS")


@click.command()
@click.option("--init", is_flag=True, help="Initialize AWS IoT Project")
@click.option("--create", "-c", is_flag=True, help="Create Things")
@click.option("--number", "-n", default=1, help="Specify numer of Things to create")
def main(init, create, number):
    """Console script for aws_iot_kit."""
    if init:
        click.echo("Init Project")
        aws_profile = click.prompt("Please enter your AWS CLI Profile Name")

        client = get_session(aws_profile)

        aws_region = click.prompt("Please enter AWS region", default=client.region_name)

        folder_name = click.prompt(
            "Please enter Thing Certs Folder Path", default=DEFAULT_CERTS_FOLDER
        )

        iot_endpoint = get_endpoint(client)

        folder_name = create_certs_folder(folder_name)
        create_config(aws_profile, aws_region, folder_name, iot_endpoint)
        return

    if create:
        create_things(count=number)
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
