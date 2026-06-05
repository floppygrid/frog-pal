"""
FrogPal — transparent pixel-art desktop frog with water reminders.

macOS  → PyObjC, single fixed-size window (no resizing — that caused disappearing)
Windows/Linux → tkinter fallback

Bubble strategy: window is ALWAYS the full height (frog + bubble space).
When bubble is hidden the upper area is transparent and clicks pass through.
This means ZERO window operations when showing/hiding the bubble → frog never moves.
"""

import platform, threading, time, random, datetime
import math, wave, struct, tempfile, subprocess

OS = platform.system()

REMINDER_HOURS  = {6, 8, 10, 12, 14, 16, 18, 20, 22}
TEST_DELAY_SECS = 20        # show a reminder 20 s after launch (for testing)

# ── Pixel art ─────────────────────────────────────────────────────────────────
PIXEL_SIZE = 6
COLS = ROWS = 16
FROG_W = FROG_H = COLS * PIXEL_SIZE   # 96 × 96
IDLE_FPS   = 8
BOB_PERIOD = 24

BUBBLE_W   = 240
BUBBLE_BH  = 80    # bubble body height
TAIL_H     = 14    # tail triangle
BUBBLE_TOT = BUBBLE_BH + TAIL_H
GAP        = 4

# The window is always this tall — frog at bottom, bubble space at top
WIN_W   = BUBBLE_W
FULL_H  = FROG_H + GAP + BUBBLE_TOT
FROG_X  = (WIN_W - FROG_W) // 2      # frog centred horizontally = 72

# Close-button position (in window coords from bottom = NSView origin)
FROG_TOP_Y   = FROG_H                 # y where frog top meets bubble tail
BUBBLE_BOT_Y = FROG_TOP_Y + GAP + TAIL_H   # y where bubble body starts
BUBBLE_TOP_Y = BUBBLE_BOT_Y + BUBBLE_BH    # y where bubble body ends
CLOSE_R  = 11
CLOSE_BX = WIN_W - 20
CLOSE_BY = BUBBLE_BOT_Y + BUBBLE_BH - 18   # near top-right of bubble

PALETTE = {
    0: None,
    1: (45,106,45),  2: (76,175,80),  3: (129,199,132),
    4: (27,94,32),   5: (255,255,255), 6: (33,33,33),
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
    sr = 44100; out = []
    def pulse(base, depth, dur, vol=0.75):
        n = int(sr*dur)
        for i in range(n):
            t=i/sr; p=i/n
            freq = base + depth*math.sin(math.pi*p)
            env  = math.sin(math.pi*p)**0.45
            s = (0.55*math.sin(2*math.pi*freq*t) +
                 0.28*math.sin(2*math.pi*freq*2*t) +
                 0.12*math.sin(2*math.pi*freq*3*t))
            out.append(env*vol*s)
    def gap(d): out.extend([0.]*int(sr*d))
    pulse(380,180,0.13); gap(0.04); pulse(420,200,0.10)
    gap(0.10); pulse(360,160,0.11); gap(0.04); pulse(400,190,0.09)
    path = tempfile.mktemp(suffix=".wav")
    with wave.open(path,"w") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
        for s in out:
            f.writeframes(struct.pack("<h",int(max(-1.,min(1.,s))*32767)))
    return path

def play_ribbit():
    """Always called in a background thread — never on the main thread."""
    global _RIBBIT_PATH
    if _RIBBIT_PATH is None: _RIBBIT_PATH = _make_ribbit_wav()
    try:
        if OS=="Darwin": subprocess.Popen(["afplay",_RIBBIT_PATH])
        elif OS=="Windows":
            import winsound
            winsound.PlaySound(_RIBBIT_PATH, winsound.SND_FILENAME|winsound.SND_ASYNC)
        else: subprocess.Popen(["aplay",_RIBBIT_PATH])
    except: pass

def play_ribbit_async():
    """Spawn sound in a daemon thread so the main thread is never touched."""
    threading.Thread(target=play_ribbit, daemon=True).start()


# ══════════════════════════════════════════════════════════════════════════════
#  macOS — PyObjC
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
        NSTrackingArea, NSTrackingMouseEnteredAndExited,
        NSTrackingActiveAlways, NSTrackingMouseMoved,
    )
    from Foundation import NSTimer, NSMakeRect, NSMakePoint

    FROG_LEVEL = 1000   # NSScreenSaverWindowLevel

    class FrogView(NSView):

        def initWithFrame_(self, frame):
            self = objc.super(FrogView, self).initWithFrame_(frame)
            if self is None: return None
            self._fc=0; self._blink_cd=random.randint(60,120)
            self._blinking=False; self._blink_f=0
            self._waving=False;   self._wave_f=0
            self._drag_origin=None; self._did_drag=False
            self._bubble_msg=None   # None = hidden
            self._hover_close=False
            self._win_ref=None
            # Flag set by background threads; consumed by tick_ on main thread
            self._remind_pending = False
            return self

        def isOpaque(self): return False
        def wantsDefaultClipping(self): return False
        def acceptsFirstMouse_(self, e): return True

        # Pass clicks through to windows below when in the transparent zone
        def hitTest_(self, pt):
            # Always respond in the frog zone (bottom FROG_H pixels)
            if pt.y <= FROG_H:
                return objc.super(FrogView, self).hitTest_(pt)
            # Respond in bubble zone only when bubble is visible
            if self._bubble_msg is not None:
                return objc.super(FrogView, self).hitTest_(pt)
            return None   # transparent → pass through

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
                sp=FROG_WAVE; self._wave_f-=1
                if self._wave_f<=0: self._waving=False
            elif self._blinking:
                sp=FROG_BLINK; self._blink_f-=1
                if self._blink_f<=0:
                    self._blinking=False; self._blink_cd=random.randint(60,120)
            else:
                sp=FROG_IDLE; self._blink_cd-=1
                if self._blink_cd<=0: self._blinking=True; self._blink_f=4
            for row in range(ROWS):
                for col in range(COLS):
                    cid=sp[row][col]
                    if cid==0: continue
                    rv,gv,bv=PALETTE[cid]
                    NSColor.colorWithCalibratedRed_green_blue_alpha_(
                        rv/255,gv/255,bv/255,1.0).set()
                    NSBezierPath.fillRect_(NSMakeRect(
                        FROG_X+col*PIXEL_SIZE,
                        (ROWS-1-row)*PIXEL_SIZE+bob,
                        PIXEL_SIZE,PIXEL_SIZE))

        def _draw_bubble(self):
            # ── Tail ──────────────────────────────────────────────────────────
            cy = WIN_W/2
            tail = NSBezierPath.bezierPath()
            tail.moveToPoint_(NSMakePoint(cy-11, FROG_TOP_Y+GAP+TAIL_H))
            tail.lineToPoint_(NSMakePoint(cy+11, FROG_TOP_Y+GAP+TAIL_H))
            tail.lineToPoint_(NSMakePoint(cy,    FROG_TOP_Y+GAP))
            tail.closePath()

            # ── Body ──────────────────────────────────────────────────────────
            r=14.0; bx=0; by=BUBBLE_BOT_Y; bw=WIN_W; bh=BUBBLE_BH
            body=NSBezierPath.bezierPath()
            body.moveToPoint_(NSMakePoint(bx+r, by+bh))
            body.lineToPoint_(NSMakePoint(bx+bw-r, by+bh))
            body.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
                NSMakePoint(bx+bw-r,by+bh-r),r,90,0)
            body.lineToPoint_(NSMakePoint(bx+bw,by+r))
            body.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
                NSMakePoint(bx+bw-r,by+r),r,0,270)
            body.lineToPoint_(NSMakePoint(bx+r,by))
            body.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
                NSMakePoint(bx+r,by+r),r,270,180)
            body.lineToPoint_(NSMakePoint(bx,by+bh-r))
            body.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(
                NSMakePoint(bx+r,by+bh-r),r,180,90)
            body.closePath()

            NSColor.colorWithCalibratedRed_green_blue_alpha_(
                1.0,0.90,0.05,0.97).set()
            body.fill(); tail.fill()
            NSColor.colorWithCalibratedRed_green_blue_alpha_(
                0.62,0.48,0.0,1.0).set()
            body.setLineWidth_(1.8); body.stroke()
            tail.setLineWidth_(1.8); tail.stroke()

            # ── Close button ──────────────────────────────────────────────────
            cbx=CLOSE_BX; cby=CLOSE_BY
            btn=NSBezierPath.bezierPathWithOvalInRect_(
                NSMakeRect(cbx-CLOSE_R,cby-CLOSE_R,CLOSE_R*2,CLOSE_R*2))
            if self._hover_close:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0.8,0.1,0.05,1.).set()
            else:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0.85,0.25,0.1,1.).set()
            btn.fill()
            NSColor.whiteColor().set()
            xp=NSBezierPath.bezierPath(); o=5.
            xp.moveToPoint_(NSMakePoint(cbx-o,cby-o))
            xp.lineToPoint_(NSMakePoint(cbx+o,cby+o))
            xp.moveToPoint_(NSMakePoint(cbx+o,cby-o))
            xp.lineToPoint_(NSMakePoint(cbx-o,cby+o))
            xp.setLineWidth_(2.2); xp.setLineCapStyle_(1); xp.stroke()

            # ── Text ──────────────────────────────────────────────────────────
            para=NSMutableParagraphStyle.alloc().init()
            para.setAlignment_(NSCenterTextAlignment)
            attrs={
                NSForegroundColorAttributeName:
                    NSColor.colorWithCalibratedRed_green_blue_alpha_(
                        0.1,0.07,0.0,1.0),
                NSFontAttributeName: NSFont.boldSystemFontOfSize_(12),
                NSParagraphStyleAttributeName: para,
            }
            tr=NSMakeRect(10, BUBBLE_BOT_Y+8, WIN_W-42, BUBBLE_BH-16)
            self._bubble_msg.drawInRect_withAttributes_(tr, attrs)

        # ── Timer tick (runs on main thread via NSTimer) ──────────────────────
        def tick_(self, _timer):
            # Consume any pending remind request set by background threads.
            # Doing it here means ALL AppKit calls stay on the main thread.
            if self._remind_pending:
                self._remind_pending = False
                self._do_remind()
            if self._win_ref:
                self._win_ref.orderFrontRegardless()
            self.setNeedsDisplay_(True)

        # ── Drag ─────────────────────────────────────────────────────────────
        def mouseDown_(self, event):
            self._drag_origin = event.locationInWindow()
            self._did_drag = False

        def mouseDragged_(self, event):
            self._did_drag = True
            loc = event.locationInWindow()
            f   = self.window().frame()
            self.window().setFrameOrigin_(NSMakePoint(
                f.origin.x + loc.x - self._drag_origin.x,
                f.origin.y + loc.y - self._drag_origin.y))

        def mouseUp_(self, event):
            if self._did_drag: return
            # Hit-test close button
            if self._bubble_msg is not None:
                loc=event.locationInWindow()
                dx=loc.x-CLOSE_BX; dy=loc.y-CLOSE_BY
                if dx*dx+dy*dy <= CLOSE_R*CLOSE_R:
                    self._bubble_msg=None
                    self._hover_close=False
                    self.setNeedsDisplay_(True)
                    return
            self._trigger_wave()

        def mouseMoved_(self, event):
            self._check_hover(event)

        def mouseEntered_(self, event):
            self._check_hover(event)

        def mouseExited_(self, event):
            if self._hover_close:
                self._hover_close=False; self.setNeedsDisplay_(True)

        def _check_hover(self, event):
            if self._bubble_msg is None: return
            loc=event.locationInWindow()
            dx=loc.x-CLOSE_BX; dy=loc.y-CLOSE_BY
            was=self._hover_close
            self._hover_close=(dx*dx+dy*dy<=CLOSE_R*CLOSE_R)
            if self._hover_close!=was: self.setNeedsDisplay_(True)

        # ── Right-click menu ──────────────────────────────────────────────────
        def rightMouseDown_(self, event):
            menu=NSMenu.alloc().initWithTitle_("FrogPal")
            for title,sel in [
                ("Wave! 🐸","waveAction:"),
                (None,None),
                ("Remind me now 💧","remindAction:"),
                ("Quit","quitAction:"),
            ]:
                if title is None: menu.addItem_(NSMenuItem.separatorItem())
                else:
                    item=NSMenuItem.alloc()\
                        .initWithTitle_action_keyEquivalent_(title,sel,"")
                    item.setTarget_(self); menu.addItem_(item)
            NSMenu.popUpContextMenu_withEvent_forView_(menu,event,self)

        def waveAction_(self,_):   self._trigger_wave()
        def remindAction_(self,_): self._remind_pending = True   # tick_ picks it up
        def quitAction_(self,_):   NSApp.terminate_(None)

        def _trigger_wave(self):
            if not self._waving: self._waving=True; self._wave_f=IDLE_FPS*2

        # ── Remind (show bubble) — only called from tick_ on main thread ─────
        def _do_remind(self):
            self._trigger_wave()
            play_ribbit_async()           # sound in background, never blocks main
            self._bubble_msg = random.choice(WATER_MSGS)
            self._hover_close = False
            # No setNeedsDisplay_ or orderFrontRegardless_ here —
            # tick_ already does both right after calling us.


    def run_macos():
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

        # Centre frog on screen (window is taller than frog due to bubble space)
        sf = NSScreen.mainScreen().frame()
        sx = sf.size.width/2  - WIN_W/2
        # Position so the FROG part is centred — bubble space is above
        sy = sf.size.height/2 - FROG_H/2

        win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(sx, sy, WIN_W, FULL_H),
            NSWindowStyleMaskBorderless, NSBackingStoreBuffered, False)
        win.setBackgroundColor_(NSColor.clearColor())
        win.setOpaque_(False)
        win.setHasShadow_(False)
        win.setLevel_(FROG_LEVEL)
        win.setCollectionBehavior_(1|16|64)   # CanJoinAllSpaces|Stationary|IgnoresCycle
        win.setHidesOnDeactivate_(False)
        win.setCanHide_(False)
        win.setIgnoresMouseEvents_(False)
        win.setAcceptsMouseMovedEvents_(True)

        view = FrogView.alloc().initWithFrame_(NSMakeRect(0,0,WIN_W,FULL_H))
        view._win_ref = win

        # Mouse tracking for hover effects
        ta = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            NSMakeRect(0,0,WIN_W,FULL_H),
            NSTrackingMouseEnteredAndExited | NSTrackingMouseMoved | NSTrackingActiveAlways,
            view, None)
        view.addTrackingArea_(ta)

        win.setContentView_(view)
        win.orderFrontRegardless()

        # Animation + stay-on-top timer
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0/IDLE_FPS, view, "tick:", None, True)

        # Pre-generate ribbit WAV so the first reminder plays without delay
        def _pregen():
            global _RIBBIT_PATH
            _RIBBIT_PATH = _make_ribbit_wav()
        threading.Thread(target=_pregen, daemon=True).start()

        # Test reminder: set flag after TEST_DELAY_SECS; tick_ does the rest
        def test_remind():
            time.sleep(TEST_DELAY_SECS)
            view._remind_pending = True   # read by tick_ on main thread

        threading.Thread(target=test_remind, daemon=True).start()

        # Scheduled reminder thread — only ever sets a boolean flag
        def reminder_loop():
            last_hour = -1
            while True:
                now=datetime.datetime.now(); h,m=now.hour,now.minute
                if h in REMINDER_HOURS and m==0 and h!=last_hour:
                    last_hour=h
                    view._remind_pending = True
                time.sleep(30)

        threading.Thread(target=reminder_loop, daemon=True).start()
        app.run()


# ══════════════════════════════════════════════════════════════════════════════
#  Windows / Linux — tkinter
# ══════════════════════════════════════════════════════════════════════════════
else:
    import tkinter as tk

    TC = "#010101"
    def _hex(p):
        if p==0: return TC
        r,g,b=PALETTE[p]; return f"#{r:02x}{g:02x}{b:02x}"

    def draw_sprite(canvas,sprite,ox,dy):
        canvas.delete("sprite")
        for r in range(ROWS):
            for c in range(COLS):
                cid=sprite[r][c]
                if cid==0: continue
                x0=ox+c*PIXEL_SIZE; y0=r*PIXEL_SIZE+dy
                canvas.create_rectangle(x0,y0,x0+PIXEL_SIZE,y0+PIXEL_SIZE,
                                        fill=_hex(cid),outline="",tags="sprite")

    class FrogPalTk:
        def __init__(self):
            self.root=tk.Tk()
            self.root.overrideredirect(True)
            self.root.attributes("-topmost",True)
            sw=self.root.winfo_screenwidth(); sh=self.root.winfo_screenheight()
            self._wx=sw//2-WIN_W//2; self._wy=sh//2-FROG_H//2
            self.root.geometry(f"{WIN_W}x{FROG_H}+{self._wx}+{self._wy}")
            self.root.configure(bg=TC)
            if OS=="Windows": self.root.attributes("-transparentcolor",TC)
            else: self.root.attributes("-alpha",0.95)

            self.canvas=tk.Canvas(self.root,width=WIN_W,height=FROG_H,
                bg=TC,highlightthickness=0,borderwidth=0)
            self.canvas.pack(); self._bubble_lbl=None

            self._fc=0; self._blink_cd=random.randint(60,120)
            self._blinking=False; self._blink_f=0
            self._waving=False; self._wave_f=0

            self.canvas.bind("<ButtonPress-1>",  self._ds)
            self.canvas.bind("<B1-Motion>",       self._dm)
            self.canvas.bind("<ButtonRelease-1>", self._du)
            self.canvas.bind("<Button-3>",        self._show_menu)

            self._menu=tk.Menu(self.root,tearoff=0)
            self._menu.add_command(label="Wave! 🐸",command=self._wave)
            self._menu.add_separator()
            self._menu.add_command(label="Remind me now 💧",command=self._remind)
            self._menu.add_separator()
            self._menu.add_command(label="Quit",command=self.root.destroy)

            self._animate()
            threading.Thread(target=self._test_remind,daemon=True).start()
            threading.Thread(target=self._reminder_loop,daemon=True).start()
            threading.Thread(target=play_ribbit,daemon=True).start()

        def _animate(self):
            self._fc+=1
            bob=int(2*(0.5-abs((self._fc%BOB_PERIOD)/BOB_PERIOD-0.5))*2)
            if self._waving:
                sp=FROG_WAVE; self._wave_f-=1
                if self._wave_f<=0: self._waving=False
            elif self._blinking:
                sp=FROG_BLINK; self._blink_f-=1
                if self._blink_f<=0:
                    self._blinking=False; self._blink_cd=random.randint(60,120)
            else:
                sp=FROG_IDLE; self._blink_cd-=1
                if self._blink_cd<=0: self._blinking=True; self._blink_f=4
            draw_sprite(self.canvas,sp,FROG_X,bob)
            self.root.attributes("-topmost",True)
            self.root.after(1000//IDLE_FPS,self._animate)

        def _ds(self,e): self._ox=e.x_root-self.root.winfo_x(); self._oy=e.y_root-self.root.winfo_y(); self._dd=False
        def _dm(self,e): self._dd=True; self.root.geometry(f"+{e.x_root-self._ox}+{e.y_root-self._oy}")
        def _du(self,e):
            if not self._dd: self._wave()
        def _show_menu(self,e):
            try: self._menu.tk_popup(e.x_root,e.y_root)
            finally: self._menu.grab_release()
        def _wave(self): self._waving=True; self._wave_f=IDLE_FPS*2

        def _show_bubble(self,msg):
            if self._bubble_lbl:
                try: self._bubble_lbl.destroy()
                except: pass
            frm=tk.Frame(self.root,bg="#ffe80a",
                         highlightbackground="#9a7000",highlightthickness=2)
            tk.Label(frm,text=msg,bg="#ffe80a",fg="#1a0a00",
                     font=("Arial",11,"bold"),wraplength=WIN_W-50,
                     justify="center").place(relx=0.42,rely=0.5,anchor="center")
            tk.Button(frm,text="✕",bg="#cc3010",fg="white",relief="flat",
                      font=("Arial",10,"bold"),cursor="hand2",
                      command=self._hide_bubble,padx=3
                      ).place(x=WIN_W-34,y=4,width=26,height=26)
            frm.place(x=0,y=0,width=WIN_W,height=BUBBLE_BH)
            self._bubble_lbl=frm
            # Expand window upward
            bh=BUBBLE_BH+TAIL_H+GAP
            wy=self.root.winfo_y(); wx=self.root.winfo_x()
            self.root.geometry(f"{WIN_W}x{FROG_H+bh}+{wx}+{wy-bh}")
            self.canvas.place(x=0,y=bh)

        def _hide_bubble(self):
            if self._bubble_lbl:
                try: self._bubble_lbl.destroy()
                except: pass; self._bubble_lbl=None
            bh=BUBBLE_BH+TAIL_H+GAP
            wy=self.root.winfo_y(); wx=self.root.winfo_x()
            self.root.geometry(f"{WIN_W}x{FROG_H}+{wx}+{wy+bh}")
            self.canvas.place(x=0,y=0)

        def _remind(self):
            self._wave(); play_ribbit_async()
            self._show_bubble(random.choice(WATER_MSGS))

        def _test_remind(self):
            time.sleep(TEST_DELAY_SECS)
            self.root.after(0,self._remind)

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
    if OS=="Darwin": run_macos()
    else: FrogPalTk().run()
