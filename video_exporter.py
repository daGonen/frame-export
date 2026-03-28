"""
Video -> Image Sequence Exporter
Version: 1.0.0
Author:  daGonen  (github.com/daGonen)
Requires: Python 3.8+, ffmpeg + ffprobe in PATH
Run: python video_exporter.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import os
import re
import shutil

# --- Locate ffmpeg / ffprobe --------------------------------------------------
def _find_exe(name):
    found = shutil.which(name)
    if found:
        return found
    # Common Windows locations
    search = [
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
        r"C:\tools\ffmpeg\bin",
        os.path.expandvars(r"%USERPROFILE%\scoop\shims"),
        os.path.dirname(os.path.abspath(__file__)),
    ]
    for folder in search:
        candidate = os.path.join(folder, name + ".exe")
        if os.path.isfile(candidate):
            return candidate
    return name

FFMPEG  = _find_exe("ffmpeg")
FFPROBE = _find_exe("ffprobe")

# --- Meta -------------------------------------------------------------------
VERSION = "1.0.0"
AUTHOR  = "daGonen"

# --- Theme --------------------------------------------------------------------
BG        = "#0f0f11"
PANEL     = "#17171c"
BORDER    = "#2a2a35"
ACCENT    = "#6c63ff"
ACCENT2   = "#a89cff"
TEXT      = "#e8e6f0"
MUTED     = "#6b6880"
SUCCESS   = "#4caf7d"
ERROR     = "#e05c5c"
FONT_MAIN = ("Segoe UI", 10)
FONT_MONO = ("Consolas", 9)


# --- FFprobe helper -----------------------------------------------------------
def ffprobe_info(path):
    """Return (duration_seconds, fps, total_frames) or raise."""
    cmd = [
        FFPROBE, "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate,nb_frames,duration",
        "-of", "default=noprint_wrappers=1", path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True,
                            creationflags=0x08000000)  # no console window
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffprobe returned non-zero")

    data = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()

    fps_raw = data.get("r_frame_rate", "25/1")
    if "/" in fps_raw:
        num, den = fps_raw.split("/")
        fps = float(num) / float(den) if float(den) else 25.0
    else:
        fps = float(fps_raw)

    duration = float(data.get("duration", 0) or 0)
    nb = data.get("nb_frames", "N/A")
    if nb in ("N/A", "0", ""):
        total_frames = int(duration * fps) if duration else 0
    else:
        total_frames = int(nb)

    return duration, fps, total_frames


# --- Main App -----------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Frame Export")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.geometry("560x650")

        self._video_path = tk.StringVar()
        self._dest_path  = tk.StringVar()
        self._mode       = tk.StringVar(value="all")
        self._frame_num  = tk.StringVar(value="1")
        self._fmt        = tk.StringVar(value="png")
        self._prefix     = tk.StringVar(value="frame")
        self._padding    = tk.IntVar(value=4)
        self._quality    = tk.IntVar(value=95)

        self._fps          = 0.0
        self._total_frames = 0
        self._duration     = 0.0
        self._running      = False

        self._build_ui()

        # Show resolved paths in title for debugging
        self.title(f"Frame Export  v{VERSION}  |  ffmpeg: {FFMPEG}")

    # ---------- UI build ------------------------------------------------------

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=20, pady=(22, 18))
        tk.Label(hdr, text="FRAME EXPORT", font=("Segoe UI Light", 18),
                 bg=BG, fg=TEXT).pack(side="left")
        tk.Label(hdr, text="via ffmpeg", font=FONT_MONO,
                 bg=BG, fg=MUTED).pack(side="left", padx=(10, 0), pady=(6, 0))

        # SOURCE
        self._divider("SOURCE")
        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=20, pady=(6, 0))
        self._make_entry(row, self._video_path, "Select video file...").pack(
            side="left", fill="x", expand=True, ipady=6)
        self._make_btn(row, "Browse", self._browse_video).pack(side="left", padx=(8, 0))

        self._info_lbl = tk.Label(self, text="", font=FONT_MONO, bg=BG, fg=MUTED, anchor="w")
        self._info_lbl.pack(fill="x", padx=20, pady=(4, 0))

        # DESTINATION
        self._divider("DESTINATION", top=14)
        row2 = tk.Frame(self, bg=BG)
        row2.pack(fill="x", padx=20, pady=(6, 0))
        self._make_entry(row2, self._dest_path, "Output folder...").pack(
            side="left", fill="x", expand=True, ipady=6)
        self._make_btn(row2, "Browse", self._browse_dest).pack(side="left", padx=(8, 0))

        # File options
        opt = tk.Frame(self, bg=BG)
        opt.pack(fill="x", padx=20, pady=(10, 0))
        for label, var, width in [("Prefix", self._prefix, 10), ("Padding", None, None)]:
            tk.Label(opt, text=label, font=FONT_MAIN, bg=BG, fg=MUTED).pack(side="left")
            if label == "Prefix":
                tk.Entry(opt, textvariable=var, width=width, font=FONT_MONO,
                         bg=PANEL, fg=TEXT, insertbackground=TEXT,
                         relief="flat", bd=0, highlightthickness=1,
                         highlightcolor=ACCENT, highlightbackground=BORDER
                         ).pack(side="left", padx=(6, 18), ipady=4)
            else:
                tk.Spinbox(opt, from_=1, to=8, textvariable=self._padding, width=3,
                           font=FONT_MONO, bg=PANEL, fg=TEXT, buttonbackground=PANEL,
                           relief="flat", bd=0, highlightthickness=1,
                           highlightcolor=ACCENT, highlightbackground=BORDER
                           ).pack(side="left", padx=(6, 18), ipady=4)

        tk.Label(opt, text="Format", font=FONT_MAIN, bg=BG, fg=MUTED).pack(side="left")
        fmt_cb = ttk.Combobox(opt, textvariable=self._fmt,
                              values=["png", "jpg", "tif", "bmp", "webp"],
                              width=6, font=FONT_MONO, state="readonly")
        fmt_cb.pack(side="left", padx=(6, 0))
        self._fmt.trace_add("write", lambda *_: self._toggle_quality())

        # JPEG quality
        self._q_frame = tk.Frame(self, bg=BG)
        tk.Label(self._q_frame, text="JPEG quality", font=FONT_MAIN,
                 bg=BG, fg=MUTED).pack(side="left")
        tk.Scale(self._q_frame, from_=1, to=100, orient="horizontal",
                 variable=self._quality, bg=BG, fg=TEXT, troughcolor=PANEL,
                 activebackground=ACCENT, highlightthickness=0,
                 length=180, sliderlength=14, bd=0).pack(side="left", padx=(10, 0))
        tk.Label(self._q_frame, textvariable=self._quality,
                 font=FONT_MONO, bg=BG, fg=ACCENT2, width=3).pack(side="left")
        # hidden by default

        # EXPORT MODE
        self._divider("EXPORT MODE", top=14)
        modes_frame = tk.Frame(self, bg=BG)
        modes_frame.pack(fill="x", padx=20, pady=(8, 0))
        self._mode_btns = []
        for val, label in [("all","All frames"),("first","First frame"),
                            ("last","Last frame"),("range","Frame range"),
                            ("single","Specific frame")]:
            rb = tk.Radiobutton(
                modes_frame, text=label, variable=self._mode, value=val,
                command=self._on_mode_change,
                bg=BG, fg=TEXT, selectcolor=BG, activebackground=BG,
                activeforeground=ACCENT2, font=FONT_MAIN,
                indicatoron=False, relief="flat", bd=0, padx=12, pady=6)
            rb.pack(side="left", padx=(0, 6))
            self._mode_btns.append((rb, val))

        self._mode.trace_add("write", lambda *_: self._refresh_radio_colors())

        # Frame input
        self._frame_area = tk.Frame(self, bg=BG)
        self._frame_label = tk.Label(self._frame_area, text="Frame #",
                                     font=FONT_MAIN, bg=BG, fg=MUTED)
        self._frame_label.pack(side="left")
        tk.Entry(self._frame_area, textvariable=self._frame_num, width=12,
                 font=FONT_MONO, bg=PANEL, fg=TEXT, insertbackground=TEXT,
                 relief="flat", bd=0, highlightthickness=1,
                 highlightcolor=ACCENT, highlightbackground=BORDER
                 ).pack(side="left", padx=(8, 0), ipady=4)
        self._frame_hint = tk.Label(self._frame_area, text="",
                                    font=FONT_MONO, bg=BG, fg=MUTED)
        self._frame_hint.pack(side="left", padx=(8, 0))

        # Progress
        self._divider("", top=14)
        self._prog_var = tk.DoubleVar()
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("X.Horizontal.TProgressbar",
                        troughcolor=PANEL, background=ACCENT,
                        bordercolor=BG, lightcolor=ACCENT, darkcolor=ACCENT)
        ttk.Progressbar(self, variable=self._prog_var, maximum=100,
                        length=520, style="X.Horizontal.TProgressbar"
                        ).pack(padx=20)

        self._status = tk.Label(self, text="Ready", font=FONT_MONO,
                                bg=BG, fg=MUTED, anchor="w")
        self._status.pack(fill="x", padx=20, pady=(6, 0))

        # Export button
        self._export_btn = tk.Button(
            self, text="EXPORT", command=self._start_export,
            font=("Segoe UI Semibold", 11), bg=ACCENT, fg="#ffffff",
            activebackground=ACCENT2, activeforeground="#ffffff",
            relief="flat", bd=0, pady=12, cursor="hand2")
        # Footer
        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=20, pady=(0, 4))
        tk.Label(footer, text=f"v{VERSION}", font=("Consolas", 8),
                 bg=BG, fg=BORDER).pack(side="left")
        tk.Label(footer, text=f"daGonen", font=("Consolas", 8),
                 bg=BG, fg=BORDER).pack(side="right")

        self._export_btn.pack(fill="x", padx=20, pady=(18, 20))

        self._on_mode_change()

    # ---------- Helpers -------------------------------------------------------

    def _divider(self, title, top=0):
        f = tk.Frame(self, bg=BG)
        f.pack(fill="x", padx=20, pady=(top, 0))
        if title:
            tk.Label(f, text=title, font=("Segoe UI Semibold", 8),
                     bg=BG, fg=MUTED).pack(side="left")
        tk.Frame(f, bg=BORDER, height=1).pack(
            side="left", fill="x", expand=True, padx=(8 if title else 0, 0))

    def _make_entry(self, parent, var, placeholder=""):
        e = tk.Entry(parent, textvariable=var, font=FONT_MONO,
                     bg=PANEL, fg=MUTED, insertbackground=TEXT,
                     relief="flat", bd=0, highlightthickness=1,
                     highlightcolor=ACCENT, highlightbackground=BORDER)
        if not var.get():
            e.insert(0, placeholder)

        def on_in(ev):
            if e.get() == placeholder:
                e.delete(0, "end")
                e.configure(fg=TEXT)

        def on_out(ev):
            if not e.get():
                e.insert(0, placeholder)
                e.configure(fg=MUTED)

        e.bind("<FocusIn>", on_in)
        e.bind("<FocusOut>", on_out)
        return e

    def _make_btn(self, parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd,
                         font=FONT_MAIN, bg=PANEL, fg=TEXT,
                         activebackground=BORDER, activeforeground=TEXT,
                         relief="flat", bd=0, padx=12, pady=6, cursor="hand2",
                         highlightthickness=1, highlightbackground=BORDER)

    def _refresh_radio_colors(self):
        active = self._mode.get()
        for btn, val in self._mode_btns:
            btn.configure(fg=ACCENT if val == active else TEXT)

    def _on_mode_change(self):
        mode = self._mode.get()
        if mode in ("single", "range"):
            self._frame_area.pack(fill="x", padx=20, pady=(10, 0))
            if mode == "single":
                self._frame_label.config(text="Frame #")
                self._frame_hint.config(
                    text=f"(1 - {self._total_frames or '?'})")
            else:
                self._frame_label.config(text="Range")
                self._frame_hint.config(text='e.g. 10-50 or 10,20,30')
        else:
            self._frame_area.pack_forget()
        self._refresh_radio_colors()

    def _toggle_quality(self):
        if self._fmt.get() == "jpg":
            self._q_frame.pack(fill="x", padx=20, pady=(8, 0))
        else:
            self._q_frame.pack_forget()

    def _set_status(self, msg, color=MUTED):
        self._status.configure(text=msg, fg=color)
        self.update_idletasks()

    # ---------- Browse --------------------------------------------------------

    def _browse_video(self):
        path = filedialog.askopenfilename(
            title="Select video",
            filetypes=[("Video files",
                        "*.mp4 *.mov *.avi *.mkv *.mxf *.webm *.flv *.wmv"),
                       ("All files", "*.*")])
        if not path:
            return
        self._video_path.set(path)
        self._probe_video(path)

    def _browse_dest(self):
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self._dest_path.set(path)

    def _probe_video(self, path):
        self._set_status("Probing video...")
        try:
            dur, fps, frames = ffprobe_info(path)
            self._fps = fps
            self._total_frames = frames
            self._duration = dur
            mins = int(dur // 60)
            secs = dur % 60
            self._info_lbl.config(
                text=f"  {frames} frames  .  {fps:.3f} fps  .  "
                     f"{mins}m {secs:.2f}s",
                fg=ACCENT2)
            self._frame_hint.config(text=f"(1 - {frames})")
            self._set_status("Ready")
        except Exception as ex:
            self._info_lbl.config(text=f"  Probe error: {ex}", fg=ERROR)
            self._set_status("ffprobe error", ERROR)

    # ---------- Export --------------------------------------------------------

    def _start_export(self):
        if self._running:
            return

        video = self._video_path.get().strip()
        dest  = self._dest_path.get().strip()

        if not video or video == "Select video file...":
            messagebox.showerror("Missing input", "Please select a video file.")
            return
        if not os.path.isfile(video):
            messagebox.showerror("Not found", f"File not found:\n{video}")
            return
        if not dest or dest == "Output folder...":
            messagebox.showerror("Missing destination",
                                 "Please select an output folder.")
            return
        os.makedirs(dest, exist_ok=True)

        try:
            cmds = self._build_commands(
                video, dest,
                self._mode.get(), self._fmt.get(),
                self._prefix.get() or "frame",
                self._padding.get(), self._quality.get(),
                self._frame_num.get().strip())
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
            return

        self._running = True
        self._export_btn.config(state="disabled", bg=MUTED)
        self._prog_var.set(0)
        threading.Thread(target=self._run_export, args=(cmds,),
                         daemon=True).start()

    def _build_commands(self, video, dest, mode, fmt, prefix,
                        padding, quality, frame_input):
        pad_str = f"%0{padding}d"
        q_args = ["-q:v", "2"] if fmt == "jpg" and quality >= 90 else \
                 ["-q:v", str(max(2, int(31 - quality * 0.29)))] if fmt == "jpg" else []

        def seq_out():
            return os.path.join(dest, f"{prefix}_{pad_str}.{fmt}")

        def single_out(tag):
            return os.path.join(dest, f"{prefix}_{tag}.{fmt}")

        if mode == "all":
            return [[FFMPEG, "-y", "-i", video] + q_args + [seq_out()]]

        if mode == "first":
            return [[FFMPEG, "-y", "-i", video, "-vframes", "1"]
                    + q_args + [single_out("first")]]

        if mode == "last":
            if not self._total_frames:
                raise ValueError("Could not determine frame count. "
                                 "Try selecting the video again.")
            n = self._total_frames
            return [[FFMPEG, "-y", "-i", video,
                     "-vf", f"select='eq(n\\,{n-1})'",
                     "-vframes", "1", "-vsync", "0"]
                    + q_args + [single_out("last")]]

        if mode == "single":
            if not frame_input.isdigit():
                raise ValueError("Enter a single integer frame number.")
            n = int(frame_input)
            if self._total_frames and not (1 <= n <= self._total_frames):
                raise ValueError(
                    f"Frame {n} out of range (1-{self._total_frames}).")
            return [[FFMPEG, "-y", "-i", video,
                     "-vf", f"select='eq(n\\,{n-1})'",
                     "-vframes", "1", "-vsync", "0"]
                    + q_args + [single_out(f"{n:0{padding}d}")]]

        if mode == "range":
            if re.match(r"^\d+[-]\d+$", frame_input):
                a, b = frame_input.split("-")
                start, end = int(a), int(b)
                if start >= end:
                    raise ValueError("Start must be less than end.")
                frames = list(range(start, end + 1))
            elif re.match(r"^[\d,\s]+$", frame_input):
                frames = [int(x) for x in re.split(r"[,\s]+", frame_input) if x]
            else:
                raise ValueError('Use "10-50" for a range or "10,20,30" for specific frames.')
            if not frames:
                raise ValueError("No frames specified.")
            sel = "+".join(f"eq(n\\,{f-1})" for f in frames)
            return [[FFMPEG, "-y", "-i", video,
                     "-vf", f"select='{sel}'",
                     "-vframes", str(len(frames)), "-vsync", "0"]
                    + q_args + [seq_out()]]

        raise ValueError(f"Unknown mode: {mode}")

    def _run_export(self, cmds):
        try:
            for i, cmd in enumerate(cmds):
                self.after(0, self._set_status,
                           f"Running... ({i+1}/{len(cmds)})")
                self.after(0, self._prog_var.set, (i / len(cmds)) * 100)

                result = subprocess.run(
                    cmd, capture_output=True, text=True,
                    creationflags=0x08000000)  # no console popup

                if result.returncode != 0:
                    err = result.stderr[-800:].strip()
                    self.after(0, messagebox.showerror,
                               "FFmpeg error", f"Export failed:\n\n{err}")
                    self.after(0, self._set_status, "Export failed.", ERROR)
                    return

            self.after(0, self._prog_var.set, 100)
            out_dir = os.path.dirname(cmds[-1][-1])
            self.after(0, self._set_status,
                       f"Done  ->  {out_dir}", SUCCESS)
            self.after(0, messagebox.showinfo, "Done",
                       f"Frames saved to:\n{out_dir}")
        finally:
            self._running = False
            self.after(0, self._export_btn.config,
                       {"state": "normal", "bg": ACCENT})


if __name__ == "__main__":
    app = App()
    app.mainloop()