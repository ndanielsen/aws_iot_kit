
import uuid

from pathlib import Path

from dateutil.parser import parse
import yaml

from .utils import _get_iot_session, _get_session, _get_endpoint, _create_and_attach_policy, write_file

CONFIG_FILE = "aws-iot.yaml"
DEFAULT_CERTS_FOLDER = ".thing-certs/"


class Storage:
  """
  Handles the indexing and storage of IoT artifacts
  """

  def __init__(self, service=None, certs_path=None, things=None, **kwargs):
    self.service = service
    self.certs_path = certs_path
    self.things = things or {}

  @staticmethod
  def create(aws_profile, region_name, folder_name, iot_endpoint, config_file=CONFIG_FILE, provider='aws'):

    Path(folder_name).mkdir(exist_ok=True)

    service = {
        "provider": provider,
        "profile_name": aws_profile,
        "region": region_name,
        "iot_endpoint": iot_endpoint["endpointAddress"],
    }

    config = {"certs_path": folder_name, "service": service}

    with open(config_file, "w") as f:
        yaml.dump(config, f)
    
    return Storage(**config)

  @staticmethod
  def read(config_file=CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        return Storage(**config)

  def commit(self):
      config = {
        'service': self.service,
        'things': self.things,
        'certs_path': self.certs_path
      }
      with open(CONFIG_FILE, "w") as f:
          data = yaml.dump(config, f)


  def record(self, thing, commit=False):

    self.things[thing.thing_name] = thing.data

    thing_path_base = f"{self.certs_path}/{thing.thing_name}"
    Path(thing_path_base).mkdir(exist_ok=True)

    certname = f"{thing_path_base}/{thing.thing_name}.pem"
    public_key_file = f"{thing_path_base}/{thing.thing_name}.pub"
    private_key_file = f"{thing_path_base}/{thing.thing_name}.prv"

    write_file(certname, thing.keys_cert["certificatePem"])
    write_file(public_key_file, thing.keys_cert["keyPair"]["PublicKey"])
    write_file(private_key_file, thing.keys_cert["keyPair"]["PrivateKey"])

    if commit:
      self.commit()


class Config:

  def __init__(self, storage=None, **kwargs):
    self.storage = storage

  @property
  def things(self):
    return self.storage.things

  @property
  def service(self):
    return self.storage.service

  @staticmethod
  def init(aws_profile, folder_name):
    client = _get_session(aws_profile)
    iot_endpoint = _get_endpoint(client)
    storage = Storage.create(aws_profile, client.region_name, folder_name, iot_endpoint)
    return Config(storage=storage)

  @staticmethod
  def load():
    storage = Storage.read()
    return Config(storage=storage)

  def create_things(self, count=1):
      """
      Create and activate a specified number of Things in the AWS IoT Service.
      """
      for _ in range(count):
          thing = Thing.create(self.service, self.storage)

      print(f"Created {count}")

 

class Thing:

  def __init__(self, thing_name=None, prefix=None, service=None):
    self.thing_name = thing_name or str(uuid.uuid4())
    self.service = service

    self.data = {}
    self.keys_cert = {}


    @staticmethod
    def create():
      pass

    @staticmethod
    def load(thing_name):
      return Thing()

  def __str__(self):
    return self.thing_name

  @staticmethod
  def create(service, storage, thing_name=None, prefix=None, commit=True):

      thing = Thing(thing_name=thing_name, prefix=prefix)
      thing._provision(service)

      storage.record(thing, commit=commit)

      return thing


  def _provision(self, service):

      if service['provider'] == 'aws':
        iot_session = _get_iot_session(service['region'], service['profile_name'])
        self.keys_cert = iot_session.create_keys_and_certificate(setAsActive=True)
        iot_session.create_thing(thingName=self.thing_name)
        iot_session.attach_thing_principal(
            thingName=self.thing_name, principal=self.keys_cert["certificateArn"]
        )
        policy_data = _create_and_attach_policy(
            self.thing_name, self.keys_cert["certificateArn"], iot_session, service['region']
        )
        self.service = service
        self.data =  {
          "certificateArn": self.keys_cert["certificateArn"],
          "certificateId": self.keys_cert["certificateId"],
          "createDateTime": parse(self.keys_cert["ResponseMetadata"]["HTTPHeaders"]["date"]),
          "policyName": policy_data["policyName"],
          "policyArn": policy_data["policyArn"],
          }
      else:
        raise NotImplementedError("Only AWS has been implemented")

  # def _delete_thing_cloud(self):
  #   pass




  # def delete(self, scope):

  #   if scope == "cloud":
  #       self._delete_thing_cloud(thing_id, cert_details, iot_session)

  #         delete_thing_files(thing_id, config)

  #     config["things"] = {}
  #     update_config(config)




def send_messages(cli):
    """
    Send messages through the AWS IoT service from the previously created
    number of Things.
    """


    # setup Things and ElfPoster threads
    i = 0
    ep_list = list()
    for t in things:
        thing_name = thing_name_template.format(i)
        thing = t[thing_name]
        ep = ElfPoster(thing_name, cli, thing, cfg)

        things[i][thing_name][policy_name_key] = ep.policy_name
        things[i][thing_name][policy_arn_key] = ep.policy_arn

        ep_list.append(ep)
        ep.start()
        i += 1

    _update_things_config(things)

    # wait for all the ElfPoster threads to finish their post_duration
    for ep in ep_list:
        ep.join()

    # Now disconnect the MQTT Client
    for ep in ep_list:
        ep.mqttc.disconnect()
