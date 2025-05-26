from pet import VirtualPet
from interaction import setup_gui, run_gui
from ml_model import load_model
import os



def main():
    pet = VirtualPet("")
    model = load_model("model.pkl")
    state_file = f"{pet.name}_state.json"
    if os.path.exists(state_file):
        pet.load_state(state_file)
    else:
        print(f"No save file found for {pet.name}, starting fresh.")

    app = setup_gui(pet, model)
    run_gui(app)


if __name__ == "__main__":
    main()

