"""
FrogPal — transparent pixel-art desktop frog with water reminders.

macOS  → PyObjC (NSWindow, true transparency, always on top)
Windows/Linux → tkinter fallback

- Frog starts centered on screen, stays on top of ALL windows always
- Water reminders every 2 hours from 6am–10pm
- Yellow speech bubble pops above frog with a close ✕ button
- Frog NEVER disappears — bubble is a separate floating window
- Cute frog ribbit sound on every reminder
"""

import platform, sys, threading, time, random, datetime
import math, wave, struct, tempfile, subprocess, os

OS = platform.system()

# ── Schedule: hours to remind (24h) ──────────────────────────────────────────
REMINDER_HOURS = {6, 8, 10, 12, 14, 16, 18, 20, 22}

# ── Pixel art config ──────────────────────────────────────────────────────────
PIXEL_SIZE  = 6
COLS = ROWS = 16
WIN_W = COLS * PIXEL_SIZE   # 96 px
WIN_H = ROWS * PIXEL_SIZE   # 96 px
IDLE_FPS    = 8
BOB_PERIOD  = 24

# ── Colour palette (R,G,B) ────────────────────────────────────────────────────
PALETTE = {
    0: None,
    1: (45, 106, 45),
    2: (76, 175, 80),
    3: (129,199,132),
    4: (27,  94, 32),
    5: (255,255,255),
    6: (33,  33, 33),
    7: (244,143,177),
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


# ══════════════════════════════════════════════════════════════════════════════
#  Ribbit sound — FM synthesis, no external files
# ══════════════════════════════════════════════════════════════════════════════
_RIBBIT_PATH = None

def _make_ribbit_wav():
    sr = 44100
    out = []

    def frog_pulse(base, mod_freq, mod_depth, dur, vol=0.75):
        n = int(sr * dur)
        for i in range(n):
            t   = i / sr
            pct = i / n
            # Pitch arc: rises then falls like a real ribbit
            if pct < 0.35:
                freq = base + mod_depth * (pct / 0.35)
            else:
                freq = base + mod_depth * (1 - (pct - 0.35) / 0.65)
            # Smooth amplitude envelope
            env = math.sin(math.pi * pct) ** 0.45
            # Harmonics for froggy timbre
            s = (0.55 * math.sin(2*math.pi * freq   * t) +
                 0.28 * math.sin(2*math.pi * freq*2  * t) +
                 0.12 * math.sin(2*math.pi * freq*3  * t) +
                 0.05 * math.sin(2*math.pi * freq*0.5* t))
            out.append(env * vol * s)

    def gap(dur):
        out.extend([0.0] * int(sr * dur))

    # "Rib-bit" × 2 with a short gap
    frog_pulse(380, 220, 180, 0.13, vol=0.8)
    gap(0.04)
    frog_pulse(420, 260, 200, 0.10, vol=0.75)
    gap(0.10)
    frog_pulse(360, 200, 160, 0.11, vol=0.7)
    gap(0.04)
    frog_pulse(400, 240, 190, 0.09, vol=0.65)

    path = tempfile.mktemp(suffix=".wav")
    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        for s in out:
            f.writeframes(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)))
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
            winsound.PlaySound(_RIBBIT_PATH,
                               winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            subprocess.Popen(["aplay", _RIBBIT_PATH])
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  macOS — PyObjC backend
# ══════════════════════════════════════════════════════════════════════════════
if OS == "Darwin":
    import objc
    from AppKit import (
        NSApplication, NSApp, NSWindow, NSView, NSColor,
        NSBezierPath, NSFont, NSScreen,
        NSWindowStyleMaskBorderless, NSBackingStoreBuffered,
        NSApplicationActivationPolicyAccessory,
        NSMenu, NSMenuItem,
        NSMutableParagraphStyle, NSCenterTextAlignment, NSLeftTextAlignment,
        NSForegroundColorAttributeName, NSFontAttributeName,
        NSParagraphStyleAttributeName,
        NSTrackingArea,
        NSTrackingMouseEnteredAndExited, NSTrackingActiveAlways,
    )
    from Foundation import (
        NSObject, NSTimer, NSMakeRect, NSMakePoint, NSMakeSize,
        NSAttributedString,
    )

    # ── Yellow speech bubble with ✕ close button ──────────────────────────────
    BUBBLE_W  = 230
    BUBBLE_H  = 80    # body
    TAIL_H    = 12
    CLOSE_R   = 10    # radius of close button circle
    CLOSE_X   = BUBBLE_W - 18
    CLOSE_Y   = BUBBLE_H - 18

    class BubbleView(NSView):
        def initWithMessage_onClose_(self, msg, close_cb):
            frame = NSMakeRect(0, 0, BUBBLE_W, BUBBLE_H + TAIL_H)
            self = objc.super(BubbleView, self).initWithFrame_(frame)
            if self is None: return None
            self._msg      = msg
            self._close_cb = close_cb
            self._hovering_close = False
            # Track mouse for close-button hover
            ta = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
                self.bounds(),
                NSTrackingMouseEnteredAndExited | NSTrackingActiveAlways,
                self, None)
            self.addTrackingArea_(ta)
            return self

        def isOpaque(self): return False

        def drawRect_(self, dirty):
            NSColor.clearColor().set()
            NSBezierPath.fillRect_(self.bounds())

            # ── Bubble body (rounded rect above the tail) ─────────────────────
            r = 14.0
            w, h = BUBBLE_W, BUBBLE_H
            path = NSBezierPath.bezierPath()
            path.moveToPoint_(NSMakePoint(r, h + TAIL_H))
            path.lineToPoint_(NSMakePoint(w - r, h + TAIL_H))
            path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
                NSMakePoint(w - r, h + TAIL_H - r), r, 90, 0)
            path.lineToPoint_(NSMakePoint(w, TAIL_H + r))
            path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
                NSMakePoint(w - r, TAIL_H + r), r, 0, 270)
            path.lineToPoint_(NSMakePoint(r, TAIL_H))
            path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
                NSMakePoint(r, TAIL_H + r), r, 270, 180)
            path.lineToPoint_(NSMakePoint(0, h + TAIL_H - r))
            path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
                NSMakePoint(r, h + TAIL_H - r), r, 180, 90)
            path.closePath()

            # Tail triangle (centered, points down toward frog)
            tail = NSBezierPath.bezierPath()
            cx = w / 2
            tail.moveToPoint_(NSMakePoint(cx - 10, TAIL_H))
            tail.lineToPoint_(NSMakePoint(cx + 10, TAIL_H))
            tail.lineToPoint_(NSMakePoint(cx, 0))
            tail.closePath()

            # Yellow fill
            NSColor.colorWithCalibratedRed_green_blue_alpha_(
                1.0, 0.88, 0.1, 0.96).set()
            path.fill()
            tail.fill()

            # Outline
            NSColor.colorWithCalibratedRed_green_blue_alpha_(
                0.7, 0.55, 0.0, 1.0).set()
            path.setLineWidth_(1.8)
            path.stroke()
            tail.setLineWidth_(1.8)
            tail.stroke()

            # ── Close button ──────────────────────────────────────────────────
            cx_btn, cy_btn = CLOSE_X, CLOSE_Y + TAIL_H
            btn_rect = NSMakeRect(cx_btn - CLOSE_R, cy_btn - CLOSE_R,
                                  CLOSE_R*2, CLOSE_R*2)
            circle = NSBezierPath.bezierPathWithOvalInRect_(btn_rect)
            if self._hovering_close:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(
                    0.85, 0.15, 0.1, 1.0).set()
            else:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(
                    0.9, 0.35, 0.2, 1.0).set()
            circle.fill()

            NSColor.whiteColor().set()
            cross = NSBezierPath.bezierPath()
            off = 4.5
            cross.moveToPoint_(NSMakePoint(cx_btn - off, cy_btn - off))
            cross.lineToPoint_(NSMakePoint(cx_btn + off, cy_btn + off))
            cross.moveToPoint_(NSMakePoint(cx_btn + off, cy_btn - off))
            cross.lineToPoint_(NSMakePoint(cx_btn - off, cy_btn + off))
            cross.setLineWidth_(2.0)
            cross.setLineCapStyle_(1)  # NSRoundLineCapStyle
            cross.stroke()

            # ── Message text ──────────────────────────────────────────────────
            para = NSMutableParagraphStyle.alloc().init()
            para.setAlignment_(NSCenterTextAlignment)
            attrs = {
                NSForegroundColorAttributeName:
                    NSColor.colorWithCalibratedRed_green_blue_alpha_(
                        0.15, 0.1, 0.0, 1.0),
                NSFontAttributeName: NSFont.boldSystemFontOfSize_(12),
                NSParagraphStyleAttributeName: para,
            }
            text_rect = NSMakeRect(8, TAIL_H + 10, BUBBLE_W - 36, BUBBLE_H - 20)
            self._msg.drawInRect_withAttributes_(text_rect, attrs)

        def mouseUp_(self, event):
            loc = event.locationInWindow()
            cx_btn = CLOSE_X
            cy_btn = CLOSE_Y + TAIL_H
            dx = loc.x - cx_btn
            dy = loc.y - cy_btn
            if dx*dx + dy*dy <= CLOSE_R*CLOSE_R:
                if self._close_cb:
                    self._close_cb()

        def mouseMoved_(self, event):
            self._check_hover(event)
            self.setNeedsDisplay_(True)

        def mouseEntered_(self, event):
            self._check_hover(event)
            self.setNeedsDisplay_(True)

        def mouseExited_(self, event):
            self._hovering_close = False
            self.setNeedsDisplay_(True)

        def _check_hover(self, event):
            loc = event.locationInWindow()
            cx_btn = CLOSE_X
            cy_btn = CLOSE_Y + TAIL_H
            dx = loc.x - cx_btn
            dy = loc.y - cy_btn
            self._hovering_close = (dx*dx + dy*dy <= CLOSE_R*CLOSE_R)


    # ── Frog view ─────────────────────────────────────────────────────────────
    class FrogView(NSView):
        def initWithFrame_(self, frame):
            self = objc.super(FrogView, self).initWithFrame_(frame)
            if self is None: return None
            self._fc         = 0
            self._blink_cd   = random.randint(60, 120)
            self._blinking   = False
            self._blink_f    = 0
            self._waving     = False
            self._wave_f     = 0
            self._did_drag   = False
            self._frog_win   = None
            self._bubble_win = None
            return self

        def isOpaque(self): return False
        def wantsDefaultClipping(self): return False

        def drawRect_(self, dirty):
            NSColor.clearColor().set()
            NSBezierPath.fillRect_(self.bounds())

            self._fc += 1
            bob = int(2*(0.5 - abs((self._fc % BOB_PERIOD)/BOB_PERIOD - 0.5))*2)

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

            for row in range(ROWS):
                for col in range(COLS):
                    cid = sprite[row][col]
                    if cid == 0: continue
                    rv, gv, bv = PALETTE[cid]
                    NSColor.colorWithCalibratedRed_green_blue_alpha_(
                        rv/255, gv/255, bv/255, 1.0).set()
                    NSBezierPath.fillRect_(NSMakeRect(
                        col*PIXEL_SIZE,
                        (ROWS-1-row)*PIXEL_SIZE + bob,
                        PIXEL_SIZE, PIXEL_SIZE))

        def tick_(self, timer):
            # Keep frog on top every tick
            if self._frog_win:
                self._frog_win.orderFrontRegardless()
            self.setNeedsDisplay_(True)

        # ── Drag ──────────────────────────────────────────────────────────────
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
                NSMakePoint(f.origin.x + dx, f.origin.y + dy))
            # Move bubble with frog if visible
            self._reposition_bubble()

        def mouseUp_(self, event):
            if not self._did_drag:
                self._trigger_wave()

        # ── Right-click menu ──────────────────────────────────────────────────
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
                self._waving = True
                self._wave_f = IDLE_FPS * 2

        # ── Remind ────────────────────────────────────────────────────────────
        def _do_remind(self):
            msg_str = random.choice(WATER_MSGS)
            self._trigger_wave()
            play_ribbit()
            self._show_bubble(msg_str)

        def remindFromThread(self):
            self._do_remind()

        # ── Bubble ────────────────────────────────────────────────────────────
        def _show_bubble(self, msg_str):
            # Close any existing bubble
            self._close_bubble()

            if not self._frog_win: return

            fw = self._frog_win.frame()
            bx = fw.origin.x + fw.size.width/2 - BUBBLE_W/2
            by = fw.origin.y + fw.size.height + 4   # just above frog

            bwin = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
                NSMakeRect(bx, by, BUBBLE_W, BUBBLE_H + TAIL_H),
                NSWindowStyleMaskBorderless,
                NSBackingStoreBuffered,
                False)
            bwin.setBackgroundColor_(NSColor.clearColor())
            bwin.setOpaque_(False)
            bwin.setHasShadow_(True)
            bwin.setLevel_(1001)           # one above frog (1000)
            bwin.setHidesOnDeactivate_(False)
            bwin.setIgnoresMouseEvents_(False)
            bwin.setAcceptsMouseMovedEvents_(True)

            view = BubbleView.alloc().initWithMessage_onClose_(
                msg_str, self._close_bubble)
            bwin.setContentView_(view)
            bwin.orderFrontRegardless()

            self._bubble_win = bwin

            # Re-raise frog so it stays visible alongside bubble
            if self._frog_win:
                self._frog_win.orderFrontRegardless()

        def _close_bubble(self):
            if self._bubble_win:
                self._bubble_win.orderOut_(None)
                self._bubble_win = None

        def _reposition_bubble(self):
            if self._bubble_win and self._frog_win:
                fw = self._frog_win.frame()
                bx = fw.origin.x + fw.size.width/2 - BUBBLE_W/2
                by = fw.origin.y + fw.size.height + 4
                self._bubble_win.setFrameOrigin_(NSMakePoint(bx, by))


    def run_macos():
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

        # ── Center frog on main screen ────────────────────────────────────────
        screen_frame = NSScreen.mainScreen().frame()
        sx = screen_frame.size.width / 2  - WIN_W / 2
        sy = screen_frame.size.height / 2 - WIN_H / 2

        win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(sx, sy, WIN_W, WIN_H),
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False)
        win.setBackgroundColor_(NSColor.clearColor())
        win.setOpaque_(False)
        win.setHasShadow_(False)
        # Level 1000 = NSScreenSaverWindowLevel — above Finder, Dock, everything
        win.setLevel_(1000)
        win.setCollectionBehavior_(
            1  |   # NSWindowCollectionBehaviorCanJoinAllSpaces
            16 |   # NSWindowCollectionBehaviorStationary
            64     # NSWindowCollectionBehaviorIgnoresCycle
        )
        win.setHidesOnDeactivate_(False)   # NEVER hide when app loses focus
        win.setCanHide_(False)             # ignore "Hide Others" too
        win.setIgnoresMouseEvents_(False)
        win.setAcceptsMouseMovedEvents_(True)

        view = FrogView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, WIN_H))
        view._frog_win = win
        win.setContentView_(view)
        win.orderFrontRegardless()

        # Animation + keep-on-top timer
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0/IDLE_FPS, view, "tick:", None, True)

        # Pre-generate ribbit
        threading.Thread(target=play_ribbit, daemon=True).start()

        # Reminder thread
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
        r,g,b = PALETTE[pid]
        return f"#{r:02x}{g:02x}{b:02x}"

    def draw_sprite(canvas, sprite, dy=0):
        canvas.delete("sprite")
        for row in range(ROWS):
            for col in range(COLS):
                cid = sprite[row][col]
                if cid == 0: continue
                x0 = col*PIXEL_SIZE; y0 = row*PIXEL_SIZE+dy
                canvas.create_rectangle(x0,y0,x0+PIXEL_SIZE,y0+PIXEL_SIZE,
                                        fill=_hex(cid),outline="",tags="sprite")

    class BubbleTk(tk.Toplevel):
        def __init__(self, parent, msg, frog_x, frog_y, frog_w):
            super().__init__(parent)
            self.overrideredirect(True)
            self.attributes("-topmost", True)
            self.configure(bg="#ffe010")
            w = 230
            x = frog_x + frog_w//2 - w//2
            y = frog_y - 70
            self.geometry(f"{w}x60+{x}+{y}")
            frm = tk.Frame(self, bg="#ffe010")
            frm.pack(fill="both", expand=True)
            tk.Label(frm, text=msg, bg="#ffe010", fg="#2a1a00",
                     font=("Arial",10,"bold"), wraplength=190,
                     justify="center").pack(side="left", expand=True, padx=6)
            tk.Button(frm, text="✕", command=self.destroy,
                      bg="#e05020", fg="white", relief="flat",
                      font=("Arial",9,"bold"), cursor="hand2",
                      padx=4).pack(side="right", padx=4, pady=4)

    class FrogPalTk:
        def __init__(self):
            self.root = tk.Tk()
            self.root.overrideredirect(True)
            self.root.attributes("-topmost", True)

            # Center on screen
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            sx = sw//2 - WIN_W//2
            sy = sh//2 - WIN_H//2
            self.root.geometry(f"{WIN_W}x{WIN_H}+{sx}+{sy}")
            self.root.configure(bg=TC)
            if OS=="Windows": self.root.attributes("-transparentcolor", TC)
            else:              self.root.attributes("-alpha", 0.95)

            self.canvas = tk.Canvas(self.root, width=WIN_W, height=WIN_H,
                bg=TC, highlightthickness=0, borderwidth=0)
            self.canvas.pack()
            self._bubble = None

            self._fc=0; self._blink_cd=random.randint(60,120)
            self._blinking=False; self._blink_f=0
            self._waving=False; self._wave_f=0

            self.canvas.bind("<ButtonPress-1>",  self._ds)
            self.canvas.bind("<B1-Motion>",       self._dm)
            self.canvas.bind("<ButtonRelease-1>", self._du)
            self.canvas.bind("<Button-3>",        self._menu_show)

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
            draw_sprite(self.canvas, sprite, bob)
            self.root.attributes("-topmost", True)   # re-enforce every frame
            self.root.after(1000//IDLE_FPS, self._animate)

        def _ds(self,e): self._ox=e.x_root-self.root.winfo_x(); self._oy=e.y_root-self.root.winfo_y(); self._dd=False
        def _dm(self,e): self._dd=True; self.root.geometry(f"+{e.x_root-self._ox}+{e.y_root-self._oy}")
        def _du(self,e):
            if not self._dd: self._wave()
        def _menu_show(self,e):
            try: self._menu.tk_popup(e.x_root,e.y_root)
            finally: self._menu.grab_release()
        def _wave(self): self._waving=True; self._wave_f=IDLE_FPS*2

        def _remind(self):
            msg = random.choice(WATER_MSGS)
            self._wave(); play_ribbit()
            if self._bubble:
                try: self._bubble.destroy()
                except: pass
            self._bubble = BubbleTk(self.root, msg,
                self.root.winfo_x(), self.root.winfo_y(), WIN_W)

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
