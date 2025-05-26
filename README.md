# Virtual-Pet

This is a Python-based GUI application simulating a customizable, animated virtual pet. It evolves through user interactions and tracks stats like happiness, energy, health, and more. The pet responds visually through pixel art animations and remembers its state across sessions.

---

##Features

- **Animated GUI** using `tkinter` and `Pillow`
- **Custom pet name** input through GUI
- **Persistent state** stored in JSON files (e.g., `DORO_state.json`)
- **Visual feedback** with moods: `KIMOJI!!`, `Happy`, `Bored`, `Emo`
- **Action animations** for:
  - Feeding 
  - Playing 
  - Sleeping
  - Bathing
- **Intro GIF** and list of existing pets on startup
- **ML Integration Ready**: `ml_model.py` placeholder for predictive behavior
- **Logging system** for interaction tracking

---

##Directory Structure
│
├── pet.py # VirtualPet class
├── interaction.py # GUI and animations
├── main.py # Entry point
├── ml_model.py # Machine learning placeholder
├── data_logger.py # Logs actions to a JSON file
├── config.py # Centralized config
│
├── Images/
│ ├── icon.ico, icon.jpg
│ ├── doro_gif.gif
│ └── action icons (orange.png, play.png, etc.)
│
├── petImage/
│ ├── mood/
│ │ ├── kimoji.png, happy.png, bored.png, emo.png
│ ├── feed/
│ ├── play/
│ ├── sleep/
│ └── bath/
│
├── *.json # Pet state files (e.g., DORO_state.json)
└── README.md # You are here!


---

## 🚀 How to Run

### Requirements

- Python 3.10+
- `Pillow`
- `tkinter`

  
---
