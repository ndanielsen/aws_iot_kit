import uuid
import json
import threading

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient, DROP_OLDEST

AWS_IOT_MQTT_PORT = 8883


class MqttThread(threading.Thread):
    """
    The abstract thread that sets up interaction with AWS IoT Things
    """

    def __init__(self, thing_name, cli, thing, cfg, args=(), kwargs={}):
        super(ElfThread, self).__init__(name=thing_name, args=args, kwargs=kwargs)
        self.thing_name = thing_name
        self.thing = thing
        self.root_cert = cli.root_cert
        if cli.append_thing_name:
            self.topic = "{0}/{1}".format(cli.topic, self.thing_name)
        else:
            self.topic = cli.topic

        self.region = cli.region
        self.cfg = cfg
        self.duration = cli.duration
        self.aws_iot = _get_iot_session(self.region, cli.profile_name)
        self.message_qos = cli.qos

        self.policy_name = thing[policy_name_key]
        self.policy_arn = thing[policy_arn_key]

        # setup MQTT client
        eid = uuid.UUID(cfg[elf_id_key])

        # use ELF ID and a random string since we must use unique Client ID per
        # client.
        cid = eid.urn.split(":")[2] + "_" + make_string(3)

        self.mqttc = AWSIoTMQTTClient(clientID=cid)

        t_name = cfg_dir + thing_name_template.format(0)
        endpoint = self.aws_iot.describe_endpoint()

        self.mqttc.configureEndpoint(
            hostName=endpoint["endpointAddress"], portNumber=AWS_IOT_MQTT_PORT
        )
        self.mqttc.configureCredentials(
            CAFilePath=self.root_cert,
            KeyPath=t_name + ".prv",
            CertificatePath=t_name + ".pem",
        )
        self.mqttc.configureAutoReconnectBackoffTime(1, 128, 20)
        self.mqttc.configureOfflinePublishQueueing(90, DROP_OLDEST)
        self.mqttc.configureDrainingFrequency(3)
        self.mqttc.configureConnectDisconnectTimeout(20)
        self.mqttc.configureMQTTOperationTimeout(5)

        self.mqttc.connect()  # keepalive default at 30 seconds


class MqttPoster(MqttThread):
    """
    The thread that does the actual message sending for the desired duration
    """

    def __init__(self, thing_name, cli, thing, cfg, args=(), kwargs={}):
        super(ElfPoster, self).__init__(
            thing_name=thing_name,
            cli=cli,
            thing=thing,
            cfg=cfg,
            args=args,
            kwargs=kwargs,
        )
        self.message = cli.message
        self.json_message = cli.json_message

    def run(self):
        start = datetime.datetime.now()
        finish = start + datetime.timedelta(seconds=self.duration)
        while finish > datetime.datetime.now():
            time.sleep(1)  # wait a second between publishing iterations
            msg = {}
            if self.json_message is None:
                msg["msg"] = "{0}".format(self.message)
            else:
                msg.update(_get_json_message(self.json_message))

            # publish a JSON equivalent of this Thing's message with a
            # timestamp
            s = json.dumps(msg, separators=(", ", ": "))
            self.mqttc.publish(self.topic, s, self.message_qos)


class MqttListener(MqttThread):
    """
    The thread that subscribes to a topic for the desired duration
    """

    def listener_callback(self, client, userdata, message):
        print(
            "Received message: {0} from topic: {1}".format(
                message.payload, message.topic
            )
        )

    def run(self):
        self.mqttc.subscribe(self.topic, 1, self.listener_callback)

        start = datetime.datetime.now()
        finish = start + datetime.timedelta(seconds=self.duration)
        while finish > datetime.datetime.now():
            time.sleep(1)  # wait a second between iterations
