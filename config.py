# config.py
# Sections:
# 1) Paths/config
# 2) RL hyperparameters
# 3) NLP toggles
# 4) UI timing

from pathlib import Path

# 1) Paths/config
ROOT = Path(__file__).parent
ASSET_DIR = ROOT / "Images"
DATA_DIR = ROOT / "data"
MODEL_DIR = DATA_DIR / "models"
LOG_DIR = DATA_DIR / "logs"
for p in (DATA_DIR, LOG_DIR, MODEL_DIR):
    p.mkdir(parents=True, exist_ok=True)

# 2) RL hyperparameters
RL = {
    "LR": 1e-3,
    "GAMMA": 0.95,
    "EPS_START": 0.9,
    "EPS_END": 0.05,
    "EPS_DECAY_STEPS": 3000,
    "BATCH_SIZE": 64,
    "REPLAY_SIZE": 10000,
    "TARGET_SYNC": 200,
    "TRAIN_EVERY": 10
}

# 3) NLP toggles
NLP = {
    "USE_BERT": False,   # start simple with TF-IDF + LinearSVC
    "MIN_CONF": 0.6
}

# 4) UI timing
TICK_MS = 500          # how often we call pet.tick()
LOG_FLUSH_EVERY = 20   # flush log after N events

# 5) Feature toggles
USE_RL = False         # keep False until Layer B
USE_NLP = False        # keep False until Layer B