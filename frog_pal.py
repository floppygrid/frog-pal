"""
FrogPal — transparent pixel-art desktop frog with water reminders.

macOS  → PyObjC  (native NSWindow, true per-pixel transparency, no chrome)
Windows/Linux → tkinter fallback

Reminders: every 2 hours from 6 am to 10 pm
           → speech bubble pops up from the frog + cute ribbit sound
"""

import platform
import sys
import threading
import time
import random
import datetime
import math
import wave
import struct
import tempfile
import subprocess
import os

OS = platform.system()

# ── Reminder schedule ─────────────────────────────────────────────────────────
# Fires at these hours (24h): 6,8,10,12,14,16,18,20,22
REMINDER_HOURS = {6, 8, 10, 12, 14, 16, 18, 20, 22}

# ── Pixel art config ──────────────────────────────────────────────────────────
PIXEL_SIZE   = 6
COLS, ROWS   = 16, 16
WIN_W = COLS * PIXEL_SIZE
WIN_H = ROWS * PIXEL_SIZE
IDLE_FPS     = 8
BOB_PERIOD   = 24

# ── Colour palette ─────────────────────────────────────────────────────────────
PALETTE = {
    0: None,
    1: (45,  106, 45),
    2: (76,  175, 80),
    3: (129, 199, 132),
    4: (27,  94,  32),
    5: (255, 255, 255),
    6: (33,  33,  33),
    7: (244, 143, 177),
}

# ── Sprites ───────────────────────────────────────────────────────────────────
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
    [0,0,1,1,1,1,1,0,0,1,1,1,1,1,0,0],
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
    [1,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
    [1,2,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
    [0,1,1,2,2,2,2,2,2,2,2,2,2,1,2,1],
    [0,0,1,1,1,2,2,2,2,2,1,1,1,2,2,1],
    [0,0,0,0,1,2,2,2,2,2,1,0,0,1,2,1],
    [0,0,0,0,0,1,1,1,1,1,0,0,0,0,1,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]

WATER_MSGS = [
    "Ribbit! 💧 Time to drink water!",
    "Hey bestie, HYDRATE NOW! 🐸",
    "Splash splash~ drink some water!",
    "Your frog demands H2O! 💦",
    "Don't forget your water~ 🌊",
    "Leap into hydration! Drink up! 💧",
    "Croaking because you need water! 🐸",
    "Ribbit ribbit = drink water! 🫧",
]


# ── Ribbit sound (generated, no external files needed) ────────────────────────
_RIBBIT_PATH = None

def _make_ribbit_wav():
    """Synthesise a cute two-chirp ribbit and save to a temp WAV file."""
    sr = 44100
    out = []

    def chirp(freq_start, freq_end, dur, vol=0.6):
        n = int(sr * dur)
        for i in range(n):
            t   = i / sr
            pct = i / n
            freq = freq_start + (freq_end - freq_start) * pct
            env  = math.sin(math.pi * pct) ** 0.5   # smooth bell envelope
            out.append(env * vol * math.sin(2 * math.pi * freq * t))

    def silence(dur):
        out.extend([0.0] * int(sr * dur))

    # First chirp: rising then falling
    chirp(600, 950, 0.08)
    chirp(950, 700, 0.06)
    silence(0.05)
    # Second chirp: slightly higher, shorter
    chirp(700, 1050, 0.07)
    chirp(1050, 750, 0.05)
    silence(0.1)

    path = tempfile.mktemp(suffix=".wav")
    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        for s in out:
            clamped = max(-1.0, min(1.0, s))
            f.writeframes(struct.pack("<h", int(clamped * 32767)))
    return path

def play_ribbit():
    global _RIBBIT_PATH
    if _RIBBIT_PATH is None:
        _RIBBIT_PATH = _make_ribbit_wav()
    try:
        if OS == "Darwin":
            subprocess.Popen(["afplay", _RIBBIT_PATH])
        elif OS == "Windows":
            import winsound
            winsound.PlaySound(_RIBBIT_PATH, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            subprocess.Popen(["aplay", _RIBBIT_PATH])
    except Exception:
        pass


# ── Notification ──────────────────────────────────────────────────────────────
def send_notification(title, message):
    if OS == "Darwin":
        subprocess.Popen([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}"'
        ])
    else:
        try:
            from plyer import notification as pn
            pn.notify(title=title, message=message, timeout=8)
        except Exception:
            print(f"\n🐸 {title}: {message}\n")


# ── Reminder schedule helper ──────────────────────────────────────────────────
def _should_remind(last_reminded_hour):
    now = datetime.datetime.now()
    h, m = now.hour, now.minute
    return h in REMINDER_HOURS and m == 0 and h != last_reminded_hour


# ══════════════════════════════════════════════════════════════════════════════
#  macOS backend — PyObjC
# ══════════════════════════════════════════════════════════════════════════════
if OS == "Darwin":
    import objc
    from AppKit import (
        NSApplication, NSApp, NSWindow, NSView, NSColor,
        NSBezierPath, NSFont, NSString,
        NSWindowStyleMaskBorderless, NSBackingStoreBuffered,
        NSFloatingWindowLevel, NSApplicationActivationPolicyAccessory,
        NSMenu, NSMenuItem,
        NSMutableParagraphStyle,
        NSCenterTextAlignment,
        NSForegroundColorAttributeName,
        NSFontAttributeName,
        NSParagraphStyleAttributeName,
    )
    from Foundation import (
        NSObject, NSTimer, NSMakeRect, NSMakePoint,
        NSAttributedString,
    )

    # ── Speech bubble window ──────────────────────────────────────────────────
    class BubbleView(NSView):
        def initWithMessage_(self, msg):
            frame = NSMakeRect(0, 0, 220, 70)
            self = objc.super(BubbleView, self).initWithFrame_(frame)
            self._msg = msg
            return self

        def isOpaque(self): return False

        def drawRect_(self, dirty):
            NSColor.clearColor().set()
            NSBezierPath.fillRect_(self.bounds())

            # Bubble body
            w, h_body = 220, 58
            radius = 12.0
            path = NSBezierPath.bezierPath()
            path.moveToPoint_(NSMakePoint(radius, h_body))
            path.lineToPoint_(NSMakePoint(w - radius, h_body))
            path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
                NSMakePoint(w - radius, h_body - radius), radius, 90, 0)
            path.lineToPoint_(NSMakePoint(w, radius))
            path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
                NSMakePoint(w - radius, radius), radius, 0, 270)
            path.lineToPoint_(NSMakePoint(radius, 0))
            path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
                NSMakePoint(radius, radius), radius, 270, 180)
            path.lineToPoint_(NSMakePoint(0, h_body - radius))
            path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
                NSMakePoint(radius, h_body - radius), radius, 180, 90)
            path.closePath()

            # Tail (triangle pointing down toward frog)
            tail = NSBezierPath.bezierPath()
            cx = w / 2
            tail.moveToPoint_(NSMakePoint(cx - 8, 0))
            tail.lineToPoint_(NSMakePoint(cx + 8, 0))
            tail.lineToPoint_(NSMakePoint(cx, -10))
            tail.closePath()

            NSColor.colorWithCalibratedRed_green_blue_alpha_(
                0.18, 0.62, 0.22, 0.93).set()
            path.fill()
            tail.fill()

            # Outline
            NSColor.colorWithCalibratedRed_green_blue_alpha_(
                0.1, 0.4, 0.1, 1.0).set()
            path.setLineWidth_(1.5)
            path.stroke()

            # Text
            para = NSMutableParagraphStyle.alloc().init()
            para.setAlignment_(NSCenterTextAlignment)
            attrs = {
                NSForegroundColorAttributeName: NSColor.whiteColor(),
                NSFontAttributeName: NSFont.boldSystemFontOfSize_(11),
                NSParagraphStyleAttributeName: para,
            }
            rect = NSMakeRect(8, 8, 204, 46)
            self._msg.drawInRect_withAttributes_(rect, attrs)

    class BubbleWindow(NSWindow):
        @classmethod
        def showMessage_nearFrogWindow_(cls, msg, frog_win):
            fw = frog_win.frame()
            bw_w, bw_h = 220, 80
            # Position bubble above the frog
            bx = fw.origin.x + fw.size.width / 2 - bw_w / 2
            by = fw.origin.y + fw.size.height + 6

            win = cls.alloc().initWithContentRect_styleMask_backing_defer_(
                NSMakeRect(bx, by, bw_w, bw_h),
                NSWindowStyleMaskBorderless,
                NSBackingStoreBuffered,
                False,
            )
            win.setBackgroundColor_(NSColor.clearColor())
            win.setOpaque_(False)
            win.setHasShadow_(False)
            win.setLevel_(NSFloatingWindowLevel)
            win.setIgnoresMouseEvents_(True)

            view = BubbleView.alloc().initWithMessage_(msg)
            win.setContentView_(view)
            win.makeKeyAndOrderFront_(None)

            # Auto-close after 5 seconds
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                5.0, win, "close", None, False
            )
            return win

    # ── Frog view ─────────────────────────────────────────────────────────────
    class FrogView(NSView):
        def initWithFrame_(self, frame):
            self = objc.super(FrogView, self).initWithFrame_(frame)
            if self is None: return None
            self._frame_count  = 0
            self._blink_cd     = random.randint(60, 120)
            self._blinking     = False
            self._blink_frames = 0
            self._waving       = False
            self._wave_frames  = 0
            self._did_drag     = False
            self._frog_win     = None   # set after window creation
            return self

        def isOpaque(self): return False
        def wantsDefaultClipping(self): return False

        def drawRect_(self, dirty):
            NSColor.clearColor().set()
            NSBezierPath.fillRect_(self.bounds())

            self._frame_count += 1
            bob = int(2 * (0.5 - abs((self._frame_count % BOB_PERIOD) /
                                      BOB_PERIOD - 0.5)) * 2)

            if self._waving:
                sprite = FROG_WAVE
                self._wave_frames -= 1
                if self._wave_frames <= 0:
                    self._waving = False
            elif self._blinking:
                sprite = FROG_BLINK
                self._blink_frames -= 1
                if self._blink_frames <= 0:
                    self._blinking = False
                    self._blink_cd = random.randint(60, 120)
            else:
                sprite = FROG_IDLE
                self._blink_cd -= 1
                if self._blink_cd <= 0:
                    self._blinking     = True
                    self._blink_frames = 4

            for row in range(ROWS):
                for col in range(COLS):
                    cid = sprite[row][col]
                    if cid == 0: continue
                    r, g, b = PALETTE[cid]
                    NSColor.colorWithCalibratedRed_green_blue_alpha_(
                        r/255, g/255, b/255, 1.0).set()
                    flipped = (ROWS - 1 - row)
                    NSBezierPath.fillRect_(NSMakeRect(
                        col * PIXEL_SIZE,
                        flipped * PIXEL_SIZE + bob,
                        PIXEL_SIZE, PIXEL_SIZE,
                    ))

        def tick_(self, timer):
            self.setNeedsDisplay_(True)

        def mouseDown_(self, event):
            self._drag_start = event.locationInWindow()
            self._did_drag   = False

        def mouseDragged_(self, event):
            self._did_drag = True
            loc   = event.locationInWindow()
            frame = self.window().frame()
            dx = loc.x - self._drag_start.x
            dy = loc.y - self._drag_start.y
            self.window().setFrameOrigin_(
                NSMakePoint(frame.origin.x + dx, frame.origin.y + dy))

        def mouseUp_(self, event):
            if not self._did_drag:
                self.triggerWave()

        def rightMouseDown_(self, event):
            menu = NSMenu.alloc().initWithTitle_("FrogPal")
            for title, sel in [
                ("Wave! 🐸",          "waveAction:"),
                (None, None),
                ("Remind me now 💧",  "remindAction:"),
                ("Quit",              "quitAction:"),
            ]:
                if title is None:
                    menu.addItem_(NSMenuItem.separatorItem())
                else:
                    item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                        title, sel, "")
                    item.setTarget_(self)
                    menu.addItem_(item)
            NSMenu.popUpContextMenu_withEvent_forView_(menu, event, self)

        def triggerWave(self):
            if not self._waving:
                self._waving      = True
                self._wave_frames = IDLE_FPS * 2

        def showBubble_(self, msg):
            if self._frog_win:
                BubbleWindow.showMessage_nearFrogWindow_(msg, self._frog_win)

        def waveAction_(self, sender):   self.triggerWave()
        def remindAction_(self, sender): self._do_remind()
        def quitAction_(self, sender):   NSApp.terminate_(None)

        def _do_remind(self):
            msg = random.choice(WATER_MSGS)
            self.triggerWave()
            play_ribbit()
            self.showBubble_(msg)
            send_notification("FrogPal 🐸", msg)

        def remindFromThread(self):
            """Called safely from the background thread via performSelectorOnMainThread."""
            self._do_remind()

    def run_macos():
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

        win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(100, 600, WIN_W, WIN_H),
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False,
        )
        win.setBackgroundColor_(NSColor.clearColor())
        win.setOpaque_(False)
        win.setHasShadow_(False)
        win.setLevel_(NSFloatingWindowLevel)
        win.setCollectionBehavior_(1 << 3 | 1 << 6)
        win.setIgnoresMouseEvents_(False)
        win.setAcceptsMouseMovedEvents_(True)

        view = FrogView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, WIN_H))
        view._frog_win = win
        win.setContentView_(view)
        win.makeKeyAndOrderFront_(None)

        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0 / IDLE_FPS, view, "tick:", None, True
        )

        # Pre-generate the ribbit sound in background
        threading.Thread(target=lambda: play_ribbit(), daemon=True).start()

        def reminder_loop():
            last_hour = -1
            while True:
                now = datetime.datetime.now()
                h, m = now.hour, now.minute
                if h in REMINDER_HOURS and m == 0 and h != last_hour:
                    last_hour = h
                    # Must call UI stuff on main thread
                    view.performSelectorOnMainThread_withObject_waitUntilDone_(
                        "remindFromThread", None, False
                    )
                time.sleep(30)  # check every 30 seconds

        threading.Thread(target=reminder_loop, daemon=True).start()
        app.run()


# ══════════════════════════════════════════════════════════════════════════════
#  Windows / Linux backend — tkinter
# ══════════════════════════════════════════════════════════════════════════════
else:
    import tkinter as tk

    TRANSPARENT_COLOR = "#010101"

    def _hex(pid):
        if pid == 0: return TRANSPARENT_COLOR
        r, g, b = PALETTE[pid]
        return f"#{r:02x}{g:02x}{b:02x}"

    def draw_sprite(canvas, sprite, offset_y=0):
        canvas.delete("sprite")
        for row in range(ROWS):
            for col in range(COLS):
                cid = sprite[row][col]
                if cid == 0: continue
                x0 = col * PIXEL_SIZE
                y0 = row * PIXEL_SIZE + offset_y
                canvas.create_rectangle(
                    x0, y0, x0+PIXEL_SIZE, y0+PIXEL_SIZE,
                    fill=_hex(cid), outline="", tags="sprite")

    class BubbleTk(tk.Toplevel):
        def __init__(self, parent, msg, frog_x, frog_y):
            super().__init__(parent)
            self.overrideredirect(True)
            self.attributes("-topmost", True)
            self.configure(bg="#2e7d32")
            w, h = 220, 60
            x = frog_x
            y = frog_y - h - 10
            self.geometry(f"{w}x{h}+{x}+{y}")
            tk.Label(self, text=msg, bg="#2e7d32", fg="white",
                     font=("Arial", 10, "bold"), wraplength=200,
                     justify="center").pack(expand=True)
            self.after(5000, self.destroy)

    class FrogPalTk:
        def __init__(self):
            self.root = tk.Tk()
            self.root.overrideredirect(True)
            self.root.attributes("-topmost", True)
            self.root.geometry(f"{WIN_W}x{WIN_H}+100+100")
            self.root.configure(bg=TRANSPARENT_COLOR)
            if OS == "Windows":
                self.root.attributes("-transparentcolor", TRANSPARENT_COLOR)
            else:
                self.root.attributes("-alpha", 0.95)

            self.canvas = tk.Canvas(self.root, width=WIN_W, height=WIN_H,
                bg=TRANSPARENT_COLOR, highlightthickness=0, borderwidth=0)
            self.canvas.pack()

            self._frame    = 0
            self._blink_cd = random.randint(60, 120)
            self._blinking = False
            self._blink_f  = 0
            self._waving   = False
            self._wave_f   = 0

            self.canvas.bind("<ButtonPress-1>",  self._drag_start)
            self.canvas.bind("<B1-Motion>",       self._drag_motion)
            self.canvas.bind("<ButtonRelease-1>", self._drag_end)
            self.canvas.bind("<Button-3>",        self._show_menu)

            self._menu = tk.Menu(self.root, tearoff=0)
            self._menu.add_command(label="Wave! 🐸",         command=self._wave)
            self._menu.add_separator()
            self._menu.add_command(label="Remind me now 💧", command=self._remind)
            self._menu.add_separator()
            self._menu.add_command(label="Quit",              command=self.root.destroy)

            self._animate()
            threading.Thread(target=self._reminder_loop, daemon=True).start()
            # Pre-generate ribbit
            threading.Thread(target=play_ribbit, daemon=True).start()

        def _animate(self):
            self._frame += 1
            bob = int(2 * (0.5 - abs((self._frame % BOB_PERIOD)/BOB_PERIOD - 0.5)) * 2)
            if self._waving:
                sprite = FROG_WAVE
                self._wave_f -= 1
                if self._wave_f <= 0: self._waving = False
            elif self._blinking:
                sprite = FROG_BLINK
                self._blink_f -= 1
                if self._blink_f <= 0:
                    self._blinking = False
                    self._blink_cd = random.randint(60, 120)
            else:
                sprite = FROG_IDLE
                self._blink_cd -= 1
                if self._blink_cd <= 0:
                    self._blinking = True
                    self._blink_f  = 4
            draw_sprite(self.canvas, sprite, bob)
            self.root.after(1000 // IDLE_FPS, self._animate)

        def _drag_start(self, e):
            self._dx = e.x_root - self.root.winfo_x()
            self._dy = e.y_root - self.root.winfo_y()
            self._did_drag = False

        def _drag_motion(self, e):
            self._did_drag = True
            self.root.geometry(f"+{e.x_root-self._dx}+{e.y_root-self._dy}")

        def _drag_end(self, e):
            if not self._did_drag: self._wave()

        def _show_menu(self, e):
            try: self._menu.tk_popup(e.x_root, e.y_root)
            finally: self._menu.grab_release()

        def _wave(self):
            self._waving = True
            self._wave_f = IDLE_FPS * 2

        def _remind(self):
            msg = random.choice(WATER_MSGS)
            self._wave()
            play_ribbit()
            fx = self.root.winfo_x()
            fy = self.root.winfo_y()
            BubbleTk(self.root, msg, fx, fy)
            send_notification("FrogPal 🐸", msg)

        def _reminder_loop(self):
            last_hour = -1
            while True:
                now = datetime.datetime.now()
                h, m = now.hour, now.minute
                if h in REMINDER_HOURS and m == 0 and h != last_hour:
                    last_hour = h
                    self.root.after(0, self._remind)
                time.sleep(30)

        def run(self):
            self.root.mainloop()


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if OS == "Darwin":
        run_macos()
    else:
        FrogPalTk().run()
