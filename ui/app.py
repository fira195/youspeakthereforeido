import tkinter as tk
from tkinter import scrolledtext
from audio.stream import is_listening


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Assistant")
        self.root.geometry("900x500")
        self.root.configure(bg="#0b0f14")

        self.root.bind("<KeyPress-space>", self.start)
        self.root.bind("<KeyRelease-space>", self.stop)
        self.root.focus_set()

        self.log = scrolledtext.ScrolledText(root, bg="#000", fg="#00ff9c")
        self.log.pack(side="left", fill="both", expand=True)

        right = tk.Frame(root, bg="#0b0f14")
        right.pack(side="right", fill="both", expand=True)

        self.status = tk.Label(right, text="Idle", bg="#0b0f14", fg="#00d4ff")
        self.status.pack()

        self.partial = tk.Label(right, text="", bg="#0b0f14", fg="#ffd000")
        self.partial.pack()

        self.final = tk.Label(right, text="", bg="#0b0f14", fg="white")
        self.final.pack()

        self.command = tk.Label(right, text="", bg="#0b0f14", fg="#00ff9c")
        self.command.pack()

        self.update_loop()

    def log_msg(self, msg):
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)

    def update(self, type_, value):
        if type_ == "partial":
            self.partial.config(text=value)

        elif type_ == "final":
            self.final.config(text=value)

        elif type_ == "command":
            self.command.config(text=value)

    def update_loop(self):
        self.root.after(10, self.update_loop)

    def start(self, e):
        import audio.stream
        audio.stream.is_listening = True
        self.status.config(text="Listening")
        self.log_msg("[START]")

    def stop(self, e):
        import audio.stream
        audio.stream.is_listening = False
        self.status.config(text="Idle")
        self.log_msg("[STOP]")