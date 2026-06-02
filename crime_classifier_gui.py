import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"
from keras.layers import DepthwiseConv2D

# Fix for compatibility with newer TensorFlow
original_init = DepthwiseConv2D.__init__

def patched_init(self, *args, **kwargs):
    kwargs.pop("groups", None)
    original_init(self, *args, **kwargs)

DepthwiseConv2D.__init__ = patched_init




#HOW TO USE:
#   1. Export your Teachable Machine model as "Keras" format
#    2. Place keras_model.h5 and labels.txt in the same folder as this script
#       (or browse to their location in the app)
#    3. Run: python crime_classifier_gui.py


import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import numpy as np
from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageOps
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ──────────────────────────────────────────────────────────────────────────────
# CRIME DATA — descriptions, affected states, suggestions
# ──────────────────────────────────────────────────────────────────────────────

CRIME_DATA = {
    "Assault": {
        "emoji": "⚠️",
        "color": "#FF6B35",
        "description": (
            "Assault refers to the intentional act of threatening or physically attacking "
            "another person, causing bodily harm or fear of harm. It encompasses both physical "
            "battery and verbal/behavioral threats. Assault cases range from simple altercations "
            "to aggravated assault involving weapons. It is one of the most commonly reported "
            "violent crimes globally and can lead to serious psychological trauma for victims."
        ),
        "states": {
            "New Mexico": 82,
            "Alaska": 79,
            "Tennessee": 75,
            "Arkansas": 71,
            "South Carolina": 68,
            "Colorado": 63,
            "Nevada": 60,
            "Missouri": 58,
        },
        "suggestions": [
            "🚨  Call emergency services (100/112) immediately if in danger.",
            "📹  Preserve CCTV footage and eyewitness contact details.",
            "🏥  Seek immediate medical attention and document all injuries.",
            "📝  File an FIR at the nearest police station within 24 hours.",
            "⚖️   Contact a legal-aid organization for guidance on pressing charges.",
            "🔒  Install security cameras in high-risk zones.",
            "🤝  Community policing programs can significantly deter assault rates.",
        ],
        "ipc": "IPC Sections 351–358 / BNS Sections 130–137",
    },
    "Hit and Run": {
        "emoji": "🚗",
        "color": "#FFD700",
        "description": (
            "Hit and Run is a traffic crime where a driver involved in an accident deliberately "
            "flees the scene without providing identification, insurance details, or aid to "
            "injured parties. This is both a criminal and civil offence. Victims are often left "
            "critically injured with no immediate help. The offence is worsened when the driver "
            "was under the influence of alcohol or drugs, or operating an unregistered vehicle."
        ),
        "states": {
            "Uttar Pradesh": 89,
            "Maharashtra": 84,
            "Tamil Nadu": 77,
            "Rajasthan": 73,
            "Gujarat": 69,
            "Madhya Pradesh": 65,
            "Karnataka": 61,
            "Delhi": 58,
        },
        "suggestions": [
            "📸  Photograph the vehicle number plate, make, model, and direction of escape.",
            "🆘  Call traffic police (103) and ambulance (108) without delay.",
            "👁️   Collect witness statements and dashcam footage from nearby vehicles.",
            "🏦  Apply for victim compensation via Motor Accident Claims Tribunal (MACT).",
            "📋  Report to RTO for tracing vehicle ownership records.",
            "🚦  Advocate for better road lighting and speed-monitoring cameras.",
            "🧪  Push for mandatory breathalyzer checks at accident-prone zones.",
        ],
        "ipc": "Motor Vehicles Act §161 / IPC 304A / BNS Section 106",
    },
    "Murder": {
        "emoji": "💀",
        "color": "#FF2D55",
        "description": (
            "Murder is the unlawful premeditated killing of one human being by another. "
            "It is classified as the most serious violent crime in all legal systems. Murder "
            "cases are categorized by degree based on intent, premeditation, and circumstances. "
            "First-degree murder involves deliberate planning, while second-degree may result "
            "from a heat-of-passion act. The psychological impact on families and communities "
            "is profound and long-lasting."
        ),
        "states": {
            "Uttar Pradesh": 91,
            "Bihar": 86,
            "Maharashtra": 78,
            "Madhya Pradesh": 74,
            "West Bengal": 70,
            "Jharkhand": 66,
            "Rajasthan": 62,
            "Odisha": 55,
        },
        "suggestions": [
            "🔴  Do NOT disturb the crime scene — preserve all physical evidence.",
            "📞  Contact police homicide unit immediately (dial 100).",
            "🧬  Request forensic investigation including DNA and ballistics analysis.",
            "👨‍⚖️  Ensure victim's family receives legal representation.",
            "🏛️   Track case progress through the National Crime Records Bureau (NCRB).",
            "💬  Provide psychological counseling for bereaved family members.",
            "🔦  Strengthen witness-protection programs to ensure safe testimony.",
        ],
        "ipc": "IPC Sections 299–304 / BNS Sections 100–106",
    },
    "Robbery": {
        "emoji": "💰",
        "color": "#9B59B6",
        "description": (
            "Robbery is the act of taking property from a person using force, intimidation, "
            "or the threat of violence. Unlike theft, robbery involves a direct confrontation "
            "with the victim. Armed robbery (dacoity when committed by five or more persons) "
            "carries severe penalties. Robbery hotspots include urban markets, ATM locations, "
            "late-night streets, and public transport corridors. It leaves victims with both "
            "financial loss and lasting psychological trauma."
        ),
        "states": {
            "Delhi": 88,
            "Maharashtra": 83,
            "Karnataka": 76,
            "Telangana": 72,
            "Uttar Pradesh": 67,
            "Tamil Nadu": 63,
            "Gujarat": 59,
            "Haryana": 54,
        },
        "suggestions": [
            "🤲  Do NOT resist — cooperate with the robber to avoid physical harm.",
            "📲  Alert police immediately after reaching safety (dial 100).",
            "🏧  Report to your bank immediately to block cards and freeze accounts.",
            "🎥  Request CCTV footage from nearby establishments.",
            "📄  File insurance claims with a copy of the police FIR.",
            "💡  Avoid displaying valuables in public or isolated areas.",
            "🏙️   Push local authorities for increased police patrolling in hotspots.",
        ],
        "ipc": "IPC Sections 390–402 / BNS Sections 309–318",
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# COLOUR / STYLE TOKENS
# ──────────────────────────────────────────────────────────────────────────────

BG_DARK      = "#0D1117"
BG_PANEL     = "#161B22"
BG_CARD      = "#1C2431"
BG_HOVER     = "#21262D"
ACCENT_BLUE  = "#58A6FF"
ACCENT_GREEN = "#3FB950"
BORDER       = "#30363D"
TEXT_PRIMARY = "#E6EDF3"
TEXT_MUTED   = "#8B949E"
TEXT_LABEL   = "#C9D1D9"
FONT_TITLE   = ("Segoe UI", 22, "bold")
FONT_H2      = ("Segoe UI", 14, "bold")
FONT_H3      = ("Segoe UI", 11, "bold")
FONT_BODY    = ("Segoe UI", 10)
FONT_MONO    = ("Consolas", 9)
FONT_SMALL   = ("Segoe UI", 9)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN APPLICATION CLASS
# ──────────────────────────────────────────────────────────────────────────────

class CrimeClassifierApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🔍 Crime Scene Image Classifier — AI Analysis System")
        self.geometry("1400x860")
        self.minsize(1100, 700)
        self.configure(bg=BG_DARK)

        # State variables
        self.model        = None
        self.model_path   = tk.StringVar(value="keras_model.h5")
        self.labels_path  = tk.StringVar(value="labels.txt")
        self.image_path   = None
        self.pil_image    = None
        self.class_names  = []
        self.is_model_loaded = False

        self._build_ui()
        self._try_auto_load_model()

    # ── AUTO-LOAD ──────────────────────────────────────────────────────────────
    def _try_auto_load_model(self):
        if os.path.exists("keras_model.h5") and os.path.exists("labels.txt"):
            self._load_model_thread()

    # ══════════════════════════════════════════════════════════════════════════
    # UI CONSTRUCTION
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        # ── HEADER ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg="#0A0F14", height=64)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        tk.Label(
            hdr,
            text="⚖  CRIME SCENE CLASSIFICATION SYSTEM",
            font=FONT_TITLE, bg="#0A0F14", fg=ACCENT_BLUE
        ).pack(side="left", padx=24, pady=14)

        tk.Label(
            hdr,
            text=" ",
            font=FONT_SMALL, bg="#0A0F14", fg=TEXT_MUTED
        ).pack(side="right", padx=24, pady=20)

        # ── STATUS BAR ────────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="⚪  System initialising…")
        status_bar = tk.Frame(self, bg="#0A0F14", height=26)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        tk.Label(
            status_bar, textvariable=self.status_var,
            font=FONT_MONO, bg="#0A0F14", fg=TEXT_MUTED, anchor="w"
        ).pack(side="left", padx=12)

        # ── THREE-COLUMN LAYOUT ───────────────────────────────────────────────
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=10, pady=(6, 4))

        # Left panel
        left = tk.Frame(body, bg=BG_PANEL, width=300)
        left.pack(side="left", fill="y", padx=(0, 5))
        left.pack_propagate(False)
        self._build_left_panel(left)

        # Centre panel
        centre = tk.Frame(body, bg=BG_PANEL)
        centre.pack(side="left", fill="both", expand=True, padx=5)
        self._build_centre_panel(centre)

        # Right panel
        right = tk.Frame(body, bg=BG_PANEL, width=370)
        right.pack(side="left", fill="y", padx=(5, 0))
        right.pack_propagate(False)
        self._build_right_panel(right)

    # ── LEFT PANEL : MODEL LOADER + IMAGE UPLOAD ──────────────────────────────
    def _build_left_panel(self, parent):
        self._section_label(parent, "⚙  MODEL CONFIGURATION")

        # Model file
        self._file_row(parent, "Model (.h5)", self.model_path, self._browse_model)
        # Labels file
        self._file_row(parent, "Labels (.txt)", self.labels_path, self._browse_labels)

        # Load button
        self.btn_load = self._btn(parent, "⬆  LOAD MODEL", self._load_model_thread,
                                  color=ACCENT_BLUE)
        self.btn_load.pack(padx=14, pady=(4, 10), fill="x")

        # Model status badge
        self.model_badge = tk.Label(parent, text="● Model not loaded",
                                    font=FONT_SMALL, bg=BG_PANEL, fg="#FF453A")
        self.model_badge.pack(padx=14, anchor="w")

        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=10, pady=12)

        # ── IMAGE UPLOAD ──────────────────────────────────────────────────────
        self._section_label(parent, "🖼  IMAGE INPUT")

        # Drop zone
        self.drop_zone = tk.Label(
            parent,
            text="Click to Upload\nImage File",
            font=("Segoe UI", 11, "bold"), bg=BG_CARD, fg=TEXT_MUTED,
            relief="flat", cursor="hand2", height=7,
            bd=0, highlightthickness=2,
            highlightbackground=BORDER, highlightcolor=ACCENT_BLUE
        )
        self.drop_zone.pack(padx=14, pady=6, fill="x")
        self.drop_zone.bind("<Button-1>", lambda e: self._browse_image())
        self.drop_zone.bind("<Enter>",
            lambda e: self.drop_zone.config(fg=ACCENT_BLUE, highlightbackground=ACCENT_BLUE))
        self.drop_zone.bind("<Leave>",
            lambda e: self.drop_zone.config(fg=TEXT_MUTED, highlightbackground=BORDER))

        self.btn_predict = self._btn(
            parent, "🔍  ANALYSE IMAGE", self._predict,
            color=ACCENT_GREEN, state="disabled"
        )
        self.btn_predict.pack(padx=14, pady=(4, 6), fill="x")

        self.btn_clear = self._btn(
            parent, "✕  CLEAR", self._clear_all,
            color="#FF453A", state="disabled"
        )
        self.btn_clear.pack(padx=14, pady=(0, 10), fill="x")

        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=10, pady=8)
        self._section_label(parent, "📊  QUICK STATS")

        self.stats_frame = tk.Frame(parent, bg=BG_PANEL)
        self.stats_frame.pack(fill="x", padx=14)
        self._stat_row(self.stats_frame, "Images Analysed:", "0", "lbl_count")
        self._stat_row(self.stats_frame, "Last Confidence:", "—", "lbl_conf")
        self._stat_row(self.stats_frame, "Predicted Class:", "—", "lbl_class")

    # ── CENTRE PANEL : IMAGE PREVIEW + PREPROCESSING AXES ────────────────────
    def _build_centre_panel(self, parent):
        self._section_label(parent, "🔬  IMAGE ANALYSIS & PREPROCESSING")

        # Original image preview
        preview_row = tk.Frame(parent, bg=BG_PANEL)
        preview_row.pack(fill="x", padx=10, pady=(0, 6))

        orig_card = tk.Frame(preview_row, bg=BG_CARD,
                             highlightthickness=1, highlightbackground=BORDER)
        orig_card.pack(side="left", padx=(0, 6))

        tk.Label(orig_card, text="ORIGINAL IMAGE",
                 font=FONT_MONO, bg=BG_CARD, fg=TEXT_MUTED).pack(pady=(6, 2))
        self.lbl_preview = tk.Label(orig_card, bg=BG_CARD, text="No image loaded",
                                    fg=TEXT_MUTED, font=FONT_SMALL, width=26, height=14)
        self.lbl_preview.pack(padx=8, pady=(0, 8))

        # Prediction result card
        res_card = tk.Frame(preview_row, bg=BG_CARD,
                            highlightthickness=1, highlightbackground=BORDER)
        res_card.pack(side="left", fill="both", expand=True, padx=(6, 0))

        tk.Label(res_card, text="PREDICTION RESULT",
                 font=FONT_MONO, bg=BG_CARD, fg=TEXT_MUTED).pack(pady=(6, 4))

        self.lbl_crime_emoji = tk.Label(res_card, text="🔍",
                                        font=("Segoe UI", 36), bg=BG_CARD, fg=TEXT_PRIMARY)
        self.lbl_crime_emoji.pack()

        self.lbl_crime_name = tk.Label(res_card, text="Awaiting Input",
                                       font=("Segoe UI", 16, "bold"), bg=BG_CARD, fg=TEXT_PRIMARY)
        self.lbl_crime_name.pack(pady=(2, 0))

        self.lbl_crime_ipc = tk.Label(res_card, text="",
                                      font=FONT_MONO, bg=BG_CARD, fg=TEXT_MUTED)
        self.lbl_crime_ipc.pack()

        # Confidence bars
        self.conf_frame = tk.Frame(res_card, bg=BG_CARD)
        self.conf_frame.pack(fill="x", padx=14, pady=(8, 4))
        self._build_confidence_bars()

        # ── MATPLOTLIB PREPROCESSING PANEL ───────────────────────────────────
        self._section_label(parent, "🧪  PREPROCESSING VISUALISATION  (6 Views)")
        fig_frame = tk.Frame(parent, bg=BG_DARK,
                             highlightthickness=1, highlightbackground=BORDER)
        fig_frame.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        self.fig = Figure(figsize=(9, 3.2), dpi=88, facecolor=BG_DARK)
        self.fig.subplots_adjust(left=0.03, right=0.97, top=0.88, bottom=0.05, wspace=0.25)
        self.axes = self.fig.subplots(1, 6)
        self._blank_axes()

        self.canvas = FigureCanvasTkAgg(self.fig, master=fig_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ── RIGHT PANEL : CRIME INFO + STATE CHART + SUGGESTIONS ─────────────────
    def _build_right_panel(self, parent):
        self._section_label(parent, "📋  CRIME INTELLIGENCE")

        # Scrollable content
        scroll_canvas = tk.Canvas(parent, bg=BG_PANEL, bd=0,
                                  highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical",
                                  command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.info_container = tk.Frame(scroll_canvas, bg=BG_PANEL)
        self.info_window = scroll_canvas.create_window(
            (0, 0), window=self.info_container, anchor="nw")

        def on_configure(e):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
            scroll_canvas.itemconfig(self.info_window,
                                     width=scroll_canvas.winfo_width())

        self.info_container.bind("<Configure>", on_configure)
        scroll_canvas.bind("<Configure>",
            lambda e: scroll_canvas.itemconfig(self.info_window,
                                               width=scroll_canvas.winfo_width()))
        scroll_canvas.bind_all("<MouseWheel>",
            lambda e: scroll_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._show_placeholder_info()

    # ══════════════════════════════════════════════════════════════════════════
    # HELPER WIDGET BUILDERS
    # ══════════════════════════════════════════════════════════════════════════

    def _section_label(self, parent, text):
        f = tk.Frame(parent, bg=BG_PANEL)
        f.pack(fill="x", padx=10, pady=(10, 4))
        tk.Label(f, text=text, font=("Segoe UI", 9, "bold"),
                 bg=BG_PANEL, fg=ACCENT_BLUE).pack(side="left")
        tk.Frame(f, bg=BORDER, height=1).pack(side="left", fill="x",
                                               expand=True, padx=8, pady=6)

    def _file_row(self, parent, label, var, cmd):
        f = tk.Frame(parent, bg=BG_PANEL)
        f.pack(fill="x", padx=14, pady=3)
        tk.Label(f, text=label, font=FONT_SMALL, bg=BG_PANEL,
                 fg=TEXT_MUTED, width=11, anchor="w").pack(side="left")
        entry = tk.Entry(f, textvariable=var, font=FONT_MONO, bg=BG_CARD,
                         fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
                         relief="flat", bd=4)
        entry.pack(side="left", fill="x", expand=True)
        tk.Button(f, text="…", command=cmd, font=FONT_SMALL,
                  bg=BG_HOVER, fg=TEXT_PRIMARY, relief="flat",
                  bd=0, padx=6, cursor="hand2").pack(side="left", padx=(4, 0))

    def _btn(self, parent, text, cmd, color=ACCENT_BLUE, state="normal"):
        b = tk.Button(
            parent, text=text, command=cmd,
            font=("Segoe UI", 10, "bold"),
            bg=color, fg="#0D1117",
            activebackground=color, activeforeground="#0D1117",
            relief="flat", bd=0, pady=8, cursor="hand2", state=state
        )
        return b

    def _stat_row(self, parent, label, value, attr):
        f = tk.Frame(parent, bg=BG_PANEL)
        f.pack(fill="x", pady=2)
        tk.Label(f, text=label, font=FONT_SMALL, bg=BG_PANEL,
                 fg=TEXT_MUTED).pack(side="left")
        lbl = tk.Label(f, text=value, font=("Segoe UI", 9, "bold"),
                       bg=BG_PANEL, fg=ACCENT_BLUE)
        lbl.pack(side="right")
        setattr(self, attr, lbl)

    def _build_confidence_bars(self):
        """Create 4 confidence bar rows (one per class)."""
        classes = ["Assault", "Hit and Run", "Murder", "Robbery"]
        colors = [CRIME_DATA[c]["color"] for c in classes]
        self.conf_bars = {}
        self.conf_pcts = {}

        for cls, col in zip(classes, colors):
            row = tk.Frame(self.conf_frame, bg=BG_CARD)
            row.pack(fill="x", pady=2)

            tk.Label(row, text=cls, font=FONT_SMALL, bg=BG_CARD,
                     fg=TEXT_LABEL, width=11, anchor="w").pack(side="left")

            bar_bg = tk.Frame(row, bg=BORDER, height=10)
            bar_bg.pack(side="left", fill="x", expand=True, padx=4)
            bar_fg = tk.Frame(bar_bg, bg=col, height=10, width=0)
            bar_fg.place(x=0, y=0, relheight=1)
            self.conf_bars[cls] = (bar_bg, bar_fg)

            pct_lbl = tk.Label(row, text="0%", font=FONT_MONO, bg=BG_CARD,
                               fg=col, width=5)
            pct_lbl.pack(side="left")
            self.conf_pcts[cls] = pct_lbl

    def _blank_axes(self):
        titles = ["Original", "Grayscale", "Normalised",
                  "Edge Detect", "Sharpened", "Histogram"]
        for ax, t in zip(self.axes, titles):
            ax.set_facecolor(BG_CARD)
            ax.set_title(t, color=TEXT_MUTED, fontsize=7, pad=3)
            ax.set_xticks([]); ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_color(BORDER)

    def _show_placeholder_info(self):
        for w in self.info_container.winfo_children():
            w.destroy()
        tk.Label(
            self.info_container,
            text="Upload and analyse an image\nto see crime intelligence here.",
            font=FONT_BODY, bg=BG_PANEL, fg=TEXT_MUTED, justify="center"
        ).pack(expand=True, pady=60)

    # ══════════════════════════════════════════════════════════════════════════
    # MODEL LOADING
    # ══════════════════════════════════════════════════════════════════════════

    def _browse_model(self):
        p = filedialog.askopenfilename(filetypes=[("Keras Model", "*.h5 *.keras")])
        if p:
            self.model_path.set(p)

    def _browse_labels(self):
        p = filedialog.askopenfilename(filetypes=[("Text File", "*.txt")])
        if p:
            self.labels_path.set(p)

    def _load_model_thread(self):
        self.btn_load.config(state="disabled", text="⏳ Loading…")
        self._set_status("⏳  Loading Keras model…", TEXT_MUTED)
        threading.Thread(target=self._load_model, daemon=True).start()

    def _load_model(self):
        try:
            import tensorflow as tf

            mp = self.model_path.get()
            lp = self.labels_path.get()

            if not os.path.exists(mp):
                self.after(0, lambda: messagebox.showerror(
                    "File Not Found", f"Model file not found:\n{mp}"))
                self.after(0, self._reset_load_btn)
                return

            self.model = tf.keras.models.load_model(mp, compile=False)

            if os.path.exists(lp):
                with open(lp, "r") as f:
                    raw = [l.strip() for l in f if l.strip()]
                # Teachable Machine format: "0 Assault"
                self.class_names = []
                for line in raw:
                    parts = line.split(" ", 1)
                    self.class_names.append(parts[1] if len(parts) == 2 else parts[0])
            else:
                self.class_names = ["Assault", "Hit and Run", "Murder", "Robbery"]

            self.is_model_loaded = True
            self.after(0, self._on_model_loaded)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Model Error", str(e)))
            self.after(0, self._reset_load_btn)

    def _on_model_loaded(self):
        self.model_badge.config(text="● Model loaded ✓", fg=ACCENT_GREEN)
        self.btn_load.config(state="normal", text="↺  RELOAD MODEL")
        self._set_status("✅  Model loaded successfully. Upload an image to begin.", ACCENT_GREEN)
        if self.image_path:
            self.btn_predict.config(state="normal")

    def _reset_load_btn(self):
        self.btn_load.config(state="normal", text="⬆  LOAD MODEL")
        self._set_status("❌  Failed to load model.", "#FF453A")

    # ══════════════════════════════════════════════════════════════════════════
    # IMAGE BROWSING & PREVIEW
    # ══════════════════════════════════════════════════════════════════════════

    def _browse_image(self):
        p = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp")])
        if p:
            self._load_image(p)

    def _load_image(self, path):
        self.image_path = path
        self.pil_image = Image.open(path).convert("RGB")
        img_thumb = self.pil_image.copy()
        img_thumb.thumbnail((200, 170))
        photo = ImageTk.PhotoImage(img_thumb)
        self.lbl_preview.config(image=photo, text="")
        self.lbl_preview.image = photo
        self.drop_zone.config(text="✔ Image Loaded\n" + os.path.basename(path),
                              fg=ACCENT_GREEN)
        self.btn_clear.config(state="normal")
        if self.is_model_loaded:
            self.btn_predict.config(state="normal")
        self._set_status(f"📂  Image loaded: {os.path.basename(path)}", ACCENT_BLUE)

    # ══════════════════════════════════════════════════════════════════════════
    # PREDICTION
    # ══════════════════════════════════════════════════════════════════════════

    def _predict(self):
        if not self.pil_image:
            messagebox.showwarning("No Image", "Please upload an image first.")
            return
        if not self.is_model_loaded:
            messagebox.showwarning("No Model", "Please load the Keras model first.")
            return
        self.btn_predict.config(state="disabled", text="⏳ Analysing…")
        self._set_status("🔍  Running inference…", TEXT_MUTED)
        threading.Thread(target=self._run_prediction, daemon=True).start()

    def _run_prediction(self):
        try:
            import tensorflow as tf

            # ── Preprocess for model ──────────────────────────────────────────
            img_size = 224  # Teachable Machine default
            img_resized = self.pil_image.resize((img_size, img_size))
            img_arr = np.array(img_resized, dtype=np.float32) / 255.0
            img_batch = np.expand_dims(img_arr, axis=0)

            preds = self.model.predict(img_batch, verbose=0)[0]

            # Map predictions to class names
            # Handles both 4-class and arbitrary label counts
            n = min(len(preds), len(self.class_names))
            label_map = {self.class_names[i]: float(preds[i]) for i in range(n)}

            # Best match from our known CRIME_DATA keys
            best_cls   = self.class_names[int(np.argmax(preds[:n]))]
            best_score = float(np.max(preds[:n]))

            # Map label to CRIME_DATA key (flexible match)
            crime_key = self._match_crime_key(best_cls)

            # Build preprocessing images
            views = self._build_preprocessing_views(self.pil_image)

            self.after(0, lambda: self._display_results(
                label_map, best_cls, best_score, crime_key, views))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Prediction Error", str(e)))
            self.after(0, lambda: self.btn_predict.config(
                state="normal", text="🔍  ANALYSE IMAGE"))

    def _match_crime_key(self, raw_label):
        """Flexible match from model label to CRIME_DATA key."""
        for key in CRIME_DATA:
            if key.lower() in raw_label.lower() or raw_label.lower() in key.lower():
                return key
        # Fallback: map index-style labels
        mapping = {"0": "Assault", "1": "Hit and Run", "2": "Murder", "3": "Robbery"}
        return mapping.get(raw_label.strip(), "Assault")

    def _build_preprocessing_views(self, img):
        """Return list of (numpy_array, title, colormap) for 6 preprocessing views."""
        img_rgb = img.resize((224, 224))
        views = []

        # 1. Original
        views.append((np.array(img_rgb), "Original", None))

        # 2. Grayscale
        gray = img_rgb.convert("L")
        views.append((np.array(gray), "Grayscale", "gray"))

        # 3. Normalised (enhanced contrast)
        norm = ImageOps.autocontrast(img_rgb)
        views.append((np.array(norm), "Normalised", None))

        # 4. Edge Detection (approximate via filter)
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edges = ImageOps.autocontrast(edges)
        views.append((np.array(edges), "Edges", "hot"))

        # 5. Sharpened
        sharp = img_rgb.filter(ImageFilter.SHARPEN)
        sharp = img_rgb.filter(ImageFilter.SHARPEN)
        views.append((np.array(sharp), "Sharpened", None))

        # 6. Histogram equalisation
        r, g, b = img_rgb.split()
        r_eq = ImageOps.equalize(r)
        g_eq = ImageOps.equalize(g)
        b_eq = ImageOps.equalize(b)
        hist_eq = Image.merge("RGB", (r_eq, g_eq, b_eq))
        views.append((np.array(hist_eq), "Hist-EQ", None))

        return views

    # ══════════════════════════════════════════════════════════════════════════
    # DISPLAY RESULTS
    # ══════════════════════════════════════════════════════════════════════════

    def _display_results(self, label_map, best_cls, best_score, crime_key, views):
        crime = CRIME_DATA.get(crime_key, CRIME_DATA["Assault"])

        # ── Update prediction card ────────────────────────────────────────────
        self.lbl_crime_emoji.config(text=crime["emoji"])
        self.lbl_crime_name.config(text=crime_key, fg=crime["color"])
        self.lbl_crime_ipc.config(text=crime["ipc"])

        # ── Update confidence bars ────────────────────────────────────────────
        classes_order = ["Assault", "Hit and Run", "Murder", "Robbery"]
        for cls in classes_order:
            # Try to find confidence for this class
            score = 0.0
            for lbl, val in label_map.items():
                if self._match_crime_key(lbl) == cls:
                    score = val
                    break
            pct = int(score * 100)
            bar_bg, bar_fg = self.conf_bars[cls]
            bar_bg.update_idletasks()
            w = bar_bg.winfo_width()
            bar_fg.place(x=0, y=0, relheight=1, width=int(w * score))
            self.conf_pcts[cls].config(text=f"{pct}%")

        # ── Update preprocessing axes ─────────────────────────────────────────
        self.fig.clear()
        self.fig.patch.set_facecolor(BG_DARK)
        axs = self.fig.subplots(1, 6)
        self.fig.subplots_adjust(left=0.02, right=0.98, top=0.88,
                                 bottom=0.04, wspace=0.22)

        for ax, (arr, title, cmap) in zip(axs, views):
            ax.set_facecolor(BG_CARD)
            ax.imshow(arr, cmap=cmap, aspect="auto")
            ax.set_title(title, color=TEXT_LABEL, fontsize=7, pad=3)
            ax.set_xticks([]); ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_color(crime["color"])
                sp.set_linewidth(1.2)

        self.canvas.draw()

        # ── Update quick stats ────────────────────────────────────────────────
        current = int(self.lbl_count.cget("text") or 0)
        self.lbl_count.config(text=str(current + 1))
        self.lbl_conf.config(text=f"{best_score*100:.1f}%")
        self.lbl_class.config(text=crime_key, fg=crime["color"])

        # ── Build right-panel info ─────────────────────────────────────────────
        self._build_crime_info(crime_key, crime, best_score)

        # ── Status ────────────────────────────────────────────────────────────
        self.btn_predict.config(state="normal", text="🔍  ANALYSE IMAGE")
        self._set_status(
            f"✅  Predicted: {crime_key}  ({best_score*100:.1f}% confidence)", ACCENT_GREEN)

    def _build_crime_info(self, crime_key, crime, confidence):
        """Populate the right-panel with description, state chart, suggestions."""
        container = self.info_container
        for w in container.winfo_children():
            w.destroy()

        W = 340  # approx panel width

        # ── Banner ─────────────────────────────────────────────────────────────
        banner = tk.Frame(container, bg=crime["color"], height=4)
        banner.pack(fill="x")

        tk.Label(container,
                 text=f"{crime['emoji']}  {crime_key}",
                 font=("Segoe UI", 14, "bold"),
                 bg=BG_PANEL, fg=crime["color"]).pack(anchor="w", padx=14, pady=(10, 2))

        tk.Label(container, text=f"Confidence: {confidence*100:.1f}%",
                 font=FONT_MONO, bg=BG_PANEL, fg=TEXT_MUTED).pack(anchor="w", padx=14)

        tk.Label(container, text=crime["ipc"],
                 font=FONT_MONO, bg=BG_PANEL, fg=TEXT_MUTED).pack(anchor="w", padx=14, pady=(0, 8))

        # ── Description ────────────────────────────────────────────────────────
        self._section_label(container, "📖  DESCRIPTION")
        desc_frame = tk.Frame(container, bg=BG_CARD,
                              highlightthickness=1, highlightbackground=BORDER)
        desc_frame.pack(fill="x", padx=12, pady=(0, 8))
        tk.Label(
            desc_frame, text=crime["description"],
            font=FONT_SMALL, bg=BG_CARD, fg=TEXT_LABEL,
            wraplength=W - 30, justify="left"
        ).pack(padx=10, pady=10, anchor="w")

        # ── State Bar Chart ────────────────────────────────────────────────────
        self._section_label(container, "🗺  MOST AFFECTED STATES (Crime Rate Index)")
        chart_frame = tk.Frame(container, bg=BG_DARK,
                               highlightthickness=1, highlightbackground=BORDER)
        chart_frame.pack(fill="x", padx=12, pady=(0, 8))

        state_fig = Figure(figsize=(3.4, 2.6), dpi=88, facecolor=BG_DARK)
        state_fig.subplots_adjust(left=0.05, right=0.78, top=0.92, bottom=0.08)
        ax = state_fig.add_subplot(111)
        ax.set_facecolor(BG_CARD)

        states = list(crime["states"].keys())
        values = list(crime["states"].values())
        colors = [crime["color"] if v == max(values)
                  else self._dim_color(crime["color"], 0.55) for v in values]

        bars = ax.barh(states, values, color=colors, height=0.6)
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    str(val), va="center", ha="left",
                    color=TEXT_MUTED, fontsize=6.5)

        ax.set_xlim(0, max(values) + 14)
        ax.set_xlabel("Crime Rate Index", color=TEXT_MUTED, fontsize=7)
        ax.tick_params(colors=TEXT_MUTED, labelsize=6.5)
        for sp in ax.spines.values():
            sp.set_color(BORDER)
        ax.invert_yaxis()

        state_canvas = FigureCanvasTkAgg(state_fig, master=chart_frame)
        state_canvas.get_tk_widget().pack(fill="x", padx=4, pady=4)
        state_canvas.draw()

        # ── Suggestions ────────────────────────────────────────────────────────
        self._section_label(container, "💡  RECOMMENDATIONS & ACTIONS")
        for tip in crime["suggestions"]:
            tip_f = tk.Frame(container, bg=BG_CARD,
                             highlightthickness=1, highlightbackground=BORDER)
            tip_f.pack(fill="x", padx=12, pady=2)
            tk.Label(
                tip_f, text=tip,
                font=FONT_SMALL, bg=BG_CARD, fg=TEXT_LABEL,
                wraplength=W - 24, justify="left", anchor="w"
            ).pack(padx=10, pady=6, anchor="w")

        # Padding at bottom
        tk.Frame(container, bg=BG_PANEL, height=20).pack()

    # ══════════════════════════════════════════════════════════════════════════
    # UTILITIES
    # ══════════════════════════════════════════════════════════════════════════

    def _dim_color(self, hex_color, factor=0.5):
        """Return a dimmed version of a hex colour."""
        h = hex_color.lstrip("#")
        r, g, b = [int(h[i:i+2], 16) for i in (0, 2, 4)]
        return "#{:02x}{:02x}{:02x}".format(
            int(r * factor), int(g * factor), int(b * factor))

    def _set_status(self, msg, color=TEXT_MUTED):
        self.status_var.set(msg)

    def _clear_all(self):
        self.image_path = None
        self.pil_image = None
        self.lbl_preview.config(image="", text="No image loaded")
        self.lbl_preview.image = None
        self.drop_zone.config(text="Click to Upload\nImage File", fg=TEXT_MUTED)
        self.btn_predict.config(state="disabled")
        self.btn_clear.config(state="disabled")
        self.lbl_crime_emoji.config(text="🔍")
        self.lbl_crime_name.config(text="Awaiting Input", fg=TEXT_PRIMARY)
        self.lbl_crime_ipc.config(text="")
        for cls in self.conf_bars:
            _, bar_fg = self.conf_bars[cls]
            bar_fg.place(width=0)
            self.conf_pcts[cls].config(text="0%")
        self.lbl_conf.config(text="—")
        self.lbl_class.config(text="—", fg=ACCENT_BLUE)
        self._blank_axes()
        self.canvas.draw()
        self._show_placeholder_info()
        self._set_status("✕  Cleared. Ready for new image.", TEXT_MUTED)


# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # DPI awareness for Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = CrimeClassifierApp()
    app.mainloop()
