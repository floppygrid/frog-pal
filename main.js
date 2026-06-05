const { app, BrowserWindow, ipcMain, Menu, screen } = require('electron')

// ── Dimensions ────────────────────────────────────────────────────────────────
const WIN_W        = 240
const FROG_H       = 96
const BUBBLE_H     = 82   // bubble body
const TAIL_H       = 14   // tail triangle
const GAP          = 4
const BUBBLE_AREA  = BUBBLE_H + TAIL_H + GAP   // 100
const WIN_H        = BUBBLE_AREA + FROG_H       // 196

// ── Reminder schedule ─────────────────────────────────────────────────────────
const REMINDER_HOURS = new Set([6, 8, 10, 12, 14, 16, 18, 20, 22])
const TEST_DELAY_MS  = 20_000

let win
let dragInterval = null
let dragOffsetX  = 0
let dragOffsetY  = 0

// ── Window creation ───────────────────────────────────────────────────────────
app.whenReady().then(() => {
  if (process.platform === 'darwin') app.dock.hide()

  const { width: sw, height: sh } = screen.getPrimaryDisplay().workAreaSize

  // Position so the FROG is centred — bubble space is above it
  const winX = Math.round(sw / 2 - WIN_W / 2)
  const winY = Math.round(sh / 2 - BUBBLE_AREA - FROG_H / 2)

  win = new BrowserWindow({
    width:       WIN_W,
    height:      WIN_H,
    x:           winX,
    y:           winY,
    transparent: true,
    frame:       false,
    resizable:   false,
    movable:     false,      // we handle movement ourselves via IPC
    skipTaskbar: true,
    alwaysOnTop: true,
    hasShadow:   false,
    focusable:   true,
    webPreferences: {
      nodeIntegration:  true,
      contextIsolation: false,
    },
  })

  // Highest possible window level on macOS — stays above everything
  win.setAlwaysOnTop(true, 'screen-saver')
  win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true })

  win.loadFile('index.html')

  // ── Click-through for transparent areas ──────────────────────────────────
  // Start by ignoring mouse (clicks pass through to whatever is below)
  win.setIgnoreMouseEvents(true, { forward: true })

  ipcMain.on('mouse-enter-ui', () => win.setIgnoreMouseEvents(false))
  ipcMain.on('mouse-leave-ui', () => win.setIgnoreMouseEvents(true, { forward: true }))

  // ── Drag ─────────────────────────────────────────────────────────────────
  ipcMain.on('drag-start', () => {
    const { x: mx, y: my } = screen.getCursorScreenPoint()
    const [wx, wy] = win.getPosition()
    dragOffsetX = mx - wx
    dragOffsetY = my - wy
    if (dragInterval) clearInterval(dragInterval)
    dragInterval = setInterval(() => {
      const { x, y } = screen.getCursorScreenPoint()
      win.setPosition(x - dragOffsetX, y - dragOffsetY)
    }, 16)
  })

  ipcMain.on('drag-end', () => {
    if (dragInterval) { clearInterval(dragInterval); dragInterval = null }
  })

  // ── Context menu ─────────────────────────────────────────────────────────
  ipcMain.on('context-menu', () => {
    const menu = Menu.buildFromTemplate([
      { label: '🐸  Wave!',           click: () => win.webContents.send('wave') },
      { type: 'separator' },
      { label: '💧  Remind me now',   click: () => win.webContents.send('remind') },
      { type: 'separator' },
      { label: 'Quit',                click: () => app.quit() },
    ])
    menu.popup({ window: win })
  })

  // ── Reminders ────────────────────────────────────────────────────────────
  // Test reminder 20 s after launch
  setTimeout(() => win.webContents.send('remind'), TEST_DELAY_MS)

  // Check every 60 s. Track fired reminders by "YYYY-MM-DD-HH" so each
  // scheduled hour fires exactly once per day, no matter how many ticks land.
  const fired = new Set()

  setInterval(() => {
    const now  = new Date()
    const h    = now.getHours()
    const m    = now.getMinutes()
    if (!REMINDER_HOURS.has(h)) return          // not a reminder hour
    if (m > 1) return                           // only fire within first 2 min of the hour
    const key = `${now.toDateString()}-${h}`
    if (fired.has(key)) return                  // already fired this hour today
    fired.add(key)
    win.webContents.send('remind')
  }, 60_000)   // check every 60 seconds
})

app.on('window-all-closed', () => app.quit())
