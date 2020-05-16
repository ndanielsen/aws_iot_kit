import json


from boto3.session import Session


def write_file(filename, value):
    with open(filename, "w") as f:
        f.write(value)


def _get_iot_session(region, profile_name):
    if profile_name is None:
        return Session(region_name=region).client("iot")

    return Session(region_name=region, profile_name=profile_name).client("iot")


def _get_session(aws_profile):
    session = Session(profile_name=aws_profile)
    return session


def _get_endpoint(client):
    client = client.client("iot")
    return client.describe_endpoint(endpointType="iot:Data-ATS")


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

