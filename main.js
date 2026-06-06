const { app, BrowserWindow, ipcMain, screen } = require('electron')
const fs   = require('fs')
const path = require('path')

// ── Window dimensions ─────────────────────────────────────────────────────────
const WIN_W        = 240
const FROG_H       = 96
const BUBBLE_H     = 82
const TAIL_H       = 14
const GAP          = 4
const BUBBLE_AREA  = BUBBLE_H + TAIL_H + GAP
const MENU_RESERVE = 170
const WIN_H        = BUBBLE_AREA + FROG_H + MENU_RESERVE   // 366

const TEST_DELAY_MS  = 20_000
const GAP_FROM_FROG  = 40

// ── Persist helpers ───────────────────────────────────────────────────────────
const SETTINGS_PATH = path.join(app.getPath('userData'), 'frogpal-settings.json')
const TODO_PATH     = path.join(app.getPath('userData'), 'frogpal-todo.json')
const STICKY_PATH   = path.join(app.getPath('userData'), 'frogpal-stickies.json')

const DEFAULTS_SETTINGS = { soundEnabled: true, intervalMins: 120 }

function readJSON(p, fallback) {
  try { if (fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, 'utf8')) } catch (_) {}
  return fallback
}
function writeJSON(p, data) {
  try { fs.writeFileSync(p, JSON.stringify(data, null, 2)) } catch (_) {}
}

let settings = { ...DEFAULTS_SETTINGS, ...readJSON(SETTINGS_PATH, {}) }

// ── Windows ───────────────────────────────────────────────────────────────────
let win            = null
let settingsWin    = null
let todoWin        = null
let reminderDlgWin = null
const stickyWins   = new Map()   // id → BrowserWindow
let nextStickyId   = 1

// ── Helper: spawn a panel near the frog ──────────────────────────────────────
function spawnNear(file, w, h, opts = {}) {
  const { width: scrW, height: scrH } = screen.getPrimaryDisplay().workAreaSize
  const [fx, fy] = win.getPosition()
  const frogCY   = fy + BUBBLE_AREA + FROG_H / 2
  let   sx       = fx + WIN_W + GAP_FROM_FROG
  let   sy       = Math.round(frogCY - h / 2)
  if (sx + w > scrW) sx = fx - w - GAP_FROM_FROG
  sx = Math.max(0, Math.min(sx, scrW - w))
  sy = Math.max(0, Math.min(sy, scrH - h))
  const bw = new BrowserWindow({
    width: w, height: h, x: sx, y: sy,
    frame: false, resizable: true,
    alwaysOnTop: true, transparent: false,
    webPreferences: { nodeIntegration: true, contextIsolation: false },
    ...opts,
  })
  bw.loadFile(file)
  return bw
}

app.whenReady().then(() => {
  if (process.platform === 'darwin') app.dock.hide()

  const { width: sw, height: sh } = screen.getPrimaryDisplay().workAreaSize
  const winX = Math.round(sw / 2 - WIN_W / 2)
  const winY = Math.round(sh / 2 - BUBBLE_AREA - FROG_H / 2)

  // ── Frog window ──────────────────────────────────────────────────────────
  win = new BrowserWindow({
    width: WIN_W, height: WIN_H, x: winX, y: winY,
    transparent: true, frame: false, resizable: false,
    movable: false, skipTaskbar: true, alwaysOnTop: true, hasShadow: false,
    webPreferences: { nodeIntegration: true, contextIsolation: false },
  })
  win.setAlwaysOnTop(true, 'screen-saver')
  win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true })
  win.loadFile('index.html')
  win.setIgnoreMouseEvents(true, { forward: true })

  // ── Click-through ─────────────────────────────────────────────────────────
  ipcMain.on('mouse-enter-ui', () => win.setIgnoreMouseEvents(false))
  ipcMain.on('mouse-leave-ui', () => win.setIgnoreMouseEvents(true, { forward: true }))

  // ── Drag ──────────────────────────────────────────────────────────────────
  let dragInterval = null, dragOffX = 0, dragOffY = 0
  ipcMain.on('drag-start', () => {
    const { x: mx, y: my } = screen.getCursorScreenPoint()
    const [wx, wy] = win.getPosition()
    dragOffX = mx - wx; dragOffY = my - wy
    if (dragInterval) clearInterval(dragInterval)
    dragInterval = setInterval(() => {
      const { x, y } = screen.getCursorScreenPoint()
      win.setPosition(x - dragOffX, y - dragOffY)
    }, 16)
  })
  ipcMain.on('drag-end', () => {
    if (dragInterval) { clearInterval(dragInterval); dragInterval = null }
  })

  // ── Settings ──────────────────────────────────────────────────────────────
  ipcMain.on('open-settings', openSettings)
  ipcMain.handle('get-settings', () => settings)
  ipcMain.on('save-settings', (_, s) => {
    settings = s; writeJSON(SETTINGS_PATH, s)
    win.webContents.send('settings-updated', s)
    settingsWin?.webContents.send('settings-saved')
  })
  ipcMain.on('close-settings', () => settingsWin?.close())
  ipcMain.on('quit', () => app.quit())

  win.webContents.on('did-finish-load', () => {
    win.webContents.send('settings-updated', settings)
    win.webContents.send('sticky-count', stickyWins.size)
  })

  // ── Water reminders ───────────────────────────────────────────────────────
  setTimeout(() => win.webContents.send('remind', settings), TEST_DELAY_MS)
  const fired = new Set()
  setInterval(() => {
    const now = new Date(), h = now.getHours(), m = now.getMinutes()
    const total = h * 60 + m
    if (total < 360 || total > 1320) return
    if (total % settings.intervalMins > 1) return
    const key = `${now.toDateString()}-${total}`
    if (fired.has(key)) return
    fired.add(key)
    win.webContents.send('remind', settings)
  }, 60_000)

  // ── Todo ──────────────────────────────────────────────────────────────────
  ipcMain.on('open-todo', () => {
    if (todoWin) { todoWin.focus(); return }
    todoWin = spawnNear('todo.html', 320, 460)
    todoWin.on('closed', () => { todoWin = null })
  })
  ipcMain.handle('load-todo', () => readJSON(TODO_PATH, []))
  ipcMain.on('save-todo', (_, items) => writeJSON(TODO_PATH, items))

  // ── Sticky notes ──────────────────────────────────────────────────────────
  ipcMain.on('open-sticky', (_, color) => {
    if (stickyWins.size >= 10) return
    const id  = nextStickyId++
    const { width: scrW, height: scrH } = screen.getPrimaryDisplay().workAreaSize
    // Cascade from top-right
    const col = (stickyWins.size % 5)
    const row = Math.floor(stickyWins.size / 5)
    const sx  = Math.min(scrW - 200, 60 + col * 30)
    const sy  = Math.min(scrH - 200, 60 + row * 30 + col * 20)

    const sw = new BrowserWindow({
      width: 210, height: 210,
      x: sx, y: sy,
      frame: false, resizable: true,
      alwaysOnTop: true, transparent: true, hasShadow: false,
      webPreferences: { nodeIntegration: true, contextIsolation: false },
    })
    sw.loadFile('sticky.html', { query: { id: String(id), color } })
    stickyWins.set(id, sw)
    win.webContents.send('sticky-count', stickyWins.size)

    sw.on('closed', () => {
      stickyWins.delete(id)
      win.webContents.send('sticky-count', stickyWins.size)
      // Persist remaining stickies (content saved by renderer before close)
    })
  })
  ipcMain.handle('get-sticky-count', () => stickyWins.size)

  ipcMain.on('save-sticky', (_, { id, content, color }) => {
    const all = readJSON(STICKY_PATH, {})
    all[id] = { content, color }
    writeJSON(STICKY_PATH, all)
  })
  ipcMain.on('delete-sticky', (_, id) => {
    const all = readJSON(STICKY_PATH, {})
    delete all[id]
    writeJSON(STICKY_PATH, all)
  })
  ipcMain.on('close-sticky', (_, id) => {
    stickyWins.get(id)?.close()
  })

  // ── Custom reminder dialog ────────────────────────────────────────────────
  ipcMain.on('open-reminder-dialog', () => {
    if (reminderDlgWin) { reminderDlgWin.focus(); return }
    reminderDlgWin = spawnNear('reminder-dialog.html', 300, 230, { resizable: false })
    reminderDlgWin.on('closed', () => { reminderDlgWin = null })
  })
  ipcMain.on('close-reminder-dialog', () => reminderDlgWin?.close())

  ipcMain.on('set-custom-reminder', (_, { text, delayMs }) => {
    reminderDlgWin?.close()
    setTimeout(() => {
      win.webContents.send('custom-remind', text)
    }, delayMs)
  })
})

// ── Settings window ───────────────────────────────────────────────────────────
function openSettings() {
  if (settingsWin) { settingsWin.focus(); return }
  const { width: scrW, height: scrH } = screen.getPrimaryDisplay().workAreaSize
  const [fx, fy] = win.getPosition()
  const frogCY   = fy + BUBBLE_AREA + FROG_H / 2
  let sx = fx + WIN_W + GAP_FROM_FROG
  let sy = Math.round(frogCY - 300 / 2)
  if (sx + 320 > scrW) sx = fx - 320 - GAP_FROM_FROG
  sx = Math.max(0, Math.min(sx, scrW - 320))
  sy = Math.max(0, Math.min(sy, scrH - 300))
  settingsWin = new BrowserWindow({
    width: 320, height: 300, x: sx, y: sy,
    frame: false, resizable: false, alwaysOnTop: true,
    webPreferences: { nodeIntegration: true, contextIsolation: false },
  })
  settingsWin.loadFile('settings.html')
  settingsWin.on('closed', () => { settingsWin = null })
}

app.on('window-all-closed', () => app.quit())
