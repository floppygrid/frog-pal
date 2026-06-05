"""
FrogPal — transparent pixel-art desktop frog with water reminders.

macOS  → PyObjC single-window design (frog + bubble in ONE NSWindow)
Windows/Linux → tkinter fallback

- Single window: expands upward to show yellow bubble, shrinks back when closed
- Frog stays locked in place — window grows UP, frog never moves
- Always on top of everything (level 1000)
- Reminders every 2 h from 6 am – 10 pm
"""

import platform, sys, threading, time, random, datetime
import math, wave, struct, tempfile, subprocess

OS = platform.system()

REMINDER_HOURS = {6, 8, 10, 12, 14, 16, 18, 20, 22}

# ── Pixel config ──────────────────────────────────────────────────────────────
PIXEL_SIZE = 6
COLS = ROWS = 16
FROG_W = COLS * PIXEL_SIZE   # 96
FROG_H = ROWS * PIXEL_SIZE   # 96
IDLE_FPS   = 8
BOB_PERIOD = 24

BUBBLE_W   = 240
BUBBLE_H   = 76    # body height
TAIL_H     = 14    # triangle below body
BUBBLE_TOT = BUBBLE_H + TAIL_H   # total bubble height
GAP        = 2     # gap between frog top and bubble tail

# Window width wide enough for bubble; frog is centred inside it
WIN_W = BUBBLE_W
# Frog x-offset inside the wide window
FROG_X = (WIN_W - FROG_W) // 2   # = 72

CLOSE_R = 11   # close-button radius
CLOSE_BX = WIN_W - 20   # close button centre x (in bubble coords)
CLOSE_BY = BUBBLE_H - 16  # close button centre y (in bubble coords, from tail top)

PALETTE = {
    0: None,
    1: (45, 106, 45),   2: (76, 175, 80),
    3: (129,199,132),   4: (27,  94,  32),
    5: (255,255,255),   6: (33,  33,  33),
    7: (244,143,177),
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

# ── Ribbit sound ──────────────────────────────────────────────────────────────
_RIBBIT_PATH = None

def _make_ribbit_wav():
    sr = 44100
    out = []
    def pulse(base, mod_depth, dur, vol=0.75):
        n = int(sr * dur)
        for i in range(n):
            t = i / sr; pct = i / n
            freq = base + mod_depth * math.sin(math.pi * pct)
            env  = math.sin(math.pi * pct) ** 0.45
            s = (0.55*math.sin(2*math.pi*freq*t) +
                 0.28*math.sin(2*math.pi*freq*2*t) +
                 0.12*math.sin(2*math.pi*freq*3*t))
            out.append(env * vol * s)
    def gap(d): out.extend([0.0]*int(sr*d))
    pulse(380, 180, 0.13); gap(0.04)
    pulse(420, 200, 0.10); gap(0.10)
    pulse(360, 160, 0.11); gap(0.04)
    pulse(400, 190, 0.09)
    path = tempfile.mktemp(suffix=".wav")
    with wave.open(path,"w") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
        for s in out:
            f.writeframes(struct.pack("<h", int(max(-1.,min(1.,s))*32767)))
    return path

def play_ribbit():
    global _RIBBIT_PATH
    if _RIBBIT_PATH is None: _RIBBIT_PATH = _make_ribbit_wav()
    try:
        if OS=="Darwin":   subprocess.Popen(["afplay", _RIBBIT_PATH])
        elif OS=="Windows":
            import winsound
            winsound.PlaySound(_RIBBIT_PATH, winsound.SND_FILENAME|winsound.SND_ASYNC)
        else: subprocess.Popen(["aplay", _RIBBIT_PATH])
    except: pass


# ══════════════════════════════════════════════════════════════════════════════
#  macOS — single-window PyObjC backend
# ══════════════════════════════════════════════════════════════════════════════
if OS == "Darwin":
    import objc
    from AppKit import (
        NSApplication, NSApp, NSWindow, NSView, NSColor,
        NSBezierPath, NSFont, NSScreen,
        NSWindowStyleMaskBorderless, NSBackingStoreBuffered,
        NSApplicationActivationPolicyAccessory,
        NSMenu, NSMenuItem,
        NSMutableParagraphStyle, NSCenterTextAlignment,
        NSForegroundColorAttributeName, NSFontAttributeName,
        NSParagraphStyleAttributeName,
        NSTrackingArea, NSTrackingMouseEnteredAndExited, NSTrackingActiveAlways,
    )
    from Foundation import NSObject, NSTimer, NSMakeRect, NSMakePoint

    FROG_LEVEL   = 1000   # NSScreenSaverWindowLevel — above everything

    class FrogView(NSView):

        def initWithFrame_(self, frame):
            self = objc.super(FrogView, self).initWithFrame_(frame)
            if self is None: return None
            # Animation state
            self._fc       = 0
            self._blink_cd = random.randint(60, 120)
            self._blinking = False; self._blink_f = 0
            self._waving   = False; self._wave_f  = 0
            # Drag
            self._drag_origin = None
            self._did_drag    = False
            # Bubble
            self._bubble_msg     = None   # None = hidden
            self._hover_close    = False
            self._win_ref        = None   # set after window creation
            # Tracking area for hover (full view, rebuilt on resize)
            self._tracking = None
            return self

        def isOpaque(self): return False
        def wantsDefaultClipping(self): return False

        def _rebuild_tracking(self):
            if self._tracking:
                self.removeTrackingArea_(self._tracking)
            ta = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
                self.bounds(),
                NSTrackingMouseEnteredAndExited | NSTrackingActiveAlways,
                self, None)
            self.addTrackingArea_(ta)
            self._tracking = ta

        # ── Drawing ───────────────────────────────────────────────────────────
        def drawRect_(self, dirty):
            NSColor.clearColor().set()
            NSBezierPath.fillRect_(self.bounds())

            if self._bubble_msg is not None:
                self._draw_bubble()

            self._draw_frog()

        def _draw_frog(self):
            self._fc += 1
            bob = int(2*(0.5-abs((self._fc%BOB_PERIOD)/BOB_PERIOD-0.5))*2)

            if self._waving:
                sprite = FROG_WAVE; self._wave_f -= 1
                if self._wave_f <= 0: self._waving = False
            elif self._blinking:
                sprite = FROG_BLINK; self._blink_f -= 1
                if self._blink_f <= 0:
                    self._blinking = False
                    self._blink_cd = random.randint(60, 120)
            else:
                sprite = FROG_IDLE; self._blink_cd -= 1
                if self._blink_cd <= 0:
                    self._blinking = True; self._blink_f = 4

            for row in range(ROWS):
                for col in range(COLS):
                    cid = sprite[row][col]
                    if cid == 0: continue
                    rv, gv, bv = PALETTE[cid]
                    NSColor.colorWithCalibratedRed_green_blue_alpha_(
                        rv/255, gv/255, bv/255, 1.0).set()
                    # Frog sits at y=0 in view; NSView y=0 is bottom
                    NSBezierPath.fillRect_(NSMakeRect(
                        FROG_X + col*PIXEL_SIZE,
                        (ROWS-1-row)*PIXEL_SIZE + bob,
                        PIXEL_SIZE, PIXEL_SIZE))

        def _draw_bubble(self):
            # Bubble sits above the frog: y = FROG_H + GAP
            base_y = FROG_H + GAP

            # ── Tail triangle (points down to frog) ───────────────────────────
            tail = NSBezierPath.bezierPath()
            cx = WIN_W / 2
            tail.moveToPoint_(NSMakePoint(cx-11, base_y + TAIL_H))
            tail.lineToPoint_(NSMakePoint(cx+11, base_y + TAIL_H))
            tail.lineToPoint_(NSMakePoint(cx,    base_y))
            tail.closePath()

            # ── Rounded bubble body ───────────────────────────────────────────
            r = 14.0
            bx, by = 0, base_y + TAIL_H
            bw, bh = WIN_W, BUBBLE_H
            body = NSBezierPath.bezierPath()
            body.moveToPoint_(NSMakePoint(bx+r, by+bh))
            body.lineToPoint_(NSMakePoint(bx+bw-r, by+bh))
            body.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
                NSMakePoint(bx+bw-r, by+bh-r), r, 90, 0)
            body.lineToPoint_(NSMakePoint(bx+bw, by+r))
            body.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
                NSMakePoint(bx+bw-r, by+r), r, 0, 270)
            body.lineToPoint_(NSMakePoint(bx+r, by))
            body.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
                NSMakePoint(bx+r, by+r), r, 270, 180)
            body.lineToPoint_(NSMakePoint(bx, by+bh-r))
            body.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
                NSMakePoint(bx+r, by+bh-r), r, 180, 90)
            body.closePath()

            # Yellow fill
            NSColor.colorWithCalibratedRed_green_blue_alpha_(
                1.0, 0.90, 0.05, 0.96).set()
            body.fill(); tail.fill()

            # Border
            NSColor.colorWithCalibratedRed_green_blue_alpha_(
                0.65, 0.50, 0.0, 1.0).set()
            body.setLineWidth_(1.8); body.stroke()
            tail.setLineWidth_(1.8); tail.stroke()

            # ── Close button ──────────────────────────────────────────────────
            cbx = CLOSE_BX
            cby = by + CLOSE_BY
            btn = NSBezierPath.bezierPathWithOvalInRect_(
                NSMakeRect(cbx-CLOSE_R, cby-CLOSE_R, CLOSE_R*2, CLOSE_R*2))
            if self._hover_close:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(
                    0.80, 0.10, 0.05, 1.0).set()
            else:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(
                    0.88, 0.30, 0.15, 1.0).set()
            btn.fill()
            NSColor.whiteColor().set()
            x_path = NSBezierPath.bezierPath()
            off = 5.0
            x_path.moveToPoint_(NSMakePoint(cbx-off, cby-off))
            x_path.lineToPoint_(NSMakePoint(cbx+off, cby+off))
            x_path.moveToPoint_(NSMakePoint(cbx+off, cby-off))
            x_path.lineToPoint_(NSMakePoint(cbx-off, cby+off))
            x_path.setLineWidth_(2.2)
            x_path.setLineCapStyle_(1)
            x_path.stroke()

            # ── Message text ──────────────────────────────────────────────────
            para = NSMutableParagraphStyle.alloc().init()
            para.setAlignment_(NSCenterTextAlignment)
            attrs = {
                NSForegroundColorAttributeName:
                    NSColor.colorWithCalibratedRed_green_blue_alpha_(
                        0.12, 0.08, 0.0, 1.0),
                NSFontAttributeName: NSFont.boldSystemFontOfSize_(12),
                NSParagraphStyleAttributeName: para,
            }
            text_rect = NSMakeRect(10, by+8, WIN_W-44, BUBBLE_H-16)
            self._bubble_msg.drawInRect_withAttributes_(text_rect, attrs)

        # ── Timer tick ────────────────────────────────────────────────────────
        def tick_(self, timer):
            if self._win_ref:
                self._win_ref.orderFrontRegardless()
            self.setNeedsDisplay_(True)

        # ── Mouse ─────────────────────────────────────────────────────────────
        def mouseDown_(self, event):
            self._drag_origin = event.locationInWindow()
            self._did_drag = False

        def mouseDragged_(self, event):
            self._did_drag = True
            loc = event.locationInWindow()
            f   = self.window().frame()
            dx  = loc.x - self._drag_origin.x
            dy  = loc.y - self._drag_origin.y
            self.window().setFrameOrigin_(
                NSMakePoint(f.origin.x+dx, f.origin.y+dy))

        def mouseUp_(self, event):
            if not self._did_drag:
                self._trigger_wave()

        def mouseMoved_(self, event):
            self._update_hover(event)

        def mouseEntered_(self, event):
            self._update_hover(event)

        def mouseExited_(self, event):
            if self._hover_close:
                self._hover_close = False
                self.setNeedsDisplay_(True)

        def _update_hover(self, event):
            if self._bubble_msg is None:
                return
            loc  = event.locationInWindow()
            base_y = FROG_H + GAP
            by   = base_y + TAIL_H
            cbx  = CLOSE_BX
            cby  = by + CLOSE_BY
            dx   = loc.x - cbx; dy = loc.y - cby
            was  = self._hover_close
            self._hover_close = (dx*dx + dy*dy <= CLOSE_R*CLOSE_R)
            if self._hover_close != was:
                self.setNeedsDisplay_(True)

        def mouseUp_(self, event):
            if self._did_drag: return
            # Check close-button hit
            if self._bubble_msg is not None:
                loc    = event.locationInWindow()
                base_y = FROG_H + GAP
                by     = base_y + TAIL_H
                cbx    = CLOSE_BX; cby = by + CLOSE_BY
                dx     = loc.x - cbx; dy = loc.y - cby
                if dx*dx + dy*dy <= CLOSE_R*CLOSE_R:
                    self._hide_bubble()
                    return
            self._trigger_wave()

        # ── Context menu ──────────────────────────────────────────────────────
        def rightMouseDown_(self, event):
            menu = NSMenu.alloc().initWithTitle_("FrogPal")
            for title, sel in [
                ("Wave! 🐸",         "waveAction:"),
                (None, None),
                ("Remind me now 💧", "remindAction:"),
                ("Quit",             "quitAction:"),
            ]:
                if title is None:
                    menu.addItem_(NSMenuItem.separatorItem())
                else:
                    item = NSMenuItem.alloc()\
                        .initWithTitle_action_keyEquivalent_(title, sel, "")
                    item.setTarget_(self)
                    menu.addItem_(item)
            NSMenu.popUpContextMenu_withEvent_forView_(menu, event, self)

        def waveAction_(self, _):   self._trigger_wave()
        def remindAction_(self, _): self._do_remind()
        def quitAction_(self, _):   NSApp.terminate_(None)

        def _trigger_wave(self):
            if not self._waving:
                self._waving = True; self._wave_f = IDLE_FPS * 2

        # ── Bubble show/hide (resize same window) ─────────────────────────────
        def _show_bubble(self, text):
            win = self._win_ref
            if win is None: return
            f = win.frame()
            extra = BUBBLE_TOT + GAP
            # Grow upward: shift origin down, increase height
            win.setFrame_display_animate_(
                NSMakeRect(f.origin.x, f.origin.y - extra,
                           WIN_W, FROG_H + extra),
                True, False)
            self._bubble_msg = text
            self._rebuild_tracking()
            self.setNeedsDisplay_(True)

        def _hide_bubble(self):
            win = self._win_ref
            if win is None: return
            f = win.frame()
            extra = BUBBLE_TOT + GAP
            # Shrink back
            win.setFrame_display_animate_(
                NSMakeRect(f.origin.x, f.origin.y + extra,
                           WIN_W, FROG_H),
                True, False)
            self._bubble_msg  = None
            self._hover_close = False
            self._rebuild_tracking()
            self.setNeedsDisplay_(True)

        # ── Remind ────────────────────────────────────────────────────────────
        def _do_remind(self):
            self._trigger_wave()
            play_ribbit()
            self._show_bubble(random.choice(WATER_MSGS))

        def remindFromThread(self):
            # Close existing bubble first, then show new one
            if self._bubble_msg is not None:
                self._hide_bubble()
            self._do_remind()


    def run_macos():
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

        # Center frog on screen
        sf = NSScreen.mainScreen().frame()
        sx = sf.size.width  / 2 - WIN_W  / 2
        sy = sf.size.height / 2 - FROG_H / 2

        win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(sx, sy, WIN_W, FROG_H),
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered, False)
        win.setBackgroundColor_(NSColor.clearColor())
        win.setOpaque_(False)
        win.setHasShadow_(False)
        win.setLevel_(FROG_LEVEL)
        win.setCollectionBehavior_(
            1  |   # CanJoinAllSpaces
            16 |   # Stationary
            64     # IgnoresCycle
        )
        win.setHidesOnDeactivate_(False)
        win.setCanHide_(False)
        win.setIgnoresMouseEvents_(False)
        win.setAcceptsMouseMovedEvents_(True)

        view = FrogView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, FROG_H))
        view._win_ref = win
        win.setContentView_(view)
        win.orderFrontRegardless()

        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0/IDLE_FPS, view, "tick:", None, True)

        threading.Thread(target=play_ribbit, daemon=True).start()

        def reminder_loop():
            last_hour = -1
            while True:
                now = datetime.datetime.now()
                h, m = now.hour, now.minute
                if h in REMINDER_HOURS and m == 0 and h != last_hour:
                    last_hour = h
                    view.performSelectorOnMainThread_withObject_waitUntilDone_(
                        "remindFromThread", None, False)
                time.sleep(30)

        threading.Thread(target=reminder_loop, daemon=True).start()
        app.run()


# ══════════════════════════════════════════════════════════════════════════════
#  Windows / Linux — tkinter fallback
# ══════════════════════════════════════════════════════════════════════════════
else:
    import tkinter as tk

    TC = "#010101"

    def _hex(pid):
        if pid == 0: return TC
        r,g,b = PALETTE[pid]; return f"#{r:02x}{g:02x}{b:02x}"

    def draw_sprite(canvas, sprite, ox=0, dy=0):
        canvas.delete("sprite")
        for row in range(ROWS):
            for col in range(COLS):
                cid = sprite[row][col]
                if cid == 0: continue
                x0 = ox + col*PIXEL_SIZE; y0 = row*PIXEL_SIZE+dy
                canvas.create_rectangle(x0,y0,x0+PIXEL_SIZE,y0+PIXEL_SIZE,
                                        fill=_hex(cid),outline="",tags="sprite")

    class FrogPalTk:
        def __init__(self):
            self.root = tk.Tk()
            self.root.overrideredirect(True)
            self.root.attributes("-topmost", True)
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self._base_x = sw//2 - WIN_W//2
            self._base_y = sh//2 - FROG_H//2
            self._showing_bubble = False
            self.root.geometry(f"{WIN_W}x{FROG_H}+{self._base_x}+{self._base_y}")
            self.root.configure(bg=TC)
            if OS=="Windows": self.root.attributes("-transparentcolor", TC)
            else:              self.root.attributes("-alpha", 0.95)

            self.canvas = tk.Canvas(self.root, width=WIN_W, height=FROG_H,
                bg=TC, highlightthickness=0, borderwidth=0)
            self.canvas.pack()
            self._bubble_frame = None

            self._fc=0; self._blink_cd=random.randint(60,120)
            self._blinking=False; self._blink_f=0
            self._waving=False; self._wave_f=0

            self.canvas.bind("<ButtonPress-1>",  self._ds)
            self.canvas.bind("<B1-Motion>",       self._dm)
            self.canvas.bind("<ButtonRelease-1>", self._du)
            self.canvas.bind("<Button-3>",        self._show_menu)

            self._menu = tk.Menu(self.root, tearoff=0)
            self._menu.add_command(label="Wave! 🐸",         command=self._wave)
            self._menu.add_separator()
            self._menu.add_command(label="Remind me now 💧", command=self._remind)
            self._menu.add_separator()
            self._menu.add_command(label="Quit",              command=self.root.destroy)

            self._animate()
            threading.Thread(target=self._reminder_loop, daemon=True).start()
            threading.Thread(target=play_ribbit, daemon=True).start()

        def _animate(self):
            self._fc += 1
            bob = int(2*(0.5-abs((self._fc%BOB_PERIOD)/BOB_PERIOD-0.5))*2)
            if self._waving:
                sprite=FROG_WAVE; self._wave_f-=1
                if self._wave_f<=0: self._waving=False
            elif self._blinking:
                sprite=FROG_BLINK; self._blink_f-=1
                if self._blink_f<=0:
                    self._blinking=False; self._blink_cd=random.randint(60,120)
            else:
                sprite=FROG_IDLE; self._blink_cd-=1
                if self._blink_cd<=0: self._blinking=True; self._blink_f=4
            draw_sprite(self.canvas, sprite, ox=FROG_X, dy=bob)
            self.root.attributes("-topmost", True)
            self.root.after(1000//IDLE_FPS, self._animate)

        def _ds(self,e):
            self._ox=e.x_root-self.root.winfo_x()
            self._oy=e.y_root-self.root.winfo_y(); self._dd=False
        def _dm(self,e):
            self._dd=True
            self.root.geometry(f"+{e.x_root-self._ox}+{e.y_root-self._oy}")
        def _du(self,e):
            if not self._dd: self._wave()
        def _show_menu(self,e):
            try: self._menu.tk_popup(e.x_root,e.y_root)
            finally: self._menu.grab_release()
        def _wave(self): self._waving=True; self._wave_f=IDLE_FPS*2

        def _show_bubble(self, msg):
            if self._bubble_frame:
                self._bubble_frame.destroy()
            total_h = FROG_H + BUBBLE_TOT + GAP
            wy = self.root.winfo_y()
            wx = self.root.winfo_x()
            self.root.geometry(f"{WIN_W}x{total_h}+{wx}+{wy - (BUBBLE_TOT+GAP)}")
            self.canvas.configure(height=total_h)

            frm = tk.Frame(self.canvas, bg="#ffe80a",
                           highlightbackground="#a88000", highlightthickness=2,
                           bd=0)
            frm.place(x=0, y=0, width=WIN_W, height=BUBBLE_H)
            tk.Label(frm, text=msg, bg="#ffe80a", fg="#1a0f00",
                     font=("Arial",11,"bold"), wraplength=WIN_W-44,
                     justify="center").place(relx=0.5, rely=0.5, anchor="center",
                                             x=-10)
            tk.Button(frm, text="✕", bg="#cc3010", fg="white",
                      relief="flat", font=("Arial",10,"bold"),
                      command=self._hide_bubble,
                      cursor="hand2", padx=4
                      ).place(x=WIN_W-30, y=4, width=24, height=24)
            self._bubble_frame = frm
            self._showing_bubble = True

        def _hide_bubble(self):
            if self._bubble_frame:
                self._bubble_frame.destroy()
                self._bubble_frame = None
            wy = self.root.winfo_y()
            wx = self.root.winfo_x()
            self.root.geometry(f"{WIN_W}x{FROG_H}+{wx}+{wy+(BUBBLE_TOT+GAP)}")
            self.canvas.configure(height=FROG_H)
            self._showing_bubble = False

        def _remind(self):
            if self._showing_bubble:
                self._hide_bubble()
            self._wave(); play_ribbit()
            self._show_bubble(random.choice(WATER_MSGS))

        def _reminder_loop(self):
            last_hour=-1
            while True:
                now=datetime.datetime.now(); h,m=now.hour,now.minute
                if h in REMINDER_HOURS and m==0 and h!=last_hour:
                    last_hour=h; self.root.after(0,self._remind)
                time.sleep(30)

        def run(self): self.root.mainloop()


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if OS == "Darwin":
        run_macos()
    else:
        FrogPalTk().run()
