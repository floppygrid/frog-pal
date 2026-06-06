const { ipcRenderer } = require('electron')

// ── Pixel art config ──────────────────────────────────────────────────────────
const PS   = 6        // pixel size
const COLS = 16
const ROWS = 16
const FW   = COLS * PS   // frog width  = 96
const FH   = ROWS * PS   // frog height = 96
const OX   = (240 - FW) / 2   // x offset to centre frog in 240-wide canvas = 72
const FPS  = 8
const BOB  = 24        // bob period frames

const PALETTE = {
  1: '#2d6a2d', 2: '#4caf50', 3: '#81c784',
  4: '#1b5e20', 5: '#ffffff', 6: '#212121', 7: '#f48fb1',
}

const IDLE = [
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
const BLINK = [
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
const WAVE = [
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

const MSGS = [
  'Sip sip hooray! Drink water and thrive again! 🥤',
  'You are a plant. You need water. This is science! 🌿',
  'Hydration check! Drink your water! 💧',
  'Hydrated you = glowing, thriving, unstoppable you. ✨',
  'One sip at a time. It\'s time to hydrate! 🐸',
  'Did you know? Water is necessary for your brain! Drink that water! 🧠',
  'Your brain is basically 75% water. Keep the vibes flowing! 💦',
  'Breaking news: A local frog wants you to drink your water again. 📰',
  'Water break! Consider it a mini spa moment — just for your insides. 🛁',
  'A sip at a time keeps the dry skin away. Keep glowing! 🌟',
  'Splash splash~ Drink some water! 🐸',
]

// ── DOM refs ──────────────────────────────────────────────────────────────────
const canvas     = document.getElementById('frog-canvas')
const ctx        = canvas.getContext('2d')
const bubbleWrap = document.getElementById('bubble-wrap')
const bubbleText = document.getElementById('bubble-text')
const closeBtn   = document.getElementById('bubble-close')

ctx.imageSmoothingEnabled = false

// ── Animation state ───────────────────────────────────────────────────────────
let frame    = 0
let blinkCd  = randInt(60, 120)
let blinking = false, blinkF = 0
let waving   = false, waveF  = 0

function randInt(a, b) { return Math.floor(Math.random() * (b - a)) + a }

function drawSprite(sprite, bobY) {
  ctx.clearRect(0, 0, 240, 96)
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const id = sprite[r][c]
      if (id === 0) continue
      ctx.fillStyle = PALETTE[id]
      ctx.fillRect(OX + c * PS, r * PS + bobY, PS, PS)
    }
  }
}

function animate() {
  frame++
  const bob = Math.round(2 * (0.5 - Math.abs((frame % BOB) / BOB - 0.5)) * 2)

  let sprite
  if (waving) {
    sprite = WAVE; waveF--
    if (waveF <= 0) waving = false
  } else if (blinking) {
    sprite = BLINK; blinkF--
    if (blinkF <= 0) { blinking = false; blinkCd = randInt(60, 120) }
  } else {
    sprite = IDLE; blinkCd--
    if (blinkCd <= 0) { blinking = true; blinkF = 4 }
  }

  drawSprite(sprite, bob)
  setTimeout(animate, 1000 / FPS)
}
animate()

// ── Bubble ────────────────────────────────────────────────────────────────────
function showBubble(msg) {
  bubbleText.textContent = msg
  bubbleWrap.classList.add('visible')
}
function hideBubble() {
  bubbleWrap.classList.remove('visible')
}
closeBtn.addEventListener('click', hideBubble)

// ── Ribbit sound (Web Audio API — no files needed) ────────────────────────────
function playRibbit() {
  try {
    const ac = new AudioContext()
    const chirp = (t0, base, dur) => {
      [[1, 0.35], [2, 0.15], [3, 0.06]].forEach(([mul, vol]) => {
        const osc  = ac.createOscillator()
        const gain = ac.createGain()
        osc.connect(gain); gain.connect(ac.destination)
        osc.frequency.setValueAtTime(base * mul * 0.8, t0)
        osc.frequency.linearRampToValueAtTime(base * mul * 1.5, t0 + dur * 0.3)
        osc.frequency.linearRampToValueAtTime(base * mul * 0.65, t0 + dur)
        gain.gain.setValueAtTime(0, t0)
        gain.gain.linearRampToValueAtTime(vol, t0 + 0.01)
        gain.gain.linearRampToValueAtTime(0, t0 + dur)
        osc.start(t0); osc.stop(t0 + dur)
      })
    }
    const now = ac.currentTime
    chirp(now,        400, 0.13)
    chirp(now + 0.18, 440, 0.10)
    chirp(now + 0.35, 380, 0.11)
    chirp(now + 0.50, 420, 0.09)
  } catch (e) {}
}

// ── Drag ──────────────────────────────────────────────────────────────────────
let dragStartX = 0, dragStartY = 0, didDrag = false

canvas.addEventListener('mousedown', e => {
  if (e.button !== 0) return
  dragStartX = e.clientX; dragStartY = e.clientY
  didDrag = false
  ipcRenderer.send('drag-start')
})

document.addEventListener('mousemove', e => {
  if (Math.abs(e.clientX - dragStartX) + Math.abs(e.clientY - dragStartY) > 3)
    didDrag = true
})

document.addEventListener('mouseup', e => {
  if (e.button !== 0) return
  ipcRenderer.send('drag-end')
  if (!didDrag) { waving = true; waveF = FPS * 2 }
})

// ── Context menu ──────────────────────────────────────────────────────────────
canvas.addEventListener('contextmenu', e => {
  e.preventDefault()
  ipcRenderer.send('context-menu')
})
bubbleWrap.addEventListener('contextmenu', e => {
  e.preventDefault()
  ipcRenderer.send('context-menu')
})

// ── Mouse hit-test → pass clicks through transparent areas ───────────────────
// The main process starts with setIgnoreMouseEvents(true, {forward:true}).
// We track mouse position here and tell it to stop ignoring when over visible UI.
document.addEventListener('mousemove', e => {
  const el = document.elementFromPoint(e.clientX, e.clientY)
  // "over UI" = over canvas or the visible bubble
  const overUI = el === canvas ||
    (bubbleWrap.classList.contains('visible') && bubbleWrap.contains(el))
  if (overUI) ipcRenderer.send('mouse-enter-ui')
  else        ipcRenderer.send('mouse-leave-ui')
})

// ── Settings state ────────────────────────────────────────────────────────────
let soundEnabled = true

ipcRenderer.on('settings-updated', (_, s) => {
  soundEnabled = s.soundEnabled
})

// ── IPC from main ─────────────────────────────────────────────────────────────
ipcRenderer.on('remind', (_, s) => {
  if (s) soundEnabled = s.soundEnabled
  waving = true; waveF = FPS * 2
  if (soundEnabled) playRibbit()
  showBubble(MSGS[Math.floor(Math.random() * MSGS.length)])
})

ipcRenderer.on('wave', () => {
  waving = true; waveF = FPS * 2
})
