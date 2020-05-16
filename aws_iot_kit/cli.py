"""Console script for aws_iot_kit."""
import sys
import click
from pathlib import Path
import yaml

from boto3.session import Session
import boto3

from .aws_iot_kit import delete_things

from .models import Config, DEFAULT_CERTS_FOLDER


@click.command()
@click.option("--init", is_flag=True, help="Initialize AWS IoT Project")
@click.option("--create", "-c", is_flag=True, help="Create Things")
@click.option("--number", "-n", default=1, help="Specify numer of Things to create")
@click.option("--clean", "delete", flag_value="local", help="Remove local thing files")
@click.option(
    "--wipe",
    "delete",
    flag_value="cloud",
    help="Remove local thing files and Cloud instances",
)
def main(init, create, number, delete):
    """Console script for aws_iot_kit."""
    if init:
        click.echo("Init Project")
        aws_profile = click.prompt("Please enter your AWS CLI Profile Name")
        aws_region = click.prompt("Please enter AWS region", default="us-west-2")
        folder_name = click.prompt(
            "Please enter Thing Certs Folder Path", default=DEFAULT_CERTS_FOLDER
        )
        config = Config.init(aws_profile, folder_name)
        return
    config = Config.load()
    # TODO - exit if not loaded

    print(config)
    if create:
        config.create_things(count=number)
        return

    elif delete:
        delete_things(delete)
        return


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
