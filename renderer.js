const { ipcRenderer } = require('electron')

// ── Pixel art config ──────────────────────────────────────────────────────────
const PS   = 6
const COLS = 16, ROWS = 16
const FW   = COLS * PS
const OX   = (240 - FW) / 2   // 72 — centres 96px sprite in 240px canvas
const FPS  = 8
const BOB  = 24

// ══════════════════════════════════════════════════════════════════════════════
//  CHARACTERS
// ══════════════════════════════════════════════════════════════════════════════
const CHARACTERS = {

  // ── FROG (green) ────────────────────────────────────────────────────────────
  frog: {
    label: '🐸 FROG',
    theme: { border: '#1a6b1a', bubbleBg: '#ffb3cc', tailBorder: '#1a6b1a' },
    palette: {
      1:'#2d6a2d', 2:'#4caf50', 3:'#81c784',
      4:'#1b5e20', 5:'#ffffff', 6:'#212121', 7:'#f48fb1',
    },
    idle: [
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
    ],
    blink: [
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
    ],
    wave: [
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
    ],
  },

  // ── CAT (orange) ────────────────────────────────────────────────────────────
  cat: {
    label: '🐱 CAT',
    theme: { border: '#b35a00', bubbleBg: '#ffe4cc', tailBorder: '#b35a00' },
    palette: {
      1:'#7b3b00', 2:'#ff8c00', 3:'#ffaa44',
      4:'#5c2d00', 5:'#ffffff', 6:'#222222', 7:'#ffb6c1',
    },
    idle: [
      [0,1,1,0,0,0,0,0,0,0,0,0,0,1,1,0],  // pointed ears
      [1,2,2,1,0,0,0,0,0,0,0,0,1,2,2,1],
      [1,2,2,2,1,1,1,1,1,1,1,1,2,2,2,1],  // ears join head
      [0,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
      [0,1,2,5,5,2,2,2,2,2,5,5,2,2,1,0],  // eye whites
      [0,1,2,5,6,2,2,2,2,2,5,6,2,2,1,0],  // pupils
      [0,0,1,2,2,2,7,2,2,7,2,2,2,1,0,0],  // nose + whisker hints
      [0,0,1,2,2,2,2,7,7,2,2,2,2,1,0,0],  // mouth
      [0,0,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
      [0,1,2,2,2,3,3,3,3,3,3,2,2,2,1,0],  // body belly
      [0,1,2,2,3,3,3,3,3,3,3,3,2,2,1,0],
      [0,1,2,2,3,3,3,3,3,3,3,3,2,2,1,0],
      [0,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
      [1,2,1,2,2,2,2,2,2,2,2,2,2,1,2,1],
      [1,2,2,1,1,1,2,2,2,2,1,1,1,2,2,1],
      [0,1,1,0,0,0,1,1,1,1,0,0,0,1,1,0],
    ],
    blink: [
      [0,1,1,0,0,0,0,0,0,0,0,0,0,1,1,0],
      [1,2,2,1,0,0,0,0,0,0,0,0,1,2,2,1],
      [1,2,2,2,1,1,1,1,1,1,1,1,2,2,2,1],
      [0,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
      [0,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
      [0,1,2,1,1,1,2,2,2,2,1,1,1,2,1,0],  // eyes closed
      [0,0,1,2,2,2,7,2,2,7,2,2,2,1,0,0],
      [0,0,1,2,2,2,2,7,7,2,2,2,2,1,0,0],
      [0,0,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
      [0,1,2,2,2,3,3,3,3,3,3,2,2,2,1,0],
      [0,1,2,2,3,3,3,3,3,3,3,3,2,2,1,0],
      [0,1,2,2,3,3,3,3,3,3,3,3,2,2,1,0],
      [0,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
      [1,2,1,2,2,2,2,2,2,2,2,2,2,1,2,1],
      [1,2,2,1,1,1,2,2,2,2,1,1,1,2,2,1],
      [0,1,1,0,0,0,1,1,1,1,0,0,0,1,1,0],
    ],
    wave: [
      [0,1,1,0,0,0,0,0,0,0,0,0,0,1,1,0],
      [1,2,2,1,0,0,0,0,0,0,0,0,1,2,2,1],
      [1,2,2,2,1,1,1,1,1,1,1,1,2,2,2,1],
      [0,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
      [0,1,2,5,5,2,2,2,2,2,5,5,2,2,1,0],
      [0,1,2,5,6,2,2,2,2,2,5,6,2,2,1,0],
      [0,0,1,2,2,2,7,2,2,7,2,2,2,1,0,0],
      [0,0,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
      [1,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],  // arm raised
      [1,2,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
      [0,1,1,2,2,2,3,3,3,3,2,2,2,1,2,1],
      [0,0,1,1,1,3,3,3,3,3,3,1,1,2,2,1],
      [0,0,0,0,1,2,2,2,2,2,1,0,0,1,2,1],
      [0,0,0,0,0,1,1,1,1,1,0,0,0,0,1,0],
      [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    ],
  },

  // ── BUNNY (pink) ────────────────────────────────────────────────────────────
  bunny: {
    label: '🐰 BUNNY',
    theme: { border: '#b5275e', bubbleBg: '#ffe4f0', tailBorder: '#b5275e' },
    palette: {
      1:'#9c2752', 2:'#ffb6c1', 3:'#ffcdd2',
      4:'#c2185b', 5:'#ffffff', 6:'#444444', 7:'#ff69b4',
    },
    idle: [
      [0,0,0,1,1,0,0,0,0,0,1,1,0,0,0,0],  // long ear tips
      [0,0,1,2,2,1,0,0,0,1,2,2,1,0,0,0],
      [0,0,1,7,2,1,0,0,0,1,7,2,1,0,0,0],  // inner ear pink
      [0,0,1,2,2,1,0,0,0,1,2,2,1,0,0,0],
      [0,0,0,1,1,1,1,1,1,1,1,1,0,0,0,0],  // head top
      [0,0,1,2,2,2,2,2,2,2,2,2,1,0,0,0],
      [0,0,1,5,6,5,2,2,2,5,6,5,1,0,0,0],  // eyes
      [0,0,0,1,2,2,2,7,2,2,2,1,0,0,0,0],  // nose
      [0,0,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
      [0,1,2,2,2,3,3,3,3,3,3,2,2,2,1,0],  // belly
      [0,1,2,2,3,3,3,3,3,3,3,3,2,2,1,0],
      [0,1,2,2,3,3,3,3,3,3,3,3,2,2,1,0],
      [0,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
      [1,2,1,2,2,2,2,2,2,2,2,2,2,1,2,1],
      [1,2,2,1,1,1,2,2,2,2,1,1,1,2,2,1],
      [0,1,1,0,0,0,1,1,1,1,0,0,0,1,1,0],
    ],
    blink: [
      [0,0,0,1,1,0,0,0,0,0,1,1,0,0,0,0],
      [0,0,1,2,2,1,0,0,0,1,2,2,1,0,0,0],
      [0,0,1,7,2,1,0,0,0,1,7,2,1,0,0,0],
      [0,0,1,2,2,1,0,0,0,1,2,2,1,0,0,0],
      [0,0,0,1,1,1,1,1,1,1,1,1,0,0,0,0],
      [0,0,1,2,2,2,2,2,2,2,2,2,1,0,0,0],
      [0,0,1,1,1,1,2,2,2,1,1,1,1,0,0,0],  // eyes closed
      [0,0,0,1,2,2,2,7,2,2,2,1,0,0,0,0],
      [0,0,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
      [0,1,2,2,2,3,3,3,3,3,3,2,2,2,1,0],
      [0,1,2,2,3,3,3,3,3,3,3,3,2,2,1,0],
      [0,1,2,2,3,3,3,3,3,3,3,3,2,2,1,0],
      [0,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
      [1,2,1,2,2,2,2,2,2,2,2,2,2,1,2,1],
      [1,2,2,1,1,1,2,2,2,2,1,1,1,2,2,1],
      [0,1,1,0,0,0,1,1,1,1,0,0,0,1,1,0],
    ],
    wave: [
      [0,0,0,1,1,0,0,0,0,0,1,1,0,0,0,0],
      [0,0,1,2,2,1,0,0,0,1,2,2,1,0,0,0],
      [0,0,1,7,2,1,0,0,0,1,7,2,1,0,0,0],
      [0,0,1,2,2,1,0,0,0,1,2,2,1,0,0,0],
      [0,0,0,1,1,1,1,1,1,1,1,1,0,0,0,0],
      [0,0,1,2,2,2,2,2,2,2,2,2,1,0,0,0],
      [0,0,1,5,6,5,2,2,2,5,6,5,1,0,0,0],
      [0,0,0,1,2,2,2,7,2,2,2,1,0,0,0,0],
      [1,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],  // arm raised
      [1,2,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
      [0,1,1,2,2,2,3,3,3,3,2,2,2,1,2,1],
      [0,0,1,1,1,3,3,3,3,3,3,1,1,2,2,1],
      [0,0,0,0,1,2,2,2,2,2,1,0,0,1,2,1],
      [0,0,0,0,0,1,1,1,1,1,0,0,0,0,1,0],
      [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    ],
  },

  // ── DRAGON (black/dark) ──────────────────────────────────────────────────────
  dragon: {
    label: '🐲 DRAGON',
    theme: { border: '#222222', bubbleBg: '#e8e8e8', tailBorder: '#222222' },
    palette: {
      1:'#1a1a1a', 2:'#3d3d3d', 3:'#5a5a5a',
      4:'#000000', 5:'#ff3300', 6:'#ff6600', 7:'#8b0000',
    },
    idle: [
      [0,0,1,4,1,0,0,0,0,0,0,1,4,1,0,0],  // sharp horns
      [0,0,1,4,1,0,0,0,0,0,0,1,4,1,0,0],
      [0,0,0,1,2,1,1,1,1,1,1,2,1,0,0,0],  // head
      [0,0,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
      [0,0,1,2,5,2,2,2,2,2,2,5,2,1,0,0],  // glowing red eyes
      [0,0,1,2,7,2,2,6,6,2,2,7,2,1,0,0],  // fire detail
      [0,0,0,1,2,2,2,2,2,2,2,2,1,0,0,0],  // jaw
      [0,0,0,1,2,7,7,2,2,7,7,2,1,0,0,0],  // teeth
      [0,1,1,2,2,2,2,2,2,2,2,2,2,1,1,0],  // wing hints on sides
      [1,2,1,2,2,2,3,3,3,3,2,2,2,1,2,1],
      [1,2,1,2,2,3,3,3,3,3,3,2,2,1,2,1],
      [0,1,2,2,2,3,3,3,3,3,3,2,2,2,1,0],
      [0,0,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
      [0,1,2,1,2,2,2,2,2,2,2,2,1,2,1,0],
      [0,1,2,2,1,1,1,2,2,1,1,1,2,2,1,0],
      [0,0,1,1,0,0,0,1,1,0,0,0,1,1,0,0],
    ],
    blink: [
      [0,0,1,4,1,0,0,0,0,0,0,1,4,1,0,0],
      [0,0,1,4,1,0,0,0,0,0,0,1,4,1,0,0],
      [0,0,0,1,2,1,1,1,1,1,1,2,1,0,0,0],
      [0,0,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
      [0,0,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
      [0,0,1,2,1,1,1,2,2,1,1,1,2,1,0,0],  // eyes closed
      [0,0,0,1,2,2,2,2,2,2,2,2,1,0,0,0],
      [0,0,0,1,2,7,7,2,2,7,7,2,1,0,0,0],
      [0,1,1,2,2,2,2,2,2,2,2,2,2,1,1,0],
      [1,2,1,2,2,2,3,3,3,3,2,2,2,1,2,1],
      [1,2,1,2,2,3,3,3,3,3,3,2,2,1,2,1],
      [0,1,2,2,2,3,3,3,3,3,3,2,2,2,1,0],
      [0,0,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
      [0,1,2,1,2,2,2,2,2,2,2,2,1,2,1,0],
      [0,1,2,2,1,1,1,2,2,1,1,1,2,2,1,0],
      [0,0,1,1,0,0,0,1,1,0,0,0,1,1,0,0],
    ],
    wave: [
      [0,0,1,4,1,0,0,0,0,0,0,1,4,1,0,0],
      [0,0,1,4,1,0,0,0,0,0,0,1,4,1,0,0],
      [0,0,0,1,2,1,1,1,1,1,1,2,1,0,0,0],
      [0,0,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
      [0,0,1,2,5,2,2,2,2,2,2,5,2,1,0,0],
      [0,0,1,2,7,2,2,6,6,2,2,7,2,1,0,0],
      [0,0,0,1,2,2,2,2,2,2,2,2,1,0,0,0],
      [0,0,0,1,2,7,7,2,2,7,7,2,1,0,0,0],
      [1,1,2,2,2,2,2,2,2,2,2,2,2,2,1,0],  // arm raised
      [1,2,1,2,2,2,2,2,2,2,2,2,2,1,0,0],
      [0,1,1,2,2,2,3,3,3,3,2,2,2,1,2,1],
      [0,0,1,1,1,3,3,3,3,3,3,1,1,2,2,1],
      [0,0,0,0,1,2,2,2,2,2,1,0,0,1,2,1],
      [0,0,0,0,0,1,1,1,1,1,0,0,0,0,1,0],
      [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
      [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    ],
  },
}

// Active character (updated from settings)
let activeChar = CHARACTERS.frog

const MSGS = [
  'Sip sip hooray! Drink water and thrive again!',
  'You are a plant. You need water. This is science!',
  'Hydration check! Drink your water!',
  'Hydrated you = glowing, thriving, unstoppable you.',
  "One sip at a time. It's time to hydrate!",
  'Did you know? Water is necessary for your brain! Drink that water!',
  'Your brain is basically 75% water. Keep the vibes flowing!',
  'Breaking news: A local frog wants you to drink your water again.',
  'Water break! Consider it a mini spa moment',
  'A sip at a time keeps the dry skin away. Keep glowing!',
  'Splash splash~ Drink some water!',
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
  const pal = activeChar.palette
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const id = sprite[r][c]
      if (id === 0) continue
      ctx.fillStyle = pal[id]
      ctx.fillRect(OX + c * PS, r * PS + bobY, PS, PS)
    }
  }
}

function applyCharacterTheme() {
  const t = activeChar.theme
  // Bubble border + tail colour
  document.getElementById('bubble-box').style.borderColor  = t.border
  document.getElementById('bubble-tail').style.borderTopColor = t.tailBorder
  // Bubble background (reset to char default unless overridden by custom remind)
  document.getElementById('bubble-box').style.background = t.bubbleBg
}

function animate() {
  frame++
  const bob = Math.round(2 * (0.5 - Math.abs((frame % BOB) / BOB - 0.5)) * 2)

  let sprite
  if (waving) {
    sprite = activeChar.wave; waveF--
    if (waveF <= 0) waving = false
  } else if (blinking) {
    sprite = activeChar.blink; blinkF--
    if (blinkF <= 0) { blinking = false; blinkCd = randInt(60, 120) }
  } else {
    sprite = activeChar.idle; blinkCd--
    if (blinkCd <= 0) { blinking = true; blinkF = 4 }
  }

  drawSprite(sprite, bob)
  setTimeout(animate, 1000 / FPS)
}
animate()

// ── Bubble ────────────────────────────────────────────────────────────────────
function showBubble(msg, bgColor) {
  bubbleText.textContent = msg
  if (bgColor) {
    document.getElementById('bubble-box').style.background = bgColor
    document.getElementById('bubble-tail').style.borderTopColor = bgColor
  } else {
    document.getElementById('bubble-box').style.background = ''
    document.getElementById('bubble-tail').style.borderTopColor = ''
  }
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

// ── Custom pixel context menu ─────────────────────────────────────────────────
const ctxMenu = document.getElementById('ctx-menu')

// Menu always anchors to the right side of the frog, never at cursor.
// FROG_X=72, FROG_W=96 → frog right edge inside window = 168
// Menu opens 8px into the right edge of the frog → x = 160
const MENU_ANCHOR_X = 160   // slightly inside frog right edge
const WIN_W_PX      = 240
const WIN_H_PX      = 456
const MENU_W_PX     = 208   // measured menu width
const MENU_H_PX     = 248   // measured menu height (all items + notes row)

function showCtxMenu() {
  // Measure actual rendered menu height (show hidden, measure, hide)
  ctxMenu.style.visibility = 'hidden'
  ctxMenu.style.display    = 'block'
  const mw = ctxMenu.offsetWidth  || MENU_W_PX
  const mh = ctxMenu.offsetHeight || MENU_H_PX
  ctxMenu.style.visibility = ''
  ctxMenu.style.display    = ''

  // Prefer right side of frog; flip left if it would overflow window width
  let mx = MENU_ANCHOR_X
  if (mx + mw > WIN_W_PX - 2) mx = WIN_W_PX - mw - 4

  // Prefer just below frog top (bubble area ends at y=100); clamp so bottom fits
  const frogTopInWindow = 100   // BUBBLE_AREA
  let   my = frogTopInWindow + 4
  if (my + mh > WIN_H_PX - 4) my = WIN_H_PX - mh - 4
  if (my < 0) my = 4

  ctxMenu.style.left = Math.max(2, mx) + 'px'
  ctxMenu.style.top  = my + 'px'
  ctxMenu.classList.add('open')
  ipcRenderer.send('mouse-enter-ui')
}

function hideCtxMenu() {
  ctxMenu.classList.remove('open')
}

document.addEventListener('contextmenu', e => {
  e.preventDefault()
  showCtxMenu()
})

// Close on any left-click outside the menu
document.addEventListener('click', e => {
  if (!ctxMenu.contains(e.target)) hideCtxMenu()
})

document.getElementById('ctx-wave').addEventListener('click', () => {
  hideCtxMenu()
  waving = true; waveF = FPS * 2
})

document.getElementById('ctx-remind').addEventListener('click', () => {
  hideCtxMenu()
  waving = true; waveF = FPS * 2
  if (soundEnabled) playRibbit()
  showBubble(MSGS[Math.floor(Math.random() * MSGS.length)])
})

document.getElementById('ctx-settings').addEventListener('click', () => {
  hideCtxMenu()
  ipcRenderer.send('open-settings')
})

document.getElementById('ctx-todo').addEventListener('click', () => {
  hideCtxMenu()
  ipcRenderer.send('open-todo')
})

const stickyBtn = document.getElementById('ctx-sticky')
stickyBtn.addEventListener('click', () => {
  if (stickyBtn.classList.contains('disabled')) return
  hideCtxMenu()
  const colors = ['pink', 'blue', 'yellow', 'green']
  ipcRenderer.send('open-sticky', colors[Math.floor(Math.random() * colors.length)])
})

document.getElementById('ctx-reminder-custom').addEventListener('click', () => {
  hideCtxMenu()
  ipcRenderer.send('open-reminder-dialog')
})

document.getElementById('ctx-quit').addEventListener('click', () => {
  hideCtxMenu()
  ipcRenderer.send('quit')
})

// ── Custom tooltip (renders above context menu z-index) ───────────────────────
const tooltip = document.getElementById('custom-tooltip')

function showTooltip(el, text) {
  el.removeAttribute('title')   // suppress native tooltip
  el._tooltipText = text
  el.addEventListener('mouseenter', _onEnter)
  el.addEventListener('mouseleave', _onLeave)
  el.addEventListener('mousemove',  _onMove)
}

function _onEnter(e) {
  tooltip.textContent = e.currentTarget._tooltipText
  tooltip.classList.add('show')
  _positionTooltip(e)
}
function _onLeave() { tooltip.classList.remove('show') }
function _onMove(e)  { _positionTooltip(e) }
function _positionTooltip(e) {
  const pad = 10
  let tx = e.clientX + pad
  let ty = e.clientY - 32
  // clamp inside window
  if (tx + 230 > window.innerWidth)  tx = e.clientX - 230 - pad
  if (ty < 0) ty = e.clientY + pad
  tooltip.style.left = tx + 'px'
  tooltip.style.top  = ty + 'px'
}

// Track sticky count to disable button at 10
ipcRenderer.on('sticky-count', (_, count) => {
  if (count >= 10) {
    stickyBtn.classList.add('disabled')
    showTooltip(stickyBtn, 'Close some of your stickies to add more')
  } else {
    stickyBtn.classList.remove('disabled')
    stickyBtn.removeEventListener('mouseenter', _onEnter)
    stickyBtn.removeEventListener('mouseleave', _onLeave)
    stickyBtn.removeEventListener('mousemove',  _onMove)
    tooltip.classList.remove('show')
  }
})

// ── Mouse hit-test → pass clicks through transparent areas ───────────────────
// The main process starts with setIgnoreMouseEvents(true, {forward:true}).
// We track mouse position here and tell it to stop ignoring when over visible UI.
document.addEventListener('mousemove', e => {
  const el = document.elementFromPoint(e.clientX, e.clientY)
  const overUI = el === canvas ||
    (bubbleWrap.classList.contains('visible') && bubbleWrap.contains(el)) ||
    ctxMenu.classList.contains('open') && ctxMenu.contains(el)
  if (overUI) ipcRenderer.send('mouse-enter-ui')
  else        ipcRenderer.send('mouse-leave-ui')
})

// ── Bell sound (for custom reminders) ────────────────────────────────────────
function playBell() {
  try {
    const ac = new AudioContext()
    ;[880, 660, 550].forEach((freq, i) => {
      const osc = ac.createOscillator(), gain = ac.createGain()
      osc.connect(gain); gain.connect(ac.destination)
      osc.type = 'sine'
      const t = ac.currentTime + i * 0.22
      osc.frequency.setValueAtTime(freq, t)
      gain.gain.setValueAtTime(0, t)
      gain.gain.linearRampToValueAtTime(0.22, t + 0.04)
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.9)
      osc.start(t); osc.stop(t + 0.9)
    })
  } catch (_) {}
}

// ── Settings state ────────────────────────────────────────────────────────────
let soundEnabled = true

ipcRenderer.on('settings-updated', (_, s) => {
  soundEnabled = s.soundEnabled
  const key = s.character || 'frog'
  activeChar = CHARACTERS[key] || CHARACTERS.frog
  applyCharacterTheme()
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

// Custom reminder — yellow bubble + bell sound
ipcRenderer.on('custom-remind', (_, text) => {
  waving = true; waveF = FPS * 2
  if (soundEnabled) playBell()
  showBubble(text, '#fff3b0')
})
