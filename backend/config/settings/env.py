import os
import json


def env_value(name, default=""):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def env_csv(name, default=""):
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def env_required(name):
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        raise RuntimeError(f"{name} must be set")
    return raw.strip()


def env_int(name, default):
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def env_json(name, default=None):
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return {} if default is None else default
    return json.loads(raw)
