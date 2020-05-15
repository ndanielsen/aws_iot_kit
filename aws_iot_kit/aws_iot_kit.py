"""Main module."""

import uuid
import json
import time
import pathlib
from pathlib import Path

from aws_iot_kit.config import load_config, update_config
from boto3.session import Session
from botocore.exceptions import ClientError

from dateutil.parser import parse

from aws_iot_kit.utils import _get_iot_session


def _mkdir_thing(thing, certs_folder):
    Path(f"{certs_folder}/{thing}").mkdir(exist_ok=True)


def _update_config(thing_id, meta={}):
    config = load_config()
    things = config.get("things")

    if not things:
        config["things"] = {}
        things = config["things"]

    if things.get(thing_id):
        things[thing_id] = thing["thing_id"].update(meta)
    else:
        things[thing_id] = meta

    update_config(config)


def _determine_file_paths(thing_id, certs_folder):
    thing_path_base = f"{certs_folder}/{thing_id}"
    return dict(
        thing_path_base=thing_path_base,
        certname=f"{thing_path_base}/{thing_id}.pem",
        public_key_file=f"{thing_path_base}/{thing_id}.pub",
        private_key_file=f"{thing_path_base}/{thing_id}.prv",
    )


def delete_thing_files(thing_id, config):
    paths = _determine_file_paths(thing_id, config["certs_folder"])
    for key, file_path in paths.items():
        if key == "thing_path_base":
            continue
        file_path = pathlib.Path(file_path)
        file_path.unlink()  # remove file

    dir_path = pathlib.Path(paths["thing_path_base"])
    dir_path.rmdir()  # remove directory


def _write_certs(thing_id, keys_cert):
    config = load_config()

    certs_folder = config["certs_folder"]
    paths = _determine_file_paths(thing_id, certs_folder)
    try:

        with open(paths["certname"], "w") as pem_file:
            pem = keys_cert["certificatePem"]
            pem_file.write(pem)

        with open(paths["public_key_file"], "w") as pub_file:
            pub = keys_cert["keyPair"]["PublicKey"]
            pub_file.write(pub)

        with open(paths["private_key_file"], "w") as prv_file:
            prv = keys_cert["keyPair"]["PrivateKey"]
            prv_file.write(prv)

    except OSError as ose:
        log.error("OSError while writing an ELF file. {0}".format(ose))


def extract_meta(data, policy_data):

    return {
        "certificateArn": data["certificateArn"],
        "certificateId": data["certificateId"],
        "createDateTime": parse(data["ResponseMetadata"]["HTTPHeaders"]["date"]),
        "policyName": policy_data["policyName"],
        "policyArn": policy_data["policyArn"],
    }


def _create_and_attach_policy(thing_id, thing_cert_arn, iot_session, region_name):
    # Create and attach to the principal/certificate the minimal action
    # privileges Thing policy that allows publish and subscribe
    tp = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    # "iot:*"
                    "iot:Connect",
                    "iot:Publish",
                    "iot:Receive",
                    "iot:Subscribe",
                ],
                "Resource": ["arn:aws:iot:{0}:*:*".format(region_name)],
            }
        ],
    }

    policy_name = "policy-{0}".format(thing_id)
    policy = json.dumps(tp)
    p = iot_session.create_policy(policyName=policy_name, policyDocument=policy)

    iot_session.attach_principal_policy(
        policyName=policy_name, principal=thing_cert_arn
    )

    return dict(policyName=p["policyName"], policyArn=p["policyArn"])


def create_things(count=1):
    """
    Create and activate a specified number of Things in the AWS IoT Service.
    """
    config = load_config()
    region_name = config["aws"]["region"]
    profile_name = config["aws"]["profile_name"]
    iot_session = _get_iot_session(region_name, profile_name)

    for thing in range(count):
        thing_id = str(uuid.uuid4())

        _mkdir_thing(thing_id, config["certs_folder"])
        keys_cert = iot_session.create_keys_and_certificate(setAsActive=True)
        iot_session.create_thing(thingName=thing_id)
        iot_session.attach_thing_principal(
            thingName=thing_id, principal=keys_cert["certificateArn"]
        )
        policy_data = _create_and_attach_policy(
            thing_id, keys_cert["certificateArn"], iot_session, region_name
        )

        _write_certs(thing_id, keys_cert)
        meta = extract_meta(keys_cert, policy_data)
        _update_config(thing_id, meta)
    print(f"Created {count}")


def delete_thing_cloud(thing_id, cert_details, iot_session):
    policy_name_key = "policyName"
    if policy_name_key in cert_details:
        try:
            iot_session.detach_principal_policy(
                policyName=cert_details[policy_name_key],
                principal=cert_details["certificateArn"],
            )
            iot_session.delete_policy(policyName=cert_details[policy_name_key])
        except ClientError as ce:
            print(ce)

    try:

        iot_session.update_certificate(
            certificateId=cert_details["certificateId"], newStatus="INACTIVE"
        )
        iot_session.detach_thing_principal(
            thingName=thing_id, principal=cert_details["certificateArn"]
        )
        time.sleep(1)

        iot_session.delete_certificate(certificateId=cert_details["certificateId"])

    except ClientError as ce:
        print(ce)

    iot_session.delete_thing(thingName=thing_id)
    print(f"Removed: {thing_id}")


def delete_things(clean_type):
    """
    Clean up all Things previously created in the AWS IoT Service and files
    stored locally.
    """
    config = load_config()

    things = config.get("things")
    if not things:
        print("No things locally")
        return

    region = config["aws"]["region"]
    profile_name = config["aws"]["profile_name"]
    iot_session = _get_iot_session(region, profile_name)

    for thing_id, cert_details in things.items():

        if clean_type == "cloud":
            delete_thing_cloud(thing_id, cert_details, iot_session)

        delete_thing_files(thing_id, config)

    config["things"] = {}
    update_config(config)
