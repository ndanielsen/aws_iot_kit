
from boto3.session import Session


def _get_iot_session(region, profile_name):
    if profile_name is None:
        return Session(region_name=region).client("iot")

    return Session(region_name=region, profile_name=profile_name).client("iot")