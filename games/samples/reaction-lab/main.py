"""A dependency-free Tkinter reaction game for checking native Python launch."""
import random
import time
import tkinter as tk


class ReactionGame:
    def __init__(self, root):
        self.root = root
        root.title("REACTION LAB — 4Pro Arcade")
        root.geometry("640x470")
        root.minsize(480, 390)
        root.configure(bg="#10151c")
        self.state = "idle"
        self.timer = None
        self.best = None
        self.started = 0
        tk.Label(root, text="4PRO / PYTHON SAMPLE", font=("Consolas", 10), fg="#bc9aff", bg="#10151c").pack(pady=(30, 8))
        tk.Label(root, text="REACTION LAB", font=("Consolas", 27, "bold"), fg="#f0f3f8", bg="#10151c").pack()
        tk.Label(root, text="緑になった瞬間に、クリック / スペース。", font=("Yu Gothic UI", 12), fg="#9ba7b6", bg="#10151c").pack(pady=12)
        self.button = tk.Button(root, text="クリックしてスタート", command=self.click, font=("Yu Gothic UI", 18, "bold"), bg="#292334", fg="#bc9aff", activebackground="#393044", activeforeground="#ffffff", relief="flat", bd=0, cursor="hand2")
        self.button.pack(fill="both", expand=True, padx=40, pady=16)
        self.record = tk.Label(root, text="BEST  —", font=("Consolas", 12), fg="#9ba7b6", bg="#10151c")
        self.record.pack(pady=(4, 26))
        root.bind("<space>", self.space)
        root.protocol("WM_DELETE_WINDOW", self.close)

    def space(self, _event):
        self.click()
        return "break"

    def click(self):
        if self.state == "waiting":
            self.root.after_cancel(self.timer)
            self.timer = None
            self.state = "idle"
            self.button.configure(text="フライング！\nクリックしてもう一度", bg="#422633", fg="#f59fcc")
        elif self.state == "go":
            elapsed = round((time.perf_counter() - self.started) * 1000)
            self.best = elapsed if self.best is None else min(elapsed, self.best)
            self.state = "idle"
            self.button.configure(text=f"{elapsed} ms\nクリックしてもう一度", bg="#292334", fg="#bc9aff")
            self.record.configure(text=f"BEST  {self.best} ms")
        else:
            self.state = "waiting"
            self.button.configure(text="まだ…待って！", bg="#422633", fg="#f59fcc")
            self.timer = self.root.after(random.randint(1500, 4200), self.go)

    def go(self):
        self.timer = None
        self.state = "go"
        self.button.configure(text="今！", bg="#86f7bd", fg="#10251a", activebackground="#a1ffd0")
        self.started = time.perf_counter()

    def close(self):
        if self.timer is not None:
            self.root.after_cancel(self.timer)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    ReactionGame(root)
    root.mainloop()
