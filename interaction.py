# interaction.py — Tkinter UI for Virtual Pet (Refactored)
# Sections:
# 1) Imports & Optional Integrations
# 2) PetApp class (constructor wires UI + handlers)
# 3) Helpers (flash_label, safe PhotoImage cache, mood image loader)
# 4) Action handlers (feed/play/sleep/bath/reset)
# 5) Status refresh, saved pets list, intro GIF, and name flow
# 6) Tick loop & run()

import os
import json
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageSequence
import time

# 1) Imports & Optional Integrations
# Technique: optional imports so UI still works without these modules.
try:
    from ml_model import predict_action
except Exception:
    predict_action = None

try:
    from data_logger import log_interaction
except Exception:
    def log_interaction(*args, **kwargs):  # no-op fallback
        pass


class PetApp(tk.Tk):
    """
    MVC-ish design:
      - PetApp publishes user intents and renders state.
      - It never mutates pet state directly except via pet.perform_action() and pet.tick().
    """

    # 2) Constructor: build UI, wire callbacks
    def __init__(self, pet, *, tick_ms=500):
        super().__init__()
        self.title("Virtual Pet")
        # On Windows you can "zoomed"; on macOS use geometry instead; keep try/except
        try:
            self.state("zoomed")
        except Exception:
            self.geometry("900x700")

        self.pet = pet
        self.tick_ms = tick_ms

        # Cooldowns / counters (prevent tick from instantly undoing actions)
        self._tick_count = 0
        self._no_hunger_increase_ticks = 0  # set after feeding

        # widget refs + image caches to avoid GC
        self.refs = {"status_labels": {}, "images": {}, "frames": {}, "buttons": []}

        # Icon is optional
        self._try_set_icons()

        # Intro area (pet name entry, intro GIF, saved-pets list)
        self._build_intro()

    # ---------------- Helpers & Setup ----------------

    def _try_set_icons(self):
        try:
            self.iconbitmap(os.path.abspath("Images/icon.ico"))
        except Exception:
            pass
        try:
            icon_jpg = Image.open("Images/icon.jpg")
            self.iconphoto(False, ImageTk.PhotoImage(icon_jpg))
        except Exception:
            pass

    def _build_intro(self):
        # Pet preview
        try:
            img = Image.open("Images/petImage/mood/happy.png").resize((150, 150), Image.LANCZOS)
        except Exception:
            img = Image.new("RGBA", (150, 150), (200, 200, 200, 255))
        self.refs["images"]["intro_pet"] = ImageTk.PhotoImage(img)
        self.refs["intro_pet_label"] = tk.Label(self, image=self.refs["images"]["intro_pet"])
        self.refs["intro_pet_label"].pack()

        tk.Label(self, text="Your pet's name is:", font=("Comic Sans MS", 18)).pack(pady=5)
        self.name_entry = tk.Entry(self, font=("Comic Sans MS", 16), justify="center", width=25)
        self.name_entry.insert(0, self.pet.name)
        self.name_entry.pack(pady=5)

        ttk.Button(self, text="Enter", command=self._on_name_enter).pack(pady=5)

        # Animated intro GIF (optional)
        self._build_intro_gif()

        # Saved pets list
        self._build_saved_pets_list()

    def _build_intro_gif(self):
        try:
            gif_path = "Images/doro_gif.gif"
            gif = Image.open(gif_path)
            frames = [ImageTk.PhotoImage(frame.copy().resize((300, 150), Image.LANCZOS))
                      for frame in ImageSequence.Iterator(gif)]
            self.refs["frames"]["intro"] = frames
            lbl = tk.Label(self, image=frames[0], bg="white")
            lbl.pack()
            self.refs["intro_gif_label"] = lbl

            def animate(idx=0):
                fr = frames[idx % len(frames)]
                lbl.config(image=fr)
                lbl.image = fr
                self.after(100, animate, idx + 1)

            animate()
        except Exception:
            # silently ignore if file missing
            pass

    def _build_saved_pets_list(self):
        frame = tk.Frame(self)
        frame.pack(pady=10)
        tk.Label(frame, text="Existing Pets:", font=("Comic Sans MS", 16, "bold")).pack()
        pets = self._load_existing_pets()
        if pets:
            for name, mood in pets:
                tk.Label(frame, text=f"Name: {name} | Mood: {mood}", font=("Comic Sans MS", 14)).pack()
        else:
            tk.Label(frame, text="No saved pets found.", font=("Comic Sans MS", 14)).pack()
        self.refs["saved_pets_frame"] = frame

    def _load_existing_pets(self):
        pets_info = []
        for filename in os.listdir("."):
            if filename.lower().endswith("_state.json"):
                try:
                    with open(filename, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    name = data.get("name", filename.replace("_state.json", ""))
                    mood = data.get("mood", "unknown")
                    pets_info.append((name, mood))
                except Exception:
                    # skip corrupted
                    continue
        return pets_info

    # ---------------- Name flow → build main UI ----------------

    def _on_name_enter(self):
        new_name = self.name_entry.get().strip()
        if new_name:
            self.pet.name = new_name
            state_file = f"{self.pet.name}_state.json"
            if os.path.exists(state_file):
                self.pet.load_state(state_file)

        # Clear intro widgets
        for w in list(self.winfo_children()):
            w.destroy()

        # Build main UI
        self._build_main_ui()
        self._refresh_status()
        # Start tick loop
        self.after(self.tick_ms, self._on_tick)

    def _build_main_ui(self):
        # Canvas with background + centered pet sprite
        self.canvas = tk.Canvas(self, width=300, height=300, highlightthickness=0)
        self.canvas.pack(pady=10)

        self._place_pet_sprite()  # uses current mood

        # Pet name
        tk.Label(self, text=self.pet.name, font=("Comic Sans MS", 24)).pack(pady=5)

        # Status message
        self.refs["status_message"] = tk.Label(self, text="", justify=tk.CENTER, font=("Comic Sans MS", 20))
        self.refs["status_message"].pack()

        # Status grid
        status_frame = tk.Frame(self, bg="#fffaf0", bd=3, relief="ridge")
        status_frame.pack(pady=10)

        labels = [
            ("hunger", "Hunger"), ("energy", "Energy"), ("happiness", "Happiness"), ("health", "Health"),
            ("intelligence", "Intelligence"), ("creativity", "Creativity"), ("weather_affinity", "Weather Affinity"),
            ("mood", "Mood")
        ]
        # two columns
        for i, (key, title) in enumerate(labels[:4]):
            tk.Label(status_frame, text=title, font=("Arial", 16), bg="#fffaf0")\
              .grid(row=i, column=0, padx=6, sticky="e")
            lbl = tk.Label(status_frame, text="", font=("Comic Sans MS", 14), bg="#fffaf0", width=18, anchor="w")
            lbl.grid(row=i, column=1, padx=6, pady=2, sticky="w")
            self.refs["status_labels"][key] = lbl

        for i, (key, title) in enumerate(labels[4:]):
            tk.Label(status_frame, text=title, font=("Arial", 16), bg="#fffaf0")\
              .grid(row=i, column=2, padx=6, sticky="e")
            lbl = tk.Label(status_frame, text="", font=("Comic Sans MS", 14), bg="#fffaf0", width=18, anchor="w")
            lbl.grid(row=i, column=3, padx=6, pady=2, sticky="w")
            self.refs["status_labels"][key] = lbl

        # Action buttons with images (optional if files exist)
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=16)
        self.refs["buttons"] = []

        def _mkbtn(img_path, text, cmd):
            try:
                img = Image.open(img_path).resize((70, 70), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.refs["images"][text] = photo
                btn = tk.Button(btn_frame, image=photo, text=text, compound="left",
                                font=("Comic Sans MS", 16, "bold"), command=cmd, bg="pink")
            except Exception:
                btn = tk.Button(btn_frame, text=text, font=("Comic Sans MS", 16, "bold"),
                                command=cmd, bg="pink", width=10)
            btn.pack(side="left", padx=10)
            self.refs["buttons"].append(btn)

        _mkbtn("Images/orange.png", "FEED", self._on_feed)
        _mkbtn("Images/play.png", "PLAY", self._on_play)
        _mkbtn("Images/sleep.png", "SLEEP", self._on_sleep)
        _mkbtn("Images/bath.png", "BATH", self._on_bath)

        # Reset button bottom-right
        try:
            reset_img = Image.open("Images/reset.png").resize((70, 70), Image.LANCZOS)
            reset_photo = ImageTk.PhotoImage(reset_img)
            self.refs["images"]["RESET"] = reset_photo
            reset_btn = tk.Button(self, image=reset_photo, command=self._on_reset)
        except Exception:
            reset_btn = tk.Button(self, text="RESET", command=self._on_reset, width=8)
        reset_btn.place(relx=1.0, rely=1.0, x=-90, y=-90, anchor="se")
        self.refs["reset_btn"] = reset_btn

    def _mood_to_sprite_path(self):
        # Align with pet.calculate_mood() labels
        mood = self.pet.mood
        mapping = {
            "KIMOJI!!": "Images/petImage/mood/kimoji.png",
            "Happy Happy Happy": "Images/petImage/mood/happy.png",
            "sad": "Images/petImage/mood/bored.png",
            "Emo": "Images/petImage/mood/emo.png",
        }
        return mapping.get(mood, "Images/petImage/mood/happy.png")

    def _place_pet_sprite(self):
        # choose sprite by current mood
        try:
            img = Image.open(self._mood_to_sprite_path()).resize((150, 150), Image.LANCZOS)
        except Exception:
            img = Image.new("RGBA", (150, 150), (180, 180, 180, 255))
        photo = ImageTk.PhotoImage(img)
        self.refs["images"]["pet"] = photo
        lbl = tk.Label(self.canvas, image=photo, bd=0, highlightthickness=0)
        self.refs["pet_img_label"] = lbl
        self.canvas.create_window(150, 150, window=lbl)

    def _show_pet_by_mood(self):
        # refresh pet sprite only
        try:
            img = Image.open(self._mood_to_sprite_path()).resize((150, 150), Image.LANCZOS)
        except Exception:
            img = Image.new("RGBA", (150, 150), (180, 180, 180, 255))
        photo = ImageTk.PhotoImage(img)
        self.refs["images"]["pet"] = photo
        self.refs["pet_img_label"].config(image=photo)
        self.refs["pet_img_label"].image = photo

    # ---------------- UI Effects ----------------

    def _flash_label(self, label, flashes=6, delay=100):
        def toggle(n, cur="red"):
            if n <= 0:
                label.config(fg="red")
                return
            nxt = "white" if cur == "red" else "red"
            label.config(fg=nxt)
            label.after(delay, lambda: toggle(n - 1, nxt))
        toggle(flashes)

    def _disable_buttons(self):
        for b in self.refs.get("buttons", []):
            b.config(state="disabled")

    def _enable_buttons(self):
        for b in self.refs.get("buttons", []):
            b.config(state="normal")

    # ---------------- Actions ----------------

    def _after_action_common(self, message, is_warning, action_name):
        self.pet.save_state()  # root-level atomic save
        log_interaction(action_name, action_name, self.pet.get_state())
        self._refresh_status()
        color = "red" if is_warning else "black"
        self.refs["status_message"].config(text=message, fg=color)
        if is_warning:
            self._flash_label(self.refs["status_message"])

    def _on_feed(self):
        msg, warn = self.pet.perform_action("feed")
        if not warn:
            self._disable_buttons()
            self._paused_until = time.time() + 1.5
            frames = []
            for p in ("Images/petImage/feed/feed1.png",
                      "Images/petImage/feed/feed2.png",
                      "Images/petImage/feed/feed3.png"):
                try:
                    frames.append(ImageTk.PhotoImage(Image.open(p).resize((150, 150), Image.LANCZOS)))
                except Exception:
                    pass
            self.refs["frames"]["feed"] = frames

            def animate(i=0):
                if i >= len(frames):
                    self.after(500, lambda: [self._show_pet_by_mood(), self._enable_buttons()])
                    return
                fr = frames[i]
                self.refs["pet_img_label"].config(image=fr); self.refs["pet_img_label"].image = fr
                self.after(500, animate, i + 1)
            if frames:
                animate()
            else:
                self._show_pet_by_mood()
                self._enable_buttons()

        self._after_action_common(msg, warn, "feed")

    def _on_play(self):
        msg, warn = self.pet.perform_action("play")
        if not warn:
            self._disable_buttons()
            # animated GIF
            frames = []
            self._paused_until = time.time() + 2.5
            try:
                gif = Image.open("Images/petImage/play/oiiaioiiai.gif")
                frames = [ImageTk.PhotoImage(f.resize((150, 150), Image.LANCZOS)) for f in ImageSequence.Iterator(gif)]
            except Exception:
                pass
            self.refs["frames"]["play"] = frames

            def animate(i=0, total_ms=2500, frame_ms=100):
                if not frames or i * frame_ms >= total_ms:
                    self._show_pet_by_mood()
                    self._enable_buttons()
                    return
                fr = frames[i % len(frames)]
                self.refs["pet_img_label"].config(image=fr); self.refs["pet_img_label"].image = fr
                self.after(frame_ms, animate, i + 1, total_ms, frame_ms)
            animate()

        self._after_action_common(msg, warn, "play")

    def _on_sleep(self):
        msg, warn = self.pet.perform_action("sleep")
        self._disable_buttons()
        if not warn:
            frames = []
            self._paused_until = time.time() + 3.0
            for p in ("Images/petImage/sleep/sleep2.png", "Images/petImage/sleep/sleep3.png"):
                try:
                    frames.append(ImageTk.PhotoImage(Image.open(p).resize((150, 150), Image.LANCZOS)))
                except Exception:
                    pass
            self.refs["frames"]["sleep"] = frames
            # first pose
            try:
                img1 = Image.open("Images/petImage/sleep/sleep1.png").resize((150, 150), Image.LANCZOS)
                ph1 = ImageTk.PhotoImage(img1)
                self.refs["images"]["sleep1"] = ph1
                self.refs["pet_img_label"].config(image=ph1); self.refs["pet_img_label"].image = ph1
            except Exception:
                pass

            def animate(counter=0):
                if frames:
                    fr = frames[counter % len(frames)]
                    self.refs["pet_img_label"].config(image=fr); self.refs["pet_img_label"].image = fr
                if counter < 4:
                    self.after(750, animate, counter + 1)
                else:
                    # wake
                    try:
                        wake = Image.open("Images/petImage/sleep/wake.png").resize((150, 150), Image.LANCZOS)
                        phw = ImageTk.PhotoImage(wake)
                        self.refs["images"]["wake"] = phw
                        self.refs["pet_img_label"].config(image=phw); self.refs["pet_img_label"].image = phw
                    except Exception:
                        pass
                    self.after(1000, lambda: [self._show_pet_by_mood(), self._enable_buttons()])
            self.after(500, animate)
        else:
            self._enable_buttons()

        self._after_action_common(msg, warn, "sleep")

    def _on_bath(self):
        msg, warn = self.pet.perform_action("bath")
        if not warn:
            self._disable_buttons()
            self._paused_until = time.time() + 1.5
            frames = []
            for p in ("Images/petImage/bath/bath1.png",
                      "Images/petImage/bath/bath2.png",
                      "Images/petImage/bath/bath3.png"):
                try:
                    frames.append(ImageTk.PhotoImage(Image.open(p).resize((150, 150), Image.LANCZOS)))
                except Exception:
                    pass
            self.refs["frames"]["bath"] = frames

            def animate(i=0):
                if i >= len(frames):
                    self.after(500, lambda: [self._show_pet_by_mood(), self._enable_buttons()])
                    return
                fr = frames[i]
                self.refs["pet_img_label"].config(image=fr); self.refs["pet_img_label"].image = fr
                self.after(500, animate, i + 1)
            if frames:
                animate()
            else:
                self._show_pet_by_mood()
                self._enable_buttons()

        self._after_action_common(msg, warn, "bath")

    def _on_reset(self):
        msg, warn = self.pet.perform_action("reset")  # returns tuple in new pet.py
        self._show_pet_by_mood()
        self._refresh_status()
        self.pet.save_state()
        self.refs["status_message"].config(text=msg, fg="black")

    # ---------------- Status & Tick ----------------

    def _refresh_status(self):
        s = self.pet.get_state()
        for key, lbl in self.refs["status_labels"].items():
            lbl.config(text=str(s.get(key, "N/A")))

    def _on_tick(self):
        if time.time() < self._paused_until:
            self._refresh_status()
            self.after(self.tick_ms, self._on_tick)
            return
        # otherwise do normal tick()
        self.pet.tick()
        self._refresh_status()
        self.after(self.tick_ms, self._on_tick)

    # ---------------- Runner ----------------
    def run(self):
        self.mainloop()
