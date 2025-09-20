# ============================
# nlp.py — Intent Recognition (Lightweight)
# ============================
# Sections:
# 1) Keyword dictionary (fast heuristic baseline)
# 2) predict_intent(text) -> (label, confidence)
# Technique: Start simple; keep API stable so you can replace internals later.

from typing import Tuple

# 1) Keywords
KEYWORDS = {
    "feed": ["feed", "food", "eat", "hungry", "snack"],
    "play": ["play", "game", "toy", "fun"],
    "sleep": ["sleep", "nap", "rest", "tired"],
    "bath": ["bath", "wash", "clean", "shower"],
    # "talk" is the default catch-all intent
}

# 2) Predictor
def predict_intent(text: str) -> Tuple[str, float]:
    t = (text or "").lower()
    for label, words in KEYWORDS.items():
        if any(w in t for w in words):
            return label, 0.8
    return "talk", 0.5
