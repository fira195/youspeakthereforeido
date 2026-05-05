import json
import queue
import threading
import tkinter as tk
from tkinter import scrolledtext
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import numpy as np
import os
import asyncio
import edge_tts
from rapidfuzz import process, fuzz

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

# ---------------- TTS (EDGE FIXED) ----------------
async def _speak_async(text):
    voice = "en-US-AriaNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("voice.mp3")
    os.system("mpg123 -q voice.mp3")

def speak(text):
    threading.Thread(
        target=lambda: asyncio.run(_speak_async(text)),
        daemon=True
    ).start()

# ---------------- AUDIO DEVICE ----------------
device_info = sd.query_devices(kind="input")
DEVICE_ID = sd.default.device[0]
SAMPLE_RATE = int(device_info["default_samplerate"])

log("SYSTEM", f"Device {DEVICE_ID} @ {SAMPLE_RATE}")

# ---------------- VOSK ----------------
MODEL_PATH = "vosk-model-small-en-us-0.15"
model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, SAMPLE_RATE)

# ---------------- STATE ----------------
running = False

# ---------------- COMMAND SET ----------------
COMMANDS = {
    "open chrome": ("app", "google-chrome"),
    "open vscode": ("app", "code"),
    "open terminal": ("app", "gnome-terminal"),
    "open downloads": ("file", "~/Downloads"),
    "volume up": ("vol", "up"),
    "volume down": ("vol", "down"),
}

# ---------------- FUZZY ROUTER (FIX) ----------------
def route(text):
    text = text.lower().strip()

    best = process.extractOne(
        text,
        COMMANDS.keys(),
        scorer=fuzz.WRatio
    )

    if best and best[1] > 70:
        return COMMANDS[best[0]]

    return ("unknown", None)

# ---------------- EXEC ----------------
def execute(action_type, value):
    if action_type == "app":
        os.system(f"{value} &")
        speak(f"Opening {value}")

    elif action_type == "file":
        os.system(f"xdg-open {os.path.expanduser(value)} &")
        speak("Opening folder")

    elif action_type == "vol":
        os.system(f"amixer -q sset Master {'5%+' if value=='up' else '5%-'}")
        speak("Done")

    else:
        speak("I didn't understand that")

# ---------------- AUDIO LOOP ----------------
def listen_loop():
    global running

    status("Listening...")
    log("SYSTEM", "Audio started")

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

            if recognizer.AcceptWaveform(audio.tobytes()):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()

                log("VOSK", f"heard: {text}")

                if text:
                    cmd(text)

                    act, val = route(text)
                    action(f"{act} {val}")

                    execute(act, val)

    status("Idle")

# ---------------- UI ----------------
def toggle():
    global running
    if not running:
        running = True
        threading.Thread(target=listen_loop, daemon=True).start()
        btn.config(text="Stop", bg="red")
    else:
        running = False
        btn.config(text="Start", bg="green")

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

    root.after(100, poll)

# ---------------- UI ----------------
root = tk.Tk()
root.title("Voice Assistant Pro")
root.geometry("900x600")
root.configure(bg="#0d1117")

left = tk.Frame(root, bg="#0d1117")
left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

right = tk.Frame(root, bg="#0d1117")
right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

box = scrolledtext.ScrolledText(left, bg="#000", fg="#00ff88")
box.pack(fill=tk.BOTH, expand=True)

status_lbl = tk.Label(right, text="Idle", fg="white", bg="#0d1117", font=("Arial", 16))
status_lbl.pack(pady=10)

cmd_lbl = tk.Label(right, text="", fg="#00d4ff", bg="#0d1117")
cmd_lbl.pack(pady=10)

action_lbl = tk.Label(right, text="", fg="#ffcc00", bg="#0d1117")
action_lbl.pack(pady=10)

btn = tk.Button(
    right,
    text="Start",
    command=toggle,
    bg="green",
    fg="white",
    font=("Arial", 14),
    height=2,
    width=20
)
btn.pack(pady=40)

root.after(100, poll)
root.mainloop()