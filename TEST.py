from PIL import Image, ImageTk, ImageSequence
import tkinter as tk

def animate_gif(label, gif_path):
    frames = []

    # Load and extract frames from GIF
    gif = Image.open(gif_path)
    for frame in ImageSequence.Iterator(gif):
        frame = frame.resize((150, 150), Image.LANCZOS)
        frames.append(ImageTk.PhotoImage(frame))

    def update(index=0):
        label.config(image=frames[index])
        label.image = frames[index]
        root.after(100, update, (index + 1) % len(frames))  # Adjust timing here

    update()

# --- GUI ---
root = tk.Tk()
root.title("GIF Demo")

pet_label = tk.Label(root)
pet_label.pack()

animate_gif(pet_label, "petImage/play/oiiaioiiai.gif")  # <-- your gif path

root.mainloop()
