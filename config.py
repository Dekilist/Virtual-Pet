CONFIG = {
    "model_path": "model.pkl",
    "state_file": "start.json",
    "log_file": "interaction_log.json"
}


def get_config():
    return CONFIG


def update_config(key, value):
    CONFIG[key] = value
