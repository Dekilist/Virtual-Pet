# ============================
# pet.py — Virtual Pet (Improved)
# ============================
# Sections:
# 1) Imports & Constants
# 2) Utilities (clamp)
# 3) VirtualPet class
#    3.1) __init__ (state setup)
#    3.2) calculate_mood (derived state from multiple stats)
#    3.3) tick (time-based decay/regression)
#    3.4) update_state (reserved hook for RL/policy)
#    3.5) get_state (JSON-serializable snapshot)
#    3.6) perform_action (user-triggered transitions; consistent returns)
#    3.7) save_state / load_state (atomic persistence with clamping)
#    3.8) get_state_vector (compact numeric state for RL)

import json
import os
import time
import random
from typing import Tuple, Dict, Any

# ----------------------------
# 1) Imports & Constants
# ----------------------------
# Technique: centralize "game balance" knobs to avoid magic numbers
HUNGER_MIN, HUNGER_MAX = 0, 10
ENERGY_MIN, ENERGY_MAX = 0, 10
HAPPINESS_MIN, HAPPINESS_MAX = 0, 10
HEALTH_MIN, HEALTH_MAX = 0, 100
INT_MIN, INT_MAX = 0, 200
CREAT_MIN, CREAT_MAX = 0, 200
WEATHER_MIN, WEATHER_MAX = 0, 100

INJURY_PROB = 0.15  # probability of injury on "play"


# ----------------------------
# 2) Utilities
# ----------------------------
def clamp(x: int | float, lo: int | float, hi: int | float):
    """Keep values within safe bounds (technique: defensive programming)."""
    return max(lo, min(hi, x))


# ----------------------------
# 3) VirtualPet class
# ----------------------------
class VirtualPet:

    # 3.1) __init__ (state setup)
    def __init__(self, name: str):
        self.name = name

        # Core stats (kept from your original design)
        self.hunger = 5
        self.happiness = 5
        self.energy = 5

        # Extended stats
        self.health = 100
        self.intelligence = 10
        self.creativity = 10
        self.weather_affinity = 50

        # Derived/semantic state
        self.mood = self.calculate_mood()

        # Cooldowns / counters (prevent tick from instantly undoing actions)
        self._tick_count = 0
        self._no_hunger_increase_ticks = 0  # set after feeding
        self._last_hunger_ts = int(time.time())  # when hunger last auto-increased

    # 3.2) calculate_mood
    def calculate_mood(self) -> str:
        # Hard override: if happiness is zero, show EMO
        if self.happiness <= 0:
            return "Emo"

        inv_hunger = 10 - clamp(self.hunger, HUNGER_MIN, HUNGER_MAX)
        score = (
                inv_hunger
                + clamp(self.energy, ENERGY_MIN, ENERGY_MAX)
                + clamp(self.happiness, HAPPINESS_MIN, HAPPINESS_MAX)
                + (clamp(self.health, HEALTH_MIN, HEALTH_MAX) / 20.0)
        )
        # Slightly stricter thresholds so low happiness shows as worse mood
        if score >= 24:
            return "KIMOJI!!"
        elif score >= 18:
            return "Happy Happy Happy"
        elif score >= 11:
            return "sad"
        else:
            return "Emo"

    # 3.3) tick (time-based decay)
    def tick(self):
        """
        Real-time drift: hunger increases by +1 every 30 minutes of wall time.
        Other stats do not auto-change here (tune as desired).
        """
        now = int(time.time())

        # How many full 30-minute blocks have passed since the last hunger increment?
        THIRTY_MIN = 30 * 60
        elapsed = now - int(self._last_hunger_ts or now)

        if elapsed >= THIRTY_MIN:
            steps = elapsed // THIRTY_MIN  # number of +1 steps to apply
            if steps > 0:
                self.hunger = clamp(self.hunger + int(steps), HUNGER_MIN, HUNGER_MAX)
                # move the marker forward by whole steps
                self._last_hunger_ts = int(self._last_hunger_ts) + steps * THIRTY_MIN
        else:
            # no full 30-min block yet; keep timestamp as is
            pass

        # Optional: gentle happiness regression only occasionally, or remove it entirely.
        # Commented out to avoid suppressing >5 happiness.
        if self.happiness > 5 and (now // 3600) != ((now-1) // 3600):  # once per hour, example
            self.happiness = clamp(self.happiness - 1, HAPPINESS_MIN, HAPPINESS_MAX)

        # Recompute derived mood
        self.mood = self.calculate_mood()

    # 3.4) update_state (reserved for RL/policy)
    def update_state(self, user_input: Any):
        """
        Placeholder hook for RL/policy-based updates.
        Use this later to integrate agent suggestions or NLP intents.
        """
        pass

    # 3.5) get_state (snapshot)
    def get_state(self) -> Dict[str, Any]:
        """
        Returns a JSON-serializable snapshot for UI/persistence.
        Technique: compute mood on read to ensure consistency.
        """
        return {
            "name": self.name,
            "hunger": int(self.hunger),
            "happiness": int(self.happiness),
            "energy": int(self.energy),
            "health": int(self.health),
            "intelligence": int(self.intelligence),
            "creativity": int(self.creativity),
            "weather_affinity": int(self.weather_affinity),
            "mood": self.calculate_mood(),
            "_last_hunger_ts": int(self._last_hunger_ts or int(time.time()))
        }


    # 3.6) perform_action (transitions)
    def perform_action(self, action: str) -> Tuple[str, bool]:
        """
        Apply a user action. Always returns (message, is_error).
        Technique: consistent interface + clamped updates for robustness.
        """
        # FEED
        if action == "feed":
            if self.hunger == HUNGER_MIN:
                return f"{self.name} is FULL", True

            # If intelligence is 0, warn but still allow feeding once (don’t block hunger drop)
            warned = False
            if self.intelligence == 0:
                warned = True

            self.hunger = clamp(self.hunger - 1, HUNGER_MIN, HUNGER_MAX)
            self._last_hunger_ts = int(time.time())  # reset the 30-minute clock after feeding
            self.energy = clamp(self.energy + 1, ENERGY_MIN, ENERGY_MAX)
            # Make the INT penalty gentler so it doesn't hit 0 so fast
            self.intelligence = clamp(self.intelligence - 2, INT_MIN, INT_MAX)
            if self.health < HEALTH_MAX:
                self.health = clamp(self.health + 1, HEALTH_MIN, HEALTH_MAX)
            self.mood = self.calculate_mood()

            # Pause hunger drift for a few ticks so the change is visible
            self._no_hunger_increase_ticks = 3

            if warned:
                return f"{self.name} is dizzy but eats anyway.", False
            return f"{self.name} eats happily.", False


        # PLAY
        elif action == "play":
            if self.health == HEALTH_MIN:
                return f"{self.name} is INJURED", True
            if self.energy == ENERGY_MIN:
                return f"{self.name} is TIRED, REST OR EAT TO GAIN ENERGY", True
            if random.random() < INJURY_PROB:
                self.health = clamp(self.health - 20, HEALTH_MIN, HEALTH_MAX)
            self.happiness = clamp(self.happiness + 1, HAPPINESS_MIN, HAPPINESS_MAX)
            self.energy = clamp(self.energy - 1, ENERGY_MIN, ENERGY_MAX)
            self.hunger = clamp(self.hunger + 1, HUNGER_MIN, HUNGER_MAX)
            self.mood = self.calculate_mood()
            # Prevent immediate extra hunger from tick right after play animation
            self._no_hunger_increase_ticks = max(self._no_hunger_increase_ticks, 1)
            return f"{self.name} plays around.", False

        # SLEEP
        elif action == "sleep":
            if self.happiness == HAPPINESS_MIN:
                return f"{self.name} is EMO, {self.name} needs more fun", True
            self.energy = clamp(self.energy + 2, ENERGY_MIN, ENERGY_MAX)
            self.hunger = clamp(self.hunger + 1, HUNGER_MIN, HUNGER_MAX)
            self.happiness = clamp(self.happiness - 1, HAPPINESS_MIN, HAPPINESS_MAX)
            self.health = clamp(self.health + 2, HEALTH_MIN, HEALTH_MAX)
            self.intelligence = clamp(self.intelligence + 5, INT_MIN, INT_MAX)
            self.mood = self.calculate_mood()
            return f"{self.name} takes a nap.", False

        # BATH
        elif action == "bath":
            if self.energy == ENERGY_MIN:
                return f"{self.name} is TIRED, REST OR EAT TO GAIN ENERGY", True
            self.hunger = clamp(self.hunger + 1, HUNGER_MIN, HUNGER_MAX)
            self.happiness = clamp(self.happiness + 1, HAPPINESS_MIN, HAPPINESS_MAX)
            self.energy = clamp(self.energy - 1, ENERGY_MIN, ENERGY_MAX)
            self.health = clamp(self.health + 10, HEALTH_MIN, HEALTH_MAX)
            self.mood = self.calculate_mood()
            return f"{self.name} took a bath.", False

        # RESET (ensure consistent tuple return)
        elif action == "reset":
            self.hunger = 5
            self.energy = 5
            self.happiness = 5
            self.health = 100
            self.intelligence = 10
            self.creativity = 10
            self.weather_affinity = 50
            self.mood = self.calculate_mood()
            return f"{self.name} resets.", False

        # UNKNOWN
        else:
            return f"{self.name} doesn't understand.", True


    # 3.7) Persistence (atomic)
    def save_state(self, filepath: str | None = None):
        """
        Technique: atomic write (tmp -> rename) prevents corrupted files.
        Default location: project root as <name>_state.json
        """
        if filepath is None:
            filepath = f"{self.name}_state.json"
        tmp = filepath + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.get_state(), f, ensure_ascii=False)
        os.replace(tmp, filepath)

    def load_state(self, filepath: str | None = None):
        """
        Technique: defensive read + clamping to sanitize external edits.
        """
        if filepath is None:
            filepath = f"{self.name}_state.json"
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return
                state = json.loads(content)

            # Assign with clamping
            self.name = state.get("name", self.name)
            self.hunger = clamp(state.get("hunger", 5), HUNGER_MIN, HUNGER_MAX)
            self.happiness = clamp(state.get("happiness", 5), HAPPINESS_MIN, HAPPINESS_MAX)
            self.energy = clamp(state.get("energy", 5), ENERGY_MIN, ENERGY_MAX)
            self.health = clamp(state.get("health", 100), HEALTH_MIN, HEALTH_MAX)
            self.intelligence = clamp(state.get("intelligence", 10), INT_MIN, INT_MAX)
            self.creativity = clamp(state.get("creativity", 10), CREAT_MIN, CREAT_MAX)
            self.weather_affinity = clamp(state.get("weather_affinity", 50), WEATHER_MIN, WEATHER_MAX)
            self.mood = self.calculate_mood()
            self._last_hunger_ts = int(state.get("_last_hunger_ts", int(time.time())))

            # One-time catch-up on load
            now = int(time.time())
            THIRTY_MIN = 30 * 60
            elapsed = now - int(self._last_hunger_ts or now)
            if elapsed >= THIRTY_MIN:
                steps = elapsed // THIRTY_MIN
                if steps > 0:
                    self.hunger = clamp(self.hunger + int(steps), HUNGER_MIN, HUNGER_MAX)
                    self._last_hunger_ts = int(self._last_hunger_ts) + steps * THIRTY_MIN


        except FileNotFoundError:
            # Fresh start is fine
            pass
        except json.JSONDecodeError:
            print("Warning: pet state file is corrupted. Starting fresh.")

    # 3.8) RL state vector
    def get_state_vector(self) -> Tuple[int, int, int, int]:
        """
        Compact numeric state for RL/logging.
        Order: (hunger, energy, happiness, health_scaled 0..10)
        """
        health_scaled = int(round(self.health / 10))  # 0..10 bucket
        return int(self.hunger), int(self.energy), int(self.happiness), health_scaled
