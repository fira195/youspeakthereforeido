from core.commands import match_command, execute_command
from core.tts import speak

last_partial = ""
last_final = ""


def handle_partial(text, ui_update):
    global last_partial
    last_partial = text
    ui_update("partial", text)


def handle_final(text, ui_update):
    global last_final
    last_final = text

    ui_update("final", text)

    cmd, score = match_command(text)

    if cmd:
        ui_update("command", cmd)
        execute_command(cmd)
        speak(cmd)