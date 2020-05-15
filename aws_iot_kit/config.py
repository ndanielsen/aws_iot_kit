import yaml


def load_config():
    with open("aws-iot.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        return config


def update_config(config):
    with open("aws-iot.yaml", "w") as f:
        data = yaml.dump(config, f)
        return data
