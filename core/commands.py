import os
import subprocess
from rapidfuzz import process
from config import COMMANDS, CONFIDENCE_THRESHOLD


def match_command(text):
    if not text:
        return None, 0

    match, score, _ = process.extractOne(text, COMMANDS)
    if score >= CONFIDENCE_THRESHOLD:
        return match, score

    return None, score


def execute_command(cmd):
    if cmd == "open chrome":
        subprocess.Popen(["google-chrome"])

    elif cmd == "open vscode":
        subprocess.Popen(["code"])

    elif cmd == "open terminal":
        subprocess.Popen(["gnome-terminal"])

    elif cmd == "open downloads":
        subprocess.Popen(["xdg-open", "~/Downloads"])

    elif cmd == "volume up":
        os.system("pactl set-sink-volume @DEFAULT_SINK@ +5%")

    elif cmd == "volume down":
        os.system("pactl set-sink-volume @DEFAULT_SINK@ -5%")