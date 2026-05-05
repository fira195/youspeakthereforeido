import threading
import pyttsx3

_engine = pyttsx3.init()


def speak(text):
    def run():
        _engine.say(text)
        _engine.runAndWait()

    threading.Thread(target=run, daemon=True).start()