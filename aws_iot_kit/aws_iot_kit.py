"""Main module."""

import uuid
from pathlib import Path

from config import load_config, update_config
from boto3.session import Session

from dateutil.parser import parse


def _get_iot_session(region, profile_name):
    if profile_name is None:
        return Session(region_name=region).client("iot")

    return Session(region_name=region, profile_name=profile_name).client("iot")


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


def _write_certs(thing_id, keys_cert):
    config = load_config()

    certs_folder = config["certs_folder"]
    thing_path_base = f"{certs_folder}/{thing_id}/{thing_id}"

    try:
        certname = f"{thing_path_base}.pem"
        public_key_file = f"{thing_path_base}.pub"
        private_key_file = f"{thing_path_base}.prv"
        with open(certname, "w") as pem_file:
            pem = keys_cert["certificatePem"]
            pem_file.write(pem)

        with open(public_key_file, "w") as pub_file:
            pub = keys_cert["keyPair"]["PublicKey"]
            pub_file.write(pub)

        with open(private_key_file, "w") as prv_file:
            prv = keys_cert["keyPair"]["PrivateKey"]
            prv_file.write(prv)

    except OSError as ose:
        log.error("OSError while writing an ELF file. {0}".format(ose))


def extract_meta(data):
    return {
        "certificateArn": data["certificateArn"],
        "certificateId": data["certificateId"],
        "createDateTime": parse(data["ResponseMetadata"]["HTTPHeaders"]["date"]),
    }


def create_things(count=1):
    """
    Create and activate a specified number of Things in the AWS IoT Service.
    """
    config = load_config()
    region = config["aws"]["region"]
    profile_name = config["aws"]["profile_name"]
    iot = _get_iot_session(region, profile_name)

    for thing in range(count):
        thing_id = str(uuid.uuid4())

        _mkdir_thing(thing_id, config["certs_folder"])
        keys_cert = iot.create_keys_and_certificate(setAsActive=True)
        iot.create_thing(thingName=thing_id)
        iot.attach_thing_principal(
            thingName=thing_id, principal=keys_cert["certificateArn"]
        )
        _write_certs(thing_id, keys_cert)
        meta = extract_meta(keys_cert)
        _update_config(thing_id, meta)
    print(f"Created {count}")


if __name__ == "__main__":
    config = load_config()

    print(create_things(1))
