# pet.py
# Sections:
# 1) Enums/constants
# 2) VirtualPet class: init, tick, apply_user_action, state vector, save/load
# 3) Helper: mood recompute

from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Dict, Any, Tuple

MOODS = ["very_sad", "sad", "neutral", "happy", "very_happy"]
ACTIONS_USER = ["feed", "play", "sleep", "bath", "talk", "idle"]
ACTIONS_AGENT = ["prompt_user_play", "prompt_user_feed", "self_sleep", "self_idle", "prompt_user_bath"]

@dataclass
class PetState:
    mood: str = "neutral"
    hunger: int = 2       # 0..4
    energy: int = 2       # 0..4
    hygiene: int = 2      # 0..4
    last_action: str = "idle"
    ticks_since_user: int = 0    # coarse engagement signal

class VirtualPet:
    def __init__(self, save_path: Path):
        self.save_path = save_path
        self.state = PetState()
        self._load_if_exists()

    # 2a) environment tick: passive changes + decay
    def tick(self):
        s = self.state
        s.ticks_since_user += 1
        # simple decay rules
        if s.last_action != "feed":
            s.hunger = min(4, s.hunger + 1)
        if s.last_action == "play":
            s.energy = max(0, s.energy - 1)
        else:
            s.energy = min(4, s.energy + 0)  # neutral; can add slow regen
        if s.last_action != "bath":
            s.hygiene = max(0, s.hygiene - 1)

        s.mood = self.recompute_mood(s.hunger, s.energy, s.hygiene)

    # 2b) user applies an action (from GUI/NLP)
    def apply_user_action(self, intent: str):
        s = self.state
        s.ticks_since_user = 0
        if intent == "feed":
            s.hunger = max(0, s.hunger - 2)
        elif intent == "play":
            s.energy = max(0, s.energy - 1)
            s.hygiene = max(0, s.hygiene - 1)
        elif intent == "sleep":
            s.energy = min(4, s.energy + 2)
        elif intent == "bath":
            s.hygiene = min(4, s.hygiene + 2)
        elif intent == "talk":
            pass
        s.last_action = intent
        s.mood = self.recompute_mood(s.hunger, s.energy, s.hygiene)

    # 2c) map discrete state to a compact vector for RL
    def get_state_vector(self) -> Tuple[int, int, int, int, int, int]:
        mood_idx = MOODS.index(self.state.mood)
        last_idx = ACTIONS_USER.index(self.state.last_action) if self.state.last_action in ACTIONS_USER else 5
        # buckets for ticks_since_user
        t_bucket = 0 if self.state.ticks_since_user == 0 else (1 if self.state.ticks_since_user < 4 else (2 if self.state.ticks_since_user < 8 else 3))
        return mood_idx, self.state.hunger, self.state.energy, self.state.hygiene, last_idx, t_bucket

    def save(self):
        self.save_path.write_text(json.dumps(asdict(self.state), indent=2), encoding="utf-8")

    def _load_if_exists(self):
        if self.save_path.exists():
            try:
                data = json.loads(self.save_path.read_text(encoding="utf-8"))
                self.state = PetState(**data)
            except Exception:
                pass

    # 3) heuristic mood function
    def recompute_mood(self, hunger: int, energy: int, hygiene: int) -> str:
        score = (4 - hunger) + energy + hygiene  # higher is better
        if score <= 3: return MOODS[0]
        if score <= 5: return MOODS[1]
        if score <= 7: return MOODS[2]
        if score <= 9: return MOODS[3]
        return MOODS[4]
