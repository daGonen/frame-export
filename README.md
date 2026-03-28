# Frame Export

**A lightweight Windows GUI for exporting video frames to image sequences.**  
No timeline scrubbing, no bloated software — just drop a video, pick your options, export.

![Python](https://img.shields.io/badge/python-3.8%2B-blue) ![Platform](https://img.shields.io/badge/platform-Windows-lightgrey) ![License](https://img.shields.io/badge/license-MIT-green) ![Version](https://img.shields.io/badge/version-1.0.0-purple)

---

## Features

- Export **all frames**, **first frame**, **last frame**, a **frame range**, or a **specific frame**
- Output formats: **PNG, JPG, TIF, BMP, WebP**
- Configurable filename **prefix**, **zero-padding**, and **JPEG quality**
- Auto-probes video for frame count, FPS, and duration
- Clean dark UI — no console window

---

## Requirements

- Python 3.8+
- [ffmpeg](https://www.gyan.dev/ffmpeg/builds/) (ffmpeg + ffprobe must be in your PATH)

### Installing ffmpeg (Windows)

1. Download **ffmpeg-release-essentials.zip** from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/)
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your system PATH
4. Verify: open a new cmd and run `where ffmpeg`

---

## Installation

```bash
git clone https://github.com/daGonen/frame-export.git
cd frame-export
```

No pip installs needed — uses Python standard library only.

---

## Usage

**Run directly:**
```bash
python video_exporter.py
```

**Or use the included launcher** (no cmd window):  
Double-click `video_exporter.bat`

---

## Launcher (video_exporter.bat)

Create a `video_exporter.bat` file next to the script:

```bat
@echo off
pythonw "%~dp0video_exporter.py"
```

Right-click → Create Shortcut → pin to taskbar or Desktop for quick access.

---

## Export Modes

| Mode | Description |
|------|-------------|
| All frames | Full image sequence, e.g. `frame_0001.png` |
| First frame | Single file: `frame_first.png` |
| Last frame | Single file: `frame_last.png` |
| Frame range | `10-50` for contiguous, or `10,20,30` for specific frames |
| Specific frame | Single frame by number |

---

## License

MIT — do whatever you want with it.

---

*Made by [daGonen](https://github.com/daGonen)*
