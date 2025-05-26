import json
import os
import random

class VirtualPet:
    def __init__(self, name):
        self.name = name
        self.hunger = 5
        self.happiness = 5
        self.energy = 5

        # New stats
        self.health = 100
        self.intelligence = 10
        self.creativity = 10
        self.weather_affinity = 50
        self.mood = self.calculate_mood()

        # Ensure directory exists
        os.makedirs("pet_state", exist_ok=True)

    def calculate_mood(self):
        if self.happiness >= 8:
            return "KIMOJI!!"
        elif self.happiness >= 5:
            return "Happy Happy Happy"
        elif self.happiness >= 3:
            return "bored"
        else:
            return "Emo"

    def update_state(self, user_input):
        # Placeholder for future ML-based prediction
        pass

    def get_state(self):
        return {
            "name": self.name,
            "hunger": self.hunger,
            "happiness": self.happiness,
            "energy": self.energy,
            "health": self.health,
            "intelligence": self.intelligence,
            "creativity": self.creativity,
            "weather_affinity": self.weather_affinity,
            "mood": self.calculate_mood()
        }

    def perform_action(self, action):
        if action == "feed":
            if self.hunger == 0:
                return f"{self.name} is FULL", True
            elif self.intelligence == 0:
                return f"{self.name} had TOO MUCH sugar, dizzy dizzy dizzy", True
            elif self.health < 100:
                self.hunger -= 1
                self.energy += 1
                self.intelligence -= 5
                self.health += 1
                return f"{self.name} eats happily.", False
            else:
                self.hunger -= 1
                self.energy += 1
                self.intelligence -= 5
                return f"{self.name} eats happily.", False

        elif action == "play":
            injury = random.random()
            if self.health == 0:
                return f"{self.name} is INJURED", True
            if injury < 0.15:
                self.health -= 20
            if self.energy == 0:
                return f"{self.name} is TIRED, REST OR EAT TO GAIN ENERGY", True
            else:
                self.happiness += 1
                self.energy -= 1
                self.hunger += 1
                return f"{self.name} plays around.", False

        elif action == "sleep":
            if self.happiness == 0:
                return f"{self.name} is EMO, {self.name} needs more fun", True
            elif self.health < 100:
                self.energy += 2
                self.hunger += 1
                self.happiness -= 1
                self.health += 2
                self.intelligence += 5
                return f"{self.name} takes a nap.", False
            else:
                self.energy += 2
                self.hunger += 1
                self.happiness -= 1
                self.intelligence += 5
                return f"{self.name} takes a nap.", False

        elif action == "reset":
            self.hunger = 5
            self.energy = 5
            self.happiness = 5
            self.health = 100
            self.intelligence = 10
            self.creativity = 10
            self.weather_affinity = 50
            return f"{self.name} resets."

        elif action == "bath":
            if self.energy == 0:
                return f"{self.name} is TIRED, REST OR EAT TO GAIN ENERGY", True
            else:
                self.hunger += 1
                self.happiness += 1
                self.energy -= 1
                self.health += 10
                return f"{self.name} took a bath.", False

        else:
            return f"{self.name} doesn't understand.", True

    def save_state(self, filepath=None):
        if filepath is None:
            filepath = os.path.join("pet_state", f"{self.name}_state.json")
        with open(filepath, "w") as f:
            json.dump(self.get_state(), f)

    def load_state(self, filepath=None):
        if filepath is None:
            filepath = os.path.join("pet_state", f"{self.name}_state.json")
        try:
            with open(filepath, 'r') as f:
                content = f.read().strip()
                if not content:
                    return
                state = json.loads(content)
                self.name = state["name"]
                self.hunger = state.get("hunger", 5)
                self.happiness = state.get("happiness", 5)
                self.energy = state.get("energy", 5)
                self.health = state.get("health", 100)
                self.intelligence = state.get("intelligence", 10)
                self.creativity = state.get("creativity", 10)
                self.weather_affinity = state.get("weather_affinity", 50)
                self.mood = self.calculate_mood()
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            print("Warning: pet state file is corrupted. Starting fresh.")
