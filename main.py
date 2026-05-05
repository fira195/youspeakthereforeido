import tkinter as tk
from vosk import Model
from config import MODEL_PATH
from ui.app import App
from audio.recognizer import init_recognizer
from audio.stream import start_stream


def main():
    model = Model(MODEL_PATH)
    init_recognizer(model)

    root = tk.Tk()
    app = App(root)

    device = None  # or set manually

    def ui_update(type_, value):
        app.update(type_, value)

    start_stream(device, ui_update)

    root.mainloop()


if __name__ == "__main__":
    main()