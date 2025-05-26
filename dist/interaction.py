import tkinter as tk
from tkinter import messagebox, PhotoImage
from PIL import Image, ImageTk
import os
from PIL import ImageSequence
from ml_model import predict_action
from data_logger import log_interaction
import json

# ----------------------------- Animation Effects -----------------------------
def flash_label(label, flashes=6, delay=100):
    def toggle(n):
        if n <= 0:
            label.config(fg="red")
            return
        current_color = label.cget("fg")
        new_color = "white" if current_color == "red" else "red"
        label.config(fg=new_color)
        label.after(delay, lambda: toggle(n - 1))
    toggle(flashes)

# ----------------------------- GUI Setup -----------------------------
def setup_gui(pet, model):
    label_refs = {"status_labels": {}}
    root = tk.Tk()
    root.title("Virtual Pet")
    root.state("zoomed")

    def disable_buttons():
        for btn in label_refs.get("action_buttons", []):
            btn.config(state="disabled")

    def enable_buttons():
        for btn in label_refs.get("action_buttons", []):
            btn.config(state="normal")

    def getMood():
        if pet.happiness >= 8:
            img = Image.open("petImage/mood/kimoji.png").resize((150, 150), Image.LANCZOS)
        elif pet.happiness >= 5:
            img = Image.open("petImage/mood/happy.png").resize((150, 150), Image.LANCZOS)
        elif pet.happiness >= 1:
            img = Image.open("petImage/mood/bored.png").resize((150, 150), Image.LANCZOS)
        else:
            img = Image.open("petImage/mood/emo.png").resize((150, 150), Image.LANCZOS)
        return img

    def load_existing_pets():
        pets_info = []
        for filename in os.listdir("."):
            if filename.lower().endswith("_state.json"):
                with open(filename) as f:
                    data = json.load(f)
                    name = data.get("name", filename.replace("_state.json", ""))
                    mood = data.get("mood", "unknown")
                    pets_info.append((name, mood))
        return pets_info

    def show_pet():
        img = getMood()
        pet_img = ImageTk.PhotoImage(img)
        label_refs["pet_img_label"].config(image=pet_img)
        label_refs["pet_img_label"].image = pet_img

    def update_status():
        try:
            status = pet.get_state()
            for key, label in label_refs["status_labels"].items():
                value = status.get(key, "N/A")
                label.config(text=f"{value}")
            return "Updated"
        except Exception as e:
            return f"Error: {e}"

    def feed():
        message, is_warning = pet.perform_action("feed")
        pet.save_state(f"{pet.name}_state.json")
        log_interaction("feed", "feed", pet.get_state())
        update_status()
        label_refs["status_message"].config(text=message, fg="red" if is_warning else "black")

        if not is_warning:

            disable_buttons()

            # Load 3 feed animation frames
            frames = [
                ImageTk.PhotoImage(Image.open("petImage/feed/feed1.png").resize((150, 150), Image.LANCZOS)),
                ImageTk.PhotoImage(Image.open("petImage/feed/feed2.png").resize((150, 150), Image.LANCZOS)),
                ImageTk.PhotoImage(Image.open("petImage/feed/feed3.png").resize((150, 150), Image.LANCZOS)),
            ]
            label_refs["feed_frames"] = frames  # prevent GC

            def restore_pet():
                show_pet()
                enable_buttons()

            def animate_feed(index=0):
                if index >= len(frames):
                    root.after(500, restore_pet)
                    return
                label_refs["pet_img_label"].config(image=frames[index])
                label_refs["pet_img_label"].image = frames[index]
                root.after(500, animate_feed, index + 1)

            animate_feed()
        if is_warning:
            flash_label(label_refs["status_message"])
            enable_buttons()

    def play():
        message, is_warning = pet.perform_action("play")
        pet.save_state(f"{pet.name}_state.json")
        log_interaction("play", "play", pet.get_state())
        update_status()
        label_refs["status_message"].config(text=message, fg="red" if is_warning else "black")

        if not is_warning:
            disable_buttons()
            # Load GIF frames
            gif_path = "petImage/play/oiiaioiiai.gif"
            gif = Image.open(gif_path)
            frames = [ImageTk.PhotoImage(frame.resize((150, 150), Image.LANCZOS)) for frame in ImageSequence.Iterator(gif)]
            label_refs["play_frames"] = frames  # prevent garbage collection

            def animate_play(index=0, total_duration=2500, frame_duration=100):
                if index * frame_duration >= total_duration:
                    show_pet()
                    for btn in label_refs["action_buttons"]:
                        btn.config(state="normal")
                    return

                current_frame = frames[index % len(frames)]
                label_refs["pet_img_label"].config(image=current_frame)
                label_refs["pet_img_label"].image = current_frame
                root.after(frame_duration, animate_play, index + 1, total_duration, frame_duration)

            animate_play()

        if is_warning:
            flash_label(label_refs["status_message"])

    def sleep():
        message, is_warning = pet.perform_action("sleep")
        pet.save_state(f"{pet.name}_state.json")
        log_interaction("sleep", "sleep", pet.get_state())
        update_status()
        label_refs["status_message"].config(text=message, fg="red" if is_warning else "black")

        disable_buttons()  # Lock inputs

        if not is_warning:
            img1 = Image.open("petImage/sleep/sleep1.png").resize((150, 150), Image.LANCZOS)
            pet_sleep_img1 = ImageTk.PhotoImage(img1)
            label_refs["pet_img_label"].config(image=pet_sleep_img1)
            label_refs["pet_img_label"].image = pet_sleep_img1

            sleep_frames = [
                ImageTk.PhotoImage(Image.open("petImage/sleep/sleep2.png").resize((150, 150), Image.LANCZOS)),
                ImageTk.PhotoImage(Image.open("petImage/sleep/sleep3.png").resize((150, 150), Image.LANCZOS))
            ]
            label_refs["sleep_frames"] = sleep_frames

            def wake():
                img = Image.open("petImage/sleep/wake.png").resize((150, 150), Image.LANCZOS)
                wake_img = ImageTk.PhotoImage(img)
                label_refs["pet_img_label"].config(image=wake_img)
                label_refs["pet_img_label"].image = wake_img

            def animate(counter=0):
                label_refs["pet_img_label"].configure(image=sleep_frames[counter % 2])
                label_refs["pet_img_label"].image = sleep_frames[counter % 2]
                if counter < 4:
                    root.after(750, animate, counter + 1)
                else:
                    root.after(500, wake)
                    root.after(1000, lambda: [show_pet(), enable_buttons()])  # <- unlock here

            root.after(500, animate)

        else:
            flash_label(label_refs["status_message"])
            enable_buttons()  # unlock immediately if warning

    def reset():
        message = pet.perform_action("reset")
        pet.save_state(f"{pet.name}_state.json")
        log_interaction("reset", "reset", pet.get_state())
        update_status()
        label_refs["status_message"].config(text=message, fg="black")
        show_pet()

    def bath():
        message, is_warning = pet.perform_action("bath")
        pet.save_state(f"{pet.name}_state.json")
        log_interaction("bath", "bath", pet.get_state())
        update_status()
        label_refs["status_message"].config(text=message, fg="red" if is_warning else "black")
        if not is_warning:

            disable_buttons()

            # Load 3 feed animation frames
            frames = [
                ImageTk.PhotoImage(Image.open("petImage/bath/bath1.png").resize((150, 150), Image.LANCZOS)),
                ImageTk.PhotoImage(Image.open("petImage/bath/bath2.png").resize((150, 150), Image.LANCZOS)),
                ImageTk.PhotoImage(Image.open("petImage/bath/bath3.png").resize((150, 150), Image.LANCZOS)),
            ]
            label_refs["bath_frames"] = frames  # prevent GC

            def restore_pet():
                show_pet()
                enable_buttons()

            def animate_feed(index=0):
                if index >= len(frames):
                    root.after(500, restore_pet)
                    return
                label_refs["pet_img_label"].config(image=frames[index])
                label_refs["pet_img_label"].image = frames[index]
                root.after(500, animate_feed, index + 1)

            animate_feed()
        if is_warning:
            flash_label(label_refs["status_message"])
            enable_buttons()

    def name_pet():

        new_name = name_entry.get().strip()
        if new_name:
            pet.name = new_name
            state_file = f"{pet.name}_state.json"
            if os.path.exists(state_file):
                pet.load_state(state_file)

            for widget in root.winfo_children():
                widget.destroy()

            pet_frame = tk.Frame(root)
            pet_frame.pack(pady=10)

            # Setup the pet_frame with a Canvas for background layering
            pet_frame = tk.Canvas(root, width=300, height=300, highlightthickness=0)
            pet_frame.pack(pady=10)

            # Load and resize background image
            bg_img = Image.open("Images/pet_frame_bg.png").resize((300, 300), Image.LANCZOS)
            bg_photo = ImageTk.PhotoImage(bg_img)
            label_refs["pet_bg_image"] = bg_photo  # Prevent garbage collection

            # Place the background image
            pet_frame.create_image(0, 0, image=bg_photo, anchor="nw")

            # Load the pet's mood image
            ori_pet_img = getMood()
            pet_img = ImageTk.PhotoImage(ori_pet_img)
            label_refs["pet_image"] = pet_img

            # Create the pet image on the canvas
            pet_img_label = tk.Label(pet_frame, image=pet_img, bd=0, highlightthickness=0)
            label_refs["pet_img_label"] = pet_img_label

            # Add the label to the canvas (centered)
            pet_frame.create_window(150, 150, window=pet_img_label)

            tk.Label(root, text=pet.name, font=("Comic Sans MS", 24)).pack(pady=5)

            status_container = tk.Frame(root)
            status_container.pack(pady=5)

            label_refs["status_message"] = tk.Label(
                status_container, text="", justify=tk.CENTER, font=("Comic Sans MS", 24)
            )
            label_refs["status_message"].pack()

            status_frame = tk.Frame(root, bg="#fffaf0", bd=3, relief="ridge")
            status_frame.pack(pady=10)

            emoji_map = {
                "hunger": "🍗Hunger",
                "energy": "⚡Energy",
                "happiness": "😊Happiness",
                "health": "❤️Health",
                "intelligence": "🧠Intelligence",
                "creativity": "🎨Creativity",
                "weather_affinity": "☁️Weather Affinity",
                "mood": "😶Mood"
            }

            left_stats = ["hunger", "energy", "happiness", "health"]
            right_stats = ["intelligence", "creativity", "weather_affinity", "mood"]

            for i, key in enumerate(left_stats):
                tk.Label(status_frame, text=emoji_map[key], font=("Arial", 18), bg="#fffaf0").grid(row=i, column=0, padx=5, sticky="e")
                lbl = tk.Label(status_frame, text="", font=("Comic Sans MS", 16), bg="#fffaf0", width=20, anchor="w")
                lbl.grid(row=i, column=1, padx=5, pady=2, sticky="w")
                label_refs["status_labels"][key] = lbl

            for i, key in enumerate(right_stats):
                tk.Label(status_frame, text=emoji_map[key], font=("Arial", 18), bg="#fffaf0").grid(row=i, column=2, padx=5, sticky="e")
                lbl = tk.Label(status_frame, text="", font=("Comic Sans MS", 16), bg="#fffaf0", width=20, anchor="w")
                lbl.grid(row=i, column=3, padx=5, pady=2, sticky="w")
                label_refs["status_labels"][key] = lbl

            feed_img = ImageTk.PhotoImage(Image.open("Images/orange.png").resize((70, 70)))
            play_img = ImageTk.PhotoImage(Image.open("Images/play.png").resize((70, 70)))
            sleep_img = ImageTk.PhotoImage(Image.open("Images/sleep.png").resize((70, 70)))
            bath_img = ImageTk.PhotoImage(Image.open("Images/bath.png").resize((70, 70)))

            button_frame = tk.Frame(root)

            label_refs["action_buttons"] = []  # Add this before packing buttons

            btn_feed = tk.Button(button_frame, image=feed_img, text="FEED", compound="left",
                                 font=("Comic Sans MS", 16, "bold"),
                                 command=feed, bg="pink")
            btn_feed.pack(side="left", padx=10)

            btn_play = tk.Button(button_frame, image=play_img, text="PLAY", compound="left",
                                 font=("Comic Sans MS", 16, "bold"),
                                 command=play, bg="pink")
            btn_play.pack(side="left", padx=10)

            btn_sleep = tk.Button(button_frame, image=sleep_img, text="SLEEP", compound="left",
                                  font=("Comic Sans MS", 16, "bold"),
                                  command=sleep, bg="pink")
            btn_sleep.pack(side="left", padx=10)

            btn_bath = tk.Button(button_frame, image=bath_img, text="BATH", compound="left",
                                 font=("Comic Sans MS", 16, "bold"),
                                 command=bath, bg="pink")
            btn_bath.pack(side="left", padx=10)

            # Save them
            label_refs["action_buttons"] = [btn_feed, btn_play, btn_sleep, btn_bath]
            button_frame.feed_img = feed_img
            button_frame.play_img = play_img
            button_frame.sleep_img = sleep_img
            button_frame.bath_img = bath_img
            button_frame.pack(pady=20)

            reset_img = ImageTk.PhotoImage(Image.open("Images/reset.png").resize((70, 70)))
            reset_btn = tk.Button(root, image=reset_img, command=reset)
            reset_btn.image = reset_img

            def place_reset():
                root.update_idletasks()
                rw = root.winfo_width()
                rh = root.winfo_height()
                bw = reset_btn.winfo_reqwidth()
                bh = reset_btn.winfo_reqheight()
                reset_btn.place(x=rw - bw - 20, y=rh - bh - 20)

            root.after(200, place_reset)
            update_status()

    # ---------------- Initial UI ----------------
    icon_path = os.path.abspath("Images/icon.ico")
    root.iconbitmap(icon_path)
    root.iconphoto(False, ImageTk.PhotoImage(Image.open("Images/icon.jpg")))

    original_pet_img = Image.open("petImage/mood/happy.png")
    resized_pet_img = original_pet_img.resize((150, 150), Image.Resampling.LANCZOS)
    pet_img = ImageTk.PhotoImage(resized_pet_img)  # <- this line must use ImageTk
    img_label = tk.Label(root, image=pet_img)
    img_label.image = pet_img
    img_label.pack()

    tk.Label(root, text="Your pet's name is:", font=("Comic Sans MS", 18)).pack(pady=5)
    name_entry = tk.Entry(root, font=("Comic Sans MS", 16), justify = "center",width=25)
    name_entry.insert(0, pet.name)
    name_entry.pack(pady=5)

    tk.Button(root, text="Enter", font=("Comic Sans MS", 24), command=name_pet).pack(pady=5)

    # Load GIF
    gif_path = "Images/doro_gif.gif"  # Replace with your actual file
    gif = Image.open(gif_path)

    frames = [ImageTk.PhotoImage(frame.copy().resize((300, 150), Image.LANCZOS))
              for frame in ImageSequence.Iterator(gif)]

    label_refs["intro_frames"] = frames  # Keep reference to avoid GC

    # Display first frame
    intro_label = tk.Label(root, image=frames[0], bg="white")
    intro_label.pack()
    label_refs["intro_label"] = intro_label

    # Animate
    def animate_gif(index=0):
        frame = frames[index % len(frames)]
        intro_label.config(image=frame)
        label_refs["intro_label"].image = frame
        root.after(100, animate_gif, index + 1)

    animate_gif()
    # Create a frame below the GIF
    pet_list_frame = tk.Frame(root)
    pet_list_frame.pack(pady=10)

    tk.Label(pet_list_frame, text="Existing Pets:", font=("Comic Sans MS", 16, "bold")).pack()

    pets = load_existing_pets()
    if pets:
        for name, mood in pets:
            tk.Label(pet_list_frame, text=f"Name: {name} | Mood: {mood}", font=("Comic Sans MS", 14)).pack()
    else:
        tk.Label(pet_list_frame, text="No saved pets found.", font=("Comic Sans MS", 14)).pack()

    return root

# ----------------------------- CLI Fallback -----------------------------
def run_gui(app):
    app.mainloop()

def get_user_input():
    return input("What would you like to do with your pet? ")

def display_pet_response(response):
    print(response)

def parse_input(user_input):
    return user_input.lower().strip()
