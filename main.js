const { app, BrowserWindow, ipcMain, screen } = require('electron')
const fs   = require('fs')
const path = require('path')

// ── Window dimensions ─────────────────────────────────────────────────────────
const WIN_W       = 240
const FROG_H      = 96
const BUBBLE_H    = 82
const TAIL_H      = 14
const GAP         = 4
const BUBBLE_AREA = BUBBLE_H + TAIL_H + GAP
const WIN_H       = BUBBLE_AREA + FROG_H

const TEST_DELAY_MS = 20_000

// ── Settings (persisted to userData/settings.json) ────────────────────────────
const SETTINGS_PATH = path.join(app.getPath('userData'), 'frogpal-settings.json')
const DEFAULTS = { soundEnabled: true, intervalMins: 120 }  // 120 min = 2 hrs

function loadSettings() {
  try {
    if (fs.existsSync(SETTINGS_PATH))
      return { ...DEFAULTS, ...JSON.parse(fs.readFileSync(SETTINGS_PATH, 'utf8')) }
  } catch (_) {}
  return { ...DEFAULTS }
}

function saveSettings(s) {
  try { fs.writeFileSync(SETTINGS_PATH, JSON.stringify(s, null, 2)) } catch (_) {}
}

let settings = loadSettings()

// ── Windows ───────────────────────────────────────────────────────────────────
let win         = null
let settingsWin = null

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

  // Context menu is now fully custom HTML — handled in renderer.js

  // ── Settings IPC ──────────────────────────────────────────────────────────
  ipcMain.on('open-settings', openSettings)

  ipcMain.handle('get-settings', () => settings)

  ipcMain.on('save-settings', (_, newSettings) => {
    settings = newSettings
    saveSettings(settings)
    win.webContents.send('settings-updated', settings)
    if (settingsWin) settingsWin.webContents.send('settings-saved')
  })

  ipcMain.on('close-settings', () => settingsWin?.close())
  ipcMain.on('quit', () => app.quit())

  // ── Initial settings push to renderer ────────────────────────────────────
  win.webContents.on('did-finish-load', () => {
    win.webContents.send('settings-updated', settings)
  })

  // ── Test reminder (20 s after launch) ─────────────────────────────────────
  setTimeout(() => win.webContents.send('remind', settings), TEST_DELAY_MS)

  // ── Scheduled reminders ───────────────────────────────────────────────────
  const fired = new Set()
  setInterval(() => {
    const now   = new Date()
    const h     = now.getHours()
    const m     = now.getMinutes()
    const total = h * 60 + m
    if (total < 6 * 60 || total > 22 * 60) return   // outside 6am–10pm
    if (total % settings.intervalMins > 1)  return   // not on the interval
    const key = `${now.toDateString()}-${total}`
    if (fired.has(key)) return
    fired.add(key)
    win.webContents.send('remind', settings)
  }, 60_000)
})

// ── Settings window ───────────────────────────────────────────────────────────
function openSettings() {
  if (settingsWin) { settingsWin.focus(); return }
  settingsWin = new BrowserWindow({
    width: 320, height: 300,
    frame: false, resizable: false,
    alwaysOnTop: true, transparent: false,
    webPreferences: { nodeIntegration: true, contextIsolation: false },
  })
  settingsWin.loadFile('settings.html')
  settingsWin.on('closed', () => { settingsWin = null })
}

app.on('window-all-closed', () => app.quit())
