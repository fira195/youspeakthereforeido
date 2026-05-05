import json
import queue
import threading
import tkinter as tk
from tkinter import scrolledtext
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import numpy as np
import pyttsx3
import os
from rapidfuzz import process, fuzz
import keyboard
import time

# ---------------- UI QUEUE ----------------
ui_queue = queue.Queue()

def log(tag, msg):
    ui_queue.put(("log", f"[{tag}] {msg}"))

def status(msg):
    ui_queue.put(("status", msg))

def cmd(msg):
    ui_queue.put(("cmd", msg))

def action(msg):
    ui_queue.put(("action", msg))


# ---------------- FAST TTS ----------------
engine = pyttsx3.init()
engine.setProperty("rate", 185)

def speak(text):
    def run():
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=run, daemon=True).start()


# ---------------- AUDIO DEVICE ----------------
device_info = sd.query_devices(kind="input")
DEVICE_ID = sd.default.device[0]
SAMPLE_RATE = int(device_info["default_samplerate"])

log("SYSTEM", f"Device {DEVICE_ID} @ {SAMPLE_RATE}")


# ---------------- VOSK ----------------
MODEL_PATH = "vosk-model-small-en-us-0.15"
model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, SAMPLE_RATE)


# ---------------- COMMANDS ----------------
COMMANDS = {
    "open chrome": ("app", "google-chrome"),
    "open vscode": ("app", "code"),
    "open terminal": ("app", "gnome-terminal"),
    "open downloads": ("file", "~/Downloads"),
    "volume up": ("vol", "up"),
    "volume down": ("vol", "down"),
}


def route(text):
    text = text.lower().strip()

    match = process.extractOne(
        text,
        COMMANDS.keys(),
        scorer=fuzz.WRatio
    )

    if match and match[1] > 70:
        return COMMANDS[match[0]]

    return ("unknown", None)


def execute(act, val):
    if act == "app":
        os.system(f"{val} &")
        speak("Opening application")

    elif act == "file":
        os.system(f"xdg-open {os.path.expanduser(val)} &")
        speak("Opening folder")

    elif act == "vol":
        os.system(f"amixer -q sset Master {'5%+' if val=='up' else '5%-'}")
        speak("Done")

    else:
        speak("Command not recognized")


# ---------------- AUDIO LISTENER (SPACE HOLD ONLY) ----------------
running = False


def listen_once():
    global running

    status("Listening (hold SPACE)...")
    log("SYSTEM", "Recording started")

    recognizer.Reset()

    silent_frames = 0

    with sd.InputStream(
        device=DEVICE_ID,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        blocksize=4000,
    ) as stream:

        while running:

            data, overflow = stream.read(4000)
            audio = np.frombuffer(data, dtype=np.int16)

            amp = np.abs(audio).mean()

            # silence detection
            if amp < 200:
                silent_frames += 1
            else:
                silent_frames = 0

            if recognizer.AcceptWaveform(audio.tobytes()):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()

                if text:
                    log("VOSK", f"heard: {text}")
                    cmd(text)

                    act, val = route(text)
                    action(f"{act} {val}")

                    execute(act, val)

            # stop after pause (feels instant)
            if silent_frames > 15:
                break

    status("Idle")
    log("SYSTEM", "Recording stopped")


# ---------------- SPACE CONTROL ----------------
def space_listener():
    global running

    while True:
        keyboard.wait("space")

        if not running:
            running = True
            threading.Thread(target=listen_once, daemon=True).start()

        keyboard.wait("space up")
        running = False


# ---------------- UI ----------------
def poll():
    while not ui_queue.empty():
        t, msg = ui_queue.get()

        if t == "log":
            box.insert(tk.END, msg + "\n")
            box.see(tk.END)

        elif t == "status":
            status_lbl.config(text=msg)

        elif t == "cmd":
            cmd_lbl.config(text=f"You said: {msg}")

        elif t == "action":
            action_lbl.config(text=f"Action: {msg}")

    root.after(50, poll)


# ---------------- UI DESIGN (PRETTY UPGRADE) ----------------
root = tk.Tk()
root.title("Voice Assistant Pro")
root.geometry("1000x650")
root.configure(bg="#0b0f14")

# LEFT PANEL
left = tk.Frame(root, bg="#0b0f14")
left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# RIGHT PANEL
right = tk.Frame(root, bg="#0b0f14")
right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# LOG BOX
box = scrolledtext.ScrolledText(
    left,
    bg="#05080d",
    fg="#00ff99",
    insertbackground="white",
    font=("Consolas", 10)
)
box.pack(fill=tk.BOTH, expand=True)

# STATUS
status_lbl = tk.Label(
    right,
    text="Idle",
    fg="white",
    bg="#0b0f14",
    font=("Helvetica", 18, "bold")
)
status_lbl.pack(pady=20)

cmd_lbl = tk.Label(
    right,
    text="",
    fg="#00d4ff",
    bg="#0b0f14",
    font=("Helvetica", 12)
)
cmd_lbl.pack(pady=10)

action_lbl = tk.Label(
    right,
    text="",
    fg="#ffcc00",
    bg="#0b0f14",
    font=("Helvetica", 12)
)
action_lbl.pack(pady=10)

info = tk.Label(
    right,
    text="Hold SPACE to speak",
    fg="#888",
    bg="#0b0f14",
    font=("Helvetica", 10)
)
info.pack(pady=40)


# ---------------- START THREADS ----------------
threading.Thread(target=space_listener, daemon=True).start()

root.after(50, poll)
root.mainloop()