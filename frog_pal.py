import tkinter as tk
from tkinter import font
import threading
import time
import platform
import random
import sys

try:
    from plyer import notification
    HAS_PLYER = True
except ImportError:
    HAS_PLYER = False

# ── Configuration ──────────────────────────────────────────────────────────────
REMINDER_INTERVAL_MINUTES = 30
PIXEL_SIZE = 4
CANVAS_W = 80
CANVAS_H = 80
TRANSPARENT_COLOR = "systemTransparent"
IDLE_ANIM_FPS = 8
BOB_PERIOD_FRAMES = 24

# ── Pixel art sprites (16×16, 0=transparent) ──────────────────────────────────
COLORS = {
    0: None,           # transparent
    1: "#2d6a2d",      # dark green outline
    2: "#4caf50",      # mid green body
    3: "#81c784",      # light green highlight
    4: "#1b5e20",      # darkest green shadow
    5: "#ffffff",      # white eye
    6: "#212121",      # black pupil
    7: "#f48fb1",      # pink belly / mouth
    8: "#ffeb3b",      # yellow eye shine
}

FROG_IDLE = [
    [0,0,0,1,1,1,0,0,0,0,1,1,1,0,0,0],
    [0,0,1,5,5,5,1,0,0,1,5,5,5,1,0,0],
    [0,0,1,5,6,5,1,0,0,1,5,6,5,1,0,0],
    [0,0,0,1,1,1,0,0,0,0,1,1,1,0,0,0],
    [0,1,1,1,2,2,1,1,1,1,2,2,1,1,1,0],
    [0,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
    [0,1,2,3,2,7,7,7,7,7,7,2,3,2,1,0],
    [0,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
    [0,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
    [0,0,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
    [1,2,1,2,2,2,2,2,2,2,2,2,2,1,2,1],
    [1,2,2,1,1,1,2,2,2,2,1,1,1,2,2,1],
    [1,2,1,0,0,1,2,2,2,2,1,0,0,1,2,1],
    [0,1,0,0,0,0,1,1,1,1,0,0,0,0,1,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]

FROG_BLINK = [
    [0,0,0,1,1,1,0,0,0,0,1,1,1,0,0,0],
    [0,0,1,5,5,5,1,0,0,1,5,5,5,1,0,0],
    [0,0,1,1,1,1,1,0,0,1,1,1,1,1,0,0],  # eyes closed
    [0,0,0,1,1,1,0,0,0,0,1,1,1,0,0,0],
    [0,1,1,1,2,2,1,1,1,1,2,2,1,1,1,0],
    [0,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
    [0,1,2,3,2,7,7,7,7,7,7,2,3,2,1,0],
    [0,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
    [0,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
    [0,0,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
    [1,2,1,2,2,2,2,2,2,2,2,2,2,1,2,1],
    [1,2,2,1,1,1,2,2,2,2,1,1,1,2,2,1],
    [1,2,1,0,0,1,2,2,2,2,1,0,0,1,2,1],
    [0,1,0,0,0,0,1,1,1,1,0,0,0,0,1,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]

FROG_WAVE = [
    [0,0,0,1,1,1,0,0,0,0,1,1,1,0,0,0],
    [0,0,1,5,5,5,1,0,0,1,5,5,5,1,0,0],
    [0,0,1,5,6,5,1,0,0,1,5,6,5,1,0,0],
    [0,0,0,1,1,1,0,0,0,0,1,1,1,0,0,0],
    [0,1,1,1,2,2,1,1,1,1,2,2,1,1,1,0],
    [0,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
    [0,1,2,3,2,7,7,7,7,7,2,3,2,2,1,0],
    [0,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
    [1,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],  # arm raised
    [1,2,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
    [0,1,1,2,2,2,2,2,2,2,2,2,2,1,2,1],
    [0,0,1,1,1,2,2,2,2,2,1,1,1,2,2,1],
    [0,0,0,0,1,2,2,2,2,2,1,0,0,1,2,1],
    [0,0,0,0,0,1,1,1,1,1,0,0,0,0,1,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]

# Notification messages
WATER_MSGS = [
    "Ribbit! 💧 Time to drink water!",
    "Hey! Your frog friend says: HYDRATE!",
    "Splash splash~ Drink some water, friend!",
    "Ribbit ribbit! 🐸 Water time!",
    "Don't forget your H2O! Your frog is watching 👀",
    "Leap into hydration! Drink water now~ 💦",
]


def draw_sprite(canvas, sprite, pixel_size, offset_x=0, offset_y=0):
    canvas.delete("sprite")
    rows = len(sprite)
    cols = len(sprite[0]) if rows else 0
    for r in range(rows):
        for c in range(cols):
            color_id = sprite[r][c]
            if color_id == 0:
                continue
            color = COLORS[color_id]
            x0 = offset_x + c * pixel_size
            y0 = offset_y + r * pixel_size
            x1 = x0 + pixel_size
            y1 = y0 + pixel_size
            canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="", tags="sprite")


def send_notification(title, message):
    if HAS_PLYER:
        try:
            notification.notify(title=title, message=message, timeout=8)
            return
        except Exception:
            pass
    # Fallback: tkinter toplevel popup
    popup = tk.Toplevel()
    popup.title("FrogPal")
    popup.geometry("300x100")
    popup.attributes("-topmost", True)
    lbl = tk.Label(popup, text=message, wraplength=280, justify="center", font=("Arial", 11))
    lbl.pack(expand=True)
    btn = tk.Button(popup, text="Got it! 🐸", command=popup.destroy)
    btn.pack(pady=4)
    popup.after(8000, popup.destroy)


class FrogPal:
    def __init__(self):
        self.root = tk.Tk()
        self._setup_window()
        self._setup_canvas()
        self._setup_drag()
        self._setup_menu()

        self.frame_count = 0
        self.blink_countdown = random.randint(60, 120)
        self.is_blinking = False
        self.blink_frames = 0
        self.is_waving = False
        self.wave_frames = 0
        self.bob_offset = 0

        self._animate()
        self._start_reminder_thread()

    # ── Window setup ──────────────────────────────────────────────────────────

    def _setup_window(self):
        self.root.overrideredirect(True)   # no title bar / frame
        self.root.attributes("-topmost", True)
        self.root.geometry(f"{CANVAS_W}x{CANVAS_H}+100+100")

        os_name = platform.system()
        if os_name == "Darwin":
            # macOS: "systemTransparent" makes the window truly see-through
            self.root.wm_attributes("-transparent", True)
            self.root.configure(bg=TRANSPARENT_COLOR)
        elif os_name == "Windows":
            WIN_CHROMA = "#010101"
            self.root.configure(bg=WIN_CHROMA)
            self.root.attributes("-transparentcolor", WIN_CHROMA)
        else:
            # Linux: needs a compositor; fall back to near-opaque
            self.root.configure(bg="black")
            self.root.attributes("-alpha", 0.95)

    def _setup_canvas(self):
        self.canvas = tk.Canvas(
            self.root,
            width=CANVAS_W,
            height=CANVAS_H,
            bg=TRANSPARENT_COLOR,   # "systemTransparent" on macOS
            highlightthickness=0,
            borderwidth=0,
        )
        self.canvas.pack()

    # ── Drag to move ─────────────────────────────────────────────────────────

    def _setup_drag(self):
        self.canvas.bind("<ButtonPress-1>", self._drag_start)
        self.canvas.bind("<B1-Motion>", self._drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._drag_end)
        self._drag_x = 0
        self._drag_y = 0
        self._dragging = False

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()
        self._dragging = False

    def _drag_motion(self, event):
        self._dragging = True
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _drag_end(self, event):
        if not self._dragging:
            self._trigger_wave()

    # ── Right-click context menu ──────────────────────────────────────────────

    def _setup_menu(self):
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Wave! 🐸", command=self._trigger_wave)
        self.menu.add_separator()
        self.menu.add_command(label="Remind me now 💧", command=self._remind_now)
        self.menu.add_separator()
        self.menu.add_command(label="Quit", command=self.root.destroy)
        self.canvas.bind("<Button-3>", self._show_menu)
        self.canvas.bind("<Button-2>", self._show_menu)  # macOS middle-click fallback

    def _show_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    # ── Animation ─────────────────────────────────────────────────────────────

    def _animate(self):
        self.frame_count += 1
        bob = int(2 * (0.5 - abs((self.frame_count % BOB_PERIOD_FRAMES) / BOB_PERIOD_FRAMES - 0.5)) * 2)
        self.bob_offset = bob

        if self.is_waving:
            sprite = FROG_WAVE
            self.wave_frames -= 1
            if self.wave_frames <= 0:
                self.is_waving = False
        elif self.is_blinking:
            sprite = FROG_BLINK
            self.blink_frames -= 1
            if self.blink_frames <= 0:
                self.is_blinking = False
                self.blink_countdown = random.randint(60, 120)
        else:
            sprite = FROG_IDLE
            self.blink_countdown -= 1
            if self.blink_countdown <= 0:
                self.is_blinking = True
                self.blink_frames = 4

        margin_x = (CANVAS_W - 16 * PIXEL_SIZE) // 2
        margin_y = (CANVAS_H - 16 * PIXEL_SIZE) // 2
        draw_sprite(self.canvas, sprite, PIXEL_SIZE, margin_x, margin_y + bob)

        delay = 1000 // IDLE_ANIM_FPS
        self.root.after(delay, self._animate)

    def _trigger_wave(self):
        if not self.is_waving:
            self.is_waving = True
            self.wave_frames = IDLE_ANIM_FPS * 2

    # ── Water reminders ───────────────────────────────────────────────────────

    def _start_reminder_thread(self):
        t = threading.Thread(target=self._reminder_loop, daemon=True)
        t.start()

    def _reminder_loop(self):
        time.sleep(REMINDER_INTERVAL_MINUTES * 60)
        while True:
            self.root.after(0, self._do_remind)
            time.sleep(REMINDER_INTERVAL_MINUTES * 60)

    def _remind_now(self):
        self.root.after(0, self._do_remind)

    def _do_remind(self):
        msg = random.choice(WATER_MSGS)
        self._trigger_wave()
        send_notification("FrogPal 🐸", msg)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = FrogPal()
    app.run()
