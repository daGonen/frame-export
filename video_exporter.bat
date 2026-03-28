@echo off
pythonw "%~dp0video_exporter.py"
```

`pythonw` instead of `python` is the key — it's the windowless Python launcher, so no cmd window appears at all, just the UI. `%~dp0` means "same folder as this bat file" so it works regardless of where you put it.

If you want to go one step further, right-click the `.bat` → **Create shortcut** → move the shortcut to your Desktop, then right-click the shortcut → **Properties** → **Change Icon** and point it at a `.ico` file if you want it to look like a real app in your taskbar.

For the tools folder structure I'd suggest something like:
```
C:\Users\13god\Tools\
    video_exporter\
        video_exporter.py
        video_exporter.bat
    other_tool\
        ...