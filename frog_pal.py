"""
FrogPal — transparent pixel-art desktop frog with water reminders.

macOS  → PyObjC  (native NSWindow, true per-pixel transparency, no chrome)
Windows/Linux → tkinter fallback
"""

import platform
import sys
import threading
import time
import random

OS = platform.system()

try:
    from plyer import notification
    HAS_PLYER = True
except ImportError:
    HAS_PLYER = False

# ── Shared config ──────────────────────────────────────────────────────────────
REMINDER_INTERVAL_MINUTES = 30
PIXEL_SIZE   = 6          # each "pixel" is this many screen points
COLS, ROWS   = 16, 16     # sprite grid size
WIN_W = COLS * PIXEL_SIZE
WIN_H = ROWS * PIXEL_SIZE
IDLE_FPS     = 8
BOB_PERIOD   = 24         # frames for one bob cycle

# ── Colour palette ─────────────────────────────────────────────────────────────
# (R, G, B) in 0-255
PALETTE = {
    0: None,                    # transparent
    1: (45,  106, 45),          # dark green outline
    2: (76,  175, 80),          # mid green body
    3: (129, 199, 132),         # light green highlight
    4: (27,  94,  32),          # darkest shadow
    5: (255, 255, 255),         # white eye
    6: (33,  33,  33),          # black pupil
    7: (244, 143, 177),         # pink belly / mouth
}

# ── Sprites (16 × 16) ─────────────────────────────────────────────────────────
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
    "Hey! Your frog friend says: HYDRATE!",
    "Splash splash~ Drink some water, friend!",
    "Ribbit ribbit! 🐸 Water time!",
    "Don't forget your H2O! Your frog is watching 👀",
    "Leap into hydration! Drink water now~ 💦",
]


def send_notification(title, message):
    if HAS_PLYER:
        try:
            notification.notify(title=title, message=message, timeout=8)
            return
        except Exception:
            pass
    # Fallback: use macOS osascript on macOS, else print
    if OS == "Darwin":
        import subprocess
        subprocess.Popen([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}"'
        ])
    else:
        print(f"\n🐸 {title}: {message}\n")


# ══════════════════════════════════════════════════════════════════════════════
#  macOS backend — PyObjC (NSWindow, native transparency, no chrome at all)
# ══════════════════════════════════════════════════════════════════════════════
if OS == "Darwin":
    import objc
    from AppKit import (
        NSApplication, NSApp, NSWindow, NSView, NSColor,
        NSBezierPath, NSRect, NSPoint, NSSize,
        NSWindowStyleMaskBorderless,
        NSBackingStoreBuffered,
        NSFloatingWindowLevel,
        NSApplicationActivationPolicyAccessory,
        NSMenu, NSMenuItem,
        NSEvent,
        NSLeftMouseDown, NSLeftMouseDragged,
        NSRightMouseDown,
    )
    from Foundation import (
        NSObject, NSTimer, NSRunLoop, NSDefaultRunLoopMode,
        NSMakeRect, NSMakePoint, NSMakeSize,
    )

    class FrogView(NSView):
        """Custom NSView that draws the pixel-art frog."""

        def initWithFrame_(self, frame):
            self = objc.super(FrogView, self).initWithFrame_(frame)
            if self is None:
                return None
            self._frame_count  = 0
            self._blink_cd     = random.randint(60, 120)
            self._blinking     = False
            self._blink_frames = 0
            self._waving       = False
            self._wave_frames  = 0
            self._drag_start   = None
            self._win_origin   = None
            return self

        # ── Transparency ──────────────────────────────────────────────────────
        def isOpaque(self):
            return False

        def wantsDefaultClipping(self):
            return False

        # ── Drawing ───────────────────────────────────────────────────────────
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
                    if cid == 0:
                        continue
                    r, g, b = PALETTE[cid]
                    color = NSColor.colorWithCalibratedRed_green_blue_alpha_(
                        r/255, g/255, b/255, 1.0)
                    color.set()
                    # NSView coords are bottom-left origin
                    flipped_row = (ROWS - 1 - row)
                    rect = NSMakeRect(
                        col * PIXEL_SIZE,
                        flipped_row * PIXEL_SIZE + bob,
                        PIXEL_SIZE,
                        PIXEL_SIZE,
                    )
                    NSBezierPath.fillRect_(rect)

        # ── Timer tick ────────────────────────────────────────────────────────
        def tick_(self, timer):
            self.setNeedsDisplay_(True)

        # ── Drag to move ──────────────────────────────────────────────────────
        def mouseDown_(self, event):
            self._drag_start  = event.locationInWindow()
            self._win_origin  = self.window().frame().origin
            self._did_drag    = False

        def mouseDragged_(self, event):
            self._did_drag = True
            loc   = event.locationInWindow()
            win   = self.window()
            frame = win.frame()
            dx = loc.x - self._drag_start.x
            dy = loc.y - self._drag_start.y
            new_origin = NSMakePoint(frame.origin.x + dx,
                                     frame.origin.y + dy)
            win.setFrameOrigin_(new_origin)

        def mouseUp_(self, event):
            if not self._did_drag:
                self.triggerWave()

        def rightMouseDown_(self, event):
            self._show_context_menu(event)

        # ── Wave ──────────────────────────────────────────────────────────────
        def triggerWave(self):
            if not self._waving:
                self._waving      = True
                self._wave_frames = IDLE_FPS * 2

        # ── Context menu ──────────────────────────────────────────────────────
        def _show_context_menu(self, event):
            menu = NSMenu.alloc().initWithTitle_("FrogPal")
            wave_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Wave! 🐸", "waveAction:", "")
            wave_item.setTarget_(self)
            remind_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Remind me now 💧", "remindAction:", "")
            remind_item.setTarget_(self)
            quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Quit", "quitAction:", "")
            quit_item.setTarget_(self)
            menu.addItem_(wave_item)
            menu.addItem_(NSMenuItem.separatorItem())
            menu.addItem_(remind_item)
            menu.addItem_(NSMenuItem.separatorItem())
            menu.addItem_(quit_item)
            NSMenu.popUpContextMenu_withEvent_forView_(menu, event, self)

        def waveAction_(self, sender):
            self.triggerWave()

        def remindAction_(self, sender):
            self.triggerWave()
            send_notification("FrogPal 🐸", random.choice(WATER_MSGS))

        def quitAction_(self, sender):
            NSApp.terminate_(None)

    def run_macos():
        app = NSApplication.sharedApplication()
        # Accessory policy = no Dock icon, no menu bar item
        app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

        # ── Borderless, transparent, always-on-top window ─────────────────────
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
        win.setCollectionBehavior_(
            1 << 3 |   # NSWindowCollectionBehaviorCanJoinAllSpaces
            1 << 6     # NSWindowCollectionBehaviorStationary
        )
        win.setIgnoresMouseEvents_(False)
        win.setAcceptsMouseMovedEvents_(True)

        # ── Frog view ─────────────────────────────────────────────────────────
        view = FrogView.alloc().initWithFrame_(
            NSMakeRect(0, 0, WIN_W, WIN_H)
        )
        win.setContentView_(view)
        win.makeKeyAndOrderFront_(None)

        # ── Animation timer ───────────────────────────────────────────────────
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0 / IDLE_FPS, view, "tick:", None, True
        )

        # ── Water reminder thread ─────────────────────────────────────────────
        def reminder_loop():
            time.sleep(REMINDER_INTERVAL_MINUTES * 60)
            while True:
                view.triggerWave()
                send_notification("FrogPal 🐸", random.choice(WATER_MSGS))
                time.sleep(REMINDER_INTERVAL_MINUTES * 60)

        t = threading.Thread(target=reminder_loop, daemon=True)
        t.start()

        app.run()


# ══════════════════════════════════════════════════════════════════════════════
#  Windows / Linux backend — tkinter
# ══════════════════════════════════════════════════════════════════════════════
else:
    import tkinter as tk

    TRANSPARENT_COLOR = "#010101"

    def _hex(palette_id):
        if palette_id == 0:
            return TRANSPARENT_COLOR
        r, g, b = PALETTE[palette_id]
        return f"#{r:02x}{g:02x}{b:02x}"

    def draw_sprite(canvas, sprite, offset_y=0):
        canvas.delete("sprite")
        for row in range(ROWS):
            for col in range(COLS):
                cid = sprite[row][col]
                if cid == 0:
                    continue
                x0 = col * PIXEL_SIZE
                y0 = row * PIXEL_SIZE + offset_y
                canvas.create_rectangle(
                    x0, y0, x0 + PIXEL_SIZE, y0 + PIXEL_SIZE,
                    fill=_hex(cid), outline="", tags="sprite"
                )

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

            self.canvas = tk.Canvas(
                self.root, width=WIN_W, height=WIN_H,
                bg=TRANSPARENT_COLOR, highlightthickness=0, borderwidth=0
            )
            self.canvas.pack()

            self._frame  = 0
            self._blink_cd = random.randint(60, 120)
            self._blinking = False
            self._blink_f  = 0
            self._waving   = False
            self._wave_f   = 0

            self.canvas.bind("<ButtonPress-1>",   self._drag_start)
            self.canvas.bind("<B1-Motion>",        self._drag_motion)
            self.canvas.bind("<ButtonRelease-1>",  self._drag_end)
            self.canvas.bind("<Button-3>",         self._show_menu)

            self._menu = tk.Menu(self.root, tearoff=0)
            self._menu.add_command(label="Wave! 🐸",        command=self._wave)
            self._menu.add_separator()
            self._menu.add_command(label="Remind me now 💧", command=self._remind)
            self._menu.add_separator()
            self._menu.add_command(label="Quit",             command=self.root.destroy)

            self._animate()
            threading.Thread(target=self._reminder_loop, daemon=True).start()

        def _animate(self):
            self._frame += 1
            bob = int(2 * (0.5 - abs((self._frame % BOB_PERIOD) / BOB_PERIOD - 0.5)) * 2)
            if self._waving:
                sprite = FROG_WAVE
                self._wave_f -= 1
                if self._wave_f <= 0:
                    self._waving = False
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
            self.root.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

        def _drag_end(self, e):
            if not self._did_drag:
                self._wave()

        def _show_menu(self, e):
            try:
                self._menu.tk_popup(e.x_root, e.y_root)
            finally:
                self._menu.grab_release()

        def _wave(self):
            self._waving = True
            self._wave_f = IDLE_FPS * 2

        def _remind(self):
            self._wave()
            send_notification("FrogPal 🐸", random.choice(WATER_MSGS))

        def _reminder_loop(self):
            time.sleep(REMINDER_INTERVAL_MINUTES * 60)
            while True:
                self.root.after(0, self._remind)
                time.sleep(REMINDER_INTERVAL_MINUTES * 60)

        def run(self):
            self.root.mainloop()


# ══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if OS == "Darwin":
        run_macos()
    else:
        FrogPalTk().run()
