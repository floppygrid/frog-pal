# 🐸 FrogPal — Your Desktop Hydration Buddy

A tiny pixel-art frog that lives on your desktop, always on top of every window, and reminds you to drink water.

![FrogPal preview](assets/preview.png)

## Features

- 🐸 Pixel-art frog with idle bob & blink animations
- 💧 Water reminder notification every 30 minutes
- 🖱️ Drag anywhere on screen
- 🖱️ Click the frog to make it wave
- Right-click menu: wave, remind now, quit
- Transparent background (no ugly window frame)
- Cross-platform: macOS, Windows, Linux

## Requirements

- Python 3.8+
- tkinter (bundled with most Python installs)
- `plyer` for native OS notifications (optional but recommended)

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/frog-pal.git
cd frog-pal

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run!
python frog_pal.py
```

## Configuration

Edit the constants at the top of `frog_pal.py`:

| Constant | Default | Description |
|---|---|---|
| `REMINDER_INTERVAL_MINUTES` | `30` | Minutes between water reminders |
| `PIXEL_SIZE` | `4` | Size of each pixel (bigger = larger frog) |
| `IDLE_ANIM_FPS` | `8` | Animation speed |

## Auto-start on Login

### macOS
```bash
# Create a launch agent plist
cat > ~/Library/LaunchAgents/com.frogpal.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.frogpal</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/FULL/PATH/TO/frog_pal.py</string>
  </array>
  <key>RunAtLoad</key><true/>
</dict>
</plist>
EOF
launchctl load ~/Library/LaunchAgents/com.frogpal.plist
```

### Windows
Add a shortcut to `frog_pal.py` (or a `.bat` file that runs it) to:
`C:\Users\YOUR_NAME\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`

### Linux (systemd user service)
```ini
# ~/.config/systemd/user/frogpal.service
[Unit]
Description=FrogPal desktop pet

[Service]
ExecStart=/usr/bin/python3 /FULL/PATH/TO/frog_pal.py
Restart=on-failure

[Install]
WantedBy=default.target
```
```bash
systemctl --user enable --now frogpal
```

## Linux Transparency Note

True window transparency on Linux requires a compositor (e.g. picom, compton, or a DE with compositing enabled). Without one, the background will use 95% opacity as a fallback.

## Contributing

PRs welcome! Ideas:
- More animations (jumping, sleeping)
- Custom reminder messages
- Settings GUI
- Packaged `.app` / `.exe` builds

## License

MIT
