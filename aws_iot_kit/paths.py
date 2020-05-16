from pathlib import Path


def _mkdir_thing(thing, certs_folder):
    Path(f"{certs_folder}/{thing}").mkdir(exist_ok=True)


def _determine_file_paths(thing_id, certs_folder):
    thing_path_base = f"{certs_folder}/{thing_id}"
    return dict(
        thing_path_base=thing_path_base,
        certname=f"{thing_path_base}/{thing_id}.pem",
        public_key_file=f"{thing_path_base}/{thing_id}.pub",
        private_key_file=f"{thing_path_base}/{thing_id}.prv",
    )
