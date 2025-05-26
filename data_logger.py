import json
from datetime import datetime


def log_interaction(user_input, pet_action, pet_status):
    log = {
        "timestamp": datetime.now().isoformat(),
        "user_input": user_input,
        "action": pet_action,
        "status": pet_status
    }
    with open("interaction_log.json", 'a') as f:
        f.write(json.dumps(log) + "\n")


def load_logs(filepath):
    with open(filepath, 'r') as f:
        return [json.loads(line) for line in f]


def clear_logs(filepath):
    open(filepath, 'w').close()