
import uuid

from utils import _get_iot_session



class Thing:

  def __init__(self, thing_id=None, region=None, profile_name=None, iot_session=None)
    self.thing_id = thing_id or str(uuid.uuid4())
    self.iot_session = iot_session or _get_iot_session(region, profile_name)
    self.region = region

    self.certs = {}

    @staticmethod
    def create(self):
      pass


    def _create(self):
      pass


    def delete(self, scope):
      'scope: local or cloud'
      pass


class Config:

  def __init__(self):
    pass

  