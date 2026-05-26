# Model
"""
maingui.py - AI Subtitle Engine
Yeu cau: pip install customtkinter deep-translator openai-whisper torch
"""
import os
import threading
import tkinter as tk
from tkinter import filedialog
from typing import Optional, Callable

import customtkinter as ctk

from modules.ai_engine import AIEngine
from modules.translator import SubtitleTranslator

# ---------------------------------------------------------------------------
# Du lieu
# ---------------------------------------------------------------------------
FULL_LANGUAGES: list[str] = [
    "Afrikaans","Albanian","Amharic","Arabic","Armenian","Assamese","Azerbaijani",
    "Bashkir","Basque","Belarusian","Bengali","Bosnian","Breton","Bulgarian","Burmese",
    "Catalan","Chinese","Croatian","Czech","Danish","Dutch","English","Estonian",
    "Faroese","Finnish","French","Galician","Georgian","German","Greek","Gujarati",
    "Haitian Creole","Hausa","Hawaiian","Hebrew","Hindi","Hungarian","Icelandic","Igbo",
    "Indonesian","Italian","Japanese","Javanese","Kannada","Kazakh","Khmer","Korean",
    "Lao","Latin","Latvian","Lingala","Lithuanian","Luxembourgish","Macedonian","Malagasy",
    "Malay","Malayalam","Maltese","Maori","Marathi","Mongolian","Nepali","Norwegian",
    "Nynorsk","Occitan","Pashto","Persian","Polish","Portuguese","Punjabi","Romanian",
    "Russian","Sanskrit","Serbian","Shona","Sindhi","Sinhala","Slovak","Slovenian",
    "Somali","Spanish","Sundanese","Swahili","Swedish","Tagalog","Tajik","Tamil",
    "Tatar","Telugu","Thai","Tibetan","Turkish","Turkmen","Ukrainian","Urdu",
    "Uzbek","Vietnamese","Welsh","Yiddish","Yoruba",
]
LANGUAGE_CODES: dict[str, str] = {
    "Vietnamese":"vi","English":"en","Japanese":"ja","Korean":"ko",
    "Chinese":"zh-cn","French":"fr","German":"de","Thai":"th",
    "Spanish":"es","Portuguese":"pt","Russian":"ru","Indonesian":"id",
}
SOURCE_LANGS:    list[str] = ["Auto Detect"] + FULL_LANGUAGES
WHISPER_MODELS:  list[str] = ["tiny","base","small","medium","large"]
OUTPUT_FORMATS:  list[str] = [".srt",".txt"]
API_PROVIDERS:   list[str] = ["Local","OpenAI","DeepSeek","Gemini"]
OPENAI_MODELS:   list[str] = ["gpt-4o","gpt-4o-mini","gpt-3.5-turbo"]
DEEPSEEK_MODELS: list[str] = ["deepseek-chat","deepseek-reasoner"]
GEMINI_MODELS:   list[str] = ["gemini-2.0-flash","gemini-1.5-pro"]
CONTENT_STYLES:  list[str] = ["Tổng Quát","Vui nhộn","Nghiêm túc"]
STYLE_DESC: dict[str,str] = {
    "Tong quat":  "phù hợp mọi nội dung",
    "Vui nhon":   "nhẹ nhàng, vui vẻ",
    "Nghiem tuc": "trịnh trọng, chính xác",
}

# ---------------------------------------------------------------------------
# Bang mau
# ---------------------------------------------------------------------------
THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "bg":       "#111115",
        "surface":  "#1c1c22",
        "surface2": "#26262e",
        "border":   "#35354a",
        "accent":   "#7c6af7",
        "accent2":  "#5b4fcf",
        "text":     "#f0f0f0",       # trang gan nhu trang
        "text_muted": "#9090a8",
        "text_dim": "#55556a",
        "success":  "#34d399",
        "error":    "#f87171",
        "log_bg":   "#0d0d10",
        "sa":       "#7c6af7",       # seg active bg
        "si":       "#26262e",       # seg idle bg
        "sfa":      "#ffffff",       # seg active fg
        "sfi":      "#9090a8",       # seg idle fg
    },
    "light": {
        "bg":       "#f0f0f5",
        "surface":  "#f0f0f5",
        "surface2": "#E4E4E4",
        "border":   "#d0d0e0",
        "accent":   "#6052d4",
        "accent2":  "#4a3db8",
        "text":     "#111111",       # den gan nhu den
        "text_muted": "#505060",
        "text_dim": "#a0a0b8",
        "success":  "#059669",
        "error":    "#dc2626",
        "log_bg":   "#fafafe",
        "sa":       "#6052d4",
        "si":       "#e8e8f5",
        "sfa":      "#ffffff",
        "sfi":      "#505060",
    },
}

FT = ("Georgia", 18, "bold")
FL = ("Georgia", 11)
FM = ("Courier New", 10)
FB = ("Georgia", 11, "bold")
FS = ("Georgia", 9, "bold")
P  = 12   # padding chung


# ---------------------------------------------------------------------------
# Lop chinh
# ---------------------------------------------------------------------------
class SubtitleAppUI(ctk.CTk):

    def __init__(self) -> None:
        super().__init__()
        self._mode: str = "dark"
        self._C: dict[str, str] = THEMES["dark"]
        self._dd: Optional[tk.Listbox] = None
        self._segs: list[tuple] = []
        self.selected_file: Optional[str] = None
        self._busy: bool = False
        self._key_visible: bool = False

        self.var_api_provider  = tk.StringVar(value="Local")
        self.var_api_model     = tk.StringVar(value="")
        self.var_api_key       = tk.StringVar(value="")
        self.var_output_format = tk.StringVar(value=".srt")
        self.var_skip_words    = tk.StringVar(value="")
        self.var_content_style = tk.StringVar(value="Tong quat")

        ctk.set_appearance_mode("dark")
        self.title("AI Subtitle Engine")
        self.geometry("780x680")
        self.minsize(700, 620)
        self.resizable(True, True)

        self._build()
        self._apply_theme()

    # ==========================================================================
    # BUILD
    # ==========================================================================
    def _build(self) -> None:
        C = self._C
        self.frame_root = tk.Frame(self, bg=C["bg"])
        self.frame_root.pack(fill="both", expand=True)

        self._build_header()

        # Body co dan theo cua so
        self.frame_body = tk.Frame(self.frame_root, bg=C["bg"])
        self.frame_body.pack(fill="both", expand=True, padx=P, pady=P)
        self.frame_body.columnconfigure(0, weight=1)

        # --- Hang 1: File (trai, ngang) ---
        self._build_file_row()

        # --- Hang 2: API (full width) ---
        self._build_api_section()

        # --- Hang 3: Config (2/3) + Style (1/3) ---
        self._build_config_style_row()

        # --- Hang 4: Output format (1/3) + Skip words (2/3) ---
        self._build_output_skip_row()

        # --- Hang 5: Log + Progress ---
        self._build_log_section()

        # --- Hang 6: Buttons ---
        self._build_actions()

    # ---------- Header --------------------------------------------------------
    def _build_header(self) -> None:
        C = self._C
        self.frame_header = tk.Frame(self.frame_root, bg=C["surface"], height=52)
        self.frame_header.pack(fill="x")
        self.frame_header.pack_propagate(False)

        self.lbl_icon = tk.Label(self.frame_header, text="◈",
                                 font=("Georgia",18), bg=C["surface"], fg=C["accent"])
        self.lbl_icon.pack(side="left", padx=(P,4), pady=8)

        self.lbl_title = tk.Label(self.frame_header, text="AI Subtitle Engine",
                                  font=FT, bg=C["surface"], fg=C["text"])
        self.lbl_title.pack(side="left")

        self.lbl_ver = tk.Label(self.frame_header, text="v2.0",
                                font=("Georgia",8), bg=C["surface"], fg=C["text_muted"])
        self.lbl_ver.pack(side="left", padx=(3,0), pady=(18,0))

        self.btn_theme = tk.Button(
            self.frame_header, text="☀ Light", font=("Georgia",9,"bold"),
            bg=C["surface2"], fg=C["accent"],
            activebackground=C["border"], activeforeground=C["accent"],
            relief="flat", bd=0, padx=10, pady=5, cursor="hand2",
            command=self._toggle_theme)
        self.btn_theme.pack(side="right", padx=P, pady=10)

        self.frame_hline = tk.Frame(self.frame_root, bg=C["accent"], height=2)
        self.frame_hline.pack(fill="x")

    # ---------- Hang 1: File --------------------------------------------------
    def _build_file_row(self) -> None:
        C = self._C
        self.card_file_sec = self._section(self.frame_body, "MEDIA FILE")
        inner = tk.Frame(self.card_file_sec, bg=C["surface"])
        self.inner_file = inner
        inner.pack(fill="x", padx=P, pady=(0, P))

        # Nut chon file ben trai
        self.btn_browse = tk.Button(
            inner, text="  Chọn file  ", font=("Georgia",10),
            bg=C["accent"], fg="#ffffff", activebackground=C["accent2"],
            relief="flat", bd=0, padx=14, pady=8, cursor="hand2",
            command=self._browse_file)
        self.btn_browse.pack(side="left")

        # Icon + ten file ben phai nut
        self.lbl_file_icon = tk.Label(inner, text="○",
                                      font=("Georgia",13), bg=C["surface"], fg=C["text_dim"])
        self.lbl_file_icon.pack(side="left", padx=(10, 4))

        self.lbl_file_name = tk.Label(inner, text="Chưa chọn file",
                                      font=FL, bg=C["surface"], fg=C["text_muted"],
                                      anchor="w")
        self.lbl_file_name.pack(side="left", fill="x", expand=True)

    # ---------- Hang 2: API ---------------------------------------------------
    def _build_api_section(self) -> None:
        C = self._C
        self.card_api_sec = self._section(self.frame_body, "CẤU HÌNH API")
        g = tk.Frame(self.card_api_sec, bg=C["surface"])
        self.inner_api = g
        g.pack(fill="x", padx=P, pady=(0, P))
        g.columnconfigure(1, weight=1)
        g.columnconfigure(3, weight=1)

        # Col 0-1: Nha cung cap
        self.lbl_api_prov = self._lbl(g, 0, 0, "Nhà cung cấp")
        self.frame_prov_seg = self._seg(g, 0, 1, API_PROVIDERS,
                                        self.var_api_provider,
                                        on_change=self._on_provider_change)

        # Col 2-3: Model (dong/mo theo provider)
        self.lbl_api_model = self._lbl(g, 0, 2, "Model: ")
        self.frame_api_model_seg = tk.Frame(g, bg=C["surface"])
        self.frame_api_model_seg.grid(row=0, column=3, sticky="ew", padx=(0,P), pady=6)


        # Hang 1: API Key (full width)
        self.lbl_api_key_lbl = self._lbl(g, 1, 0, "API Key")
        self.key_row = key_row = tk.Frame(g, bg=C["surface"])
        key_row.grid(row=1, column=1, columnspan=3, sticky="ew", pady=6, padx=(0,P))
        key_row.columnconfigure(0, weight=1)

        self.entry_api_key = tk.Entry(
            key_row, textvariable=self.var_api_key,
            font=FL, show="●",
            bg=C["surface2"], fg=C["text"], insertbackground=C["accent"],
            relief="flat", bd=3,
            highlightbackground=C["border"], highlightthickness=1,
            highlightcolor=C["accent"])
        self.entry_api_key.grid(row=0, column=0, sticky="ew", ipady=4)

        self.btn_toggle_key = tk.Button(
            key_row, text="◉", font=("Georgia",11),
            bg=C["surface2"], fg=C["text_muted"],
            activebackground=C["border"], activeforeground=C["accent"],
            relief="flat", bd=0, padx=6, pady=3, cursor="hand2",
            command=self._toggle_key_vis)
        self.btn_toggle_key.grid(row=0, column=1, padx=(4,0))
        self._on_provider_change("Local")

    # ---------- Hang 3: Config + Style ----------------------------------------
    def _build_config_style_row(self) -> None:
        C = self._C
        row_frame = tk.Frame(self.frame_body, bg=C["bg"])
        row_frame.pack(fill="x", pady=(0, 6))
        row_frame.columnconfigure(0, weight=2)
        row_frame.columnconfigure(1, weight=1)
        row_frame.rowconfigure(0, weight=1)

        # -- Config (2/3) --
        wrap_cfg = tk.Frame(row_frame, bg=C["bg"])
        self.wrap_cfg = wrap_cfg
        wrap_cfg.grid(row=0, column=0, sticky="nsew", padx=(0,4))
        self.card_cfg_sec = self._section(wrap_cfg, "CẤU HÌNH NHẬN DIỆN")
        g = tk.Frame(self.card_cfg_sec, bg=C["surface"])
        self.inner_cfg = g
        g.pack(fill="x", padx=P, pady=(0,P))
        g.columnconfigure(1, weight=1)

        self.lbl_model = self._lbl(g, 0, 0, "Mô hình")
        self.var_model = tk.StringVar(value="base")
        self.frame_model_seg = self._seg(g, 0, 1, WHISPER_MODELS, self.var_model)

        self.lbl_src_lang = self._lbl(g, 1, 0, "Ngôn ngữ gốc")
        self.var_src_lang = tk.StringVar(value="Auto Detect")
        self.entry_src_lang = self._smart_entry(g, 1, self.var_src_lang, SOURCE_LANGS)

        self.lbl_dst_lang = self._lbl(g, 2, 0, "Dịch sang")
        self.var_dst_lang = tk.StringVar(value="Vietnamese")
        self.entry_dst_lang = self._smart_entry(g, 2, self.var_dst_lang, FULL_LANGUAGES)

        # -- Style (1/3) --
        wrap_sty = tk.Frame(row_frame, bg=C["bg"])
        self.wrap_sty = wrap_sty
        wrap_sty.grid(row=0, column=1, sticky="nsew", padx=(4,0))
        self.card_sty_sec = self._section(wrap_sty, "PHONG CÁCH")
        inner_sty = tk.Frame(self.card_sty_sec, bg=C["surface"])
        self.inner_sty = inner_sty
        inner_sty.pack(fill="x", padx=P, pady=(0,P))

        self.frame_style_seg = self._seg_pack(
            inner_sty, CONTENT_STYLES, self.var_content_style,
            on_change=self._on_style_change)
        self.frame_style_seg.pack(anchor="w", pady=(8, 6))

        self.lbl_style_desc = tk.Label(
            inner_sty, text=STYLE_DESC["Tong quat"],
            font=("Courier New",8), bg=C["surface"], fg=C["text_dim"],
            justify="left", anchor="w", wraplength=150)
        self.lbl_style_desc.pack(anchor="w")

        self.frame_row_config_style = row_frame

    # ---------- Hang 4: Output + Skip -----------------------------------------
    def _build_output_skip_row(self) -> None:
        C = self._C
        row_frame = tk.Frame(self.frame_body, bg=C["bg"])
        row_frame.pack(fill="x", pady=(0, 6))
        row_frame.columnconfigure(0, weight=1)
        row_frame.columnconfigure(1, weight=2)
        row_frame.rowconfigure(0, weight=1)

        # -- Output format (1/3) --
        wrap_out = tk.Frame(row_frame, bg=C["bg"])
        self.wrap_out = wrap_out
        wrap_out.grid(row=0, column=0, sticky="nsew", padx=(0,4))
        self.card_out_sec = self._section(wrap_out, "ĐỊNH DẠNG XUẤT")
        inner_out = tk.Frame(self.card_out_sec, bg=C["surface"])
        self.inner_out = inner_out
        inner_out.pack(fill="x", padx=P, pady=(0,P))

        self.frame_out_seg = self._seg_pack(inner_out, OUTPUT_FORMATS,
                                            self.var_output_format)
        self.frame_out_seg.pack(anchor="w", pady=(8,4))

        self.lbl_fmt_desc = tk.Label(
            inner_out, text=".srt = co timestamp\n.txt = van ban thuan",
            font=("Courier New",8), bg=C["surface"], fg=C["text_dim"],
            justify="left", anchor="w")
        self.lbl_fmt_desc.pack(anchor="w")

        # -- Skip words (2/3) --
        wrap_skip = tk.Frame(row_frame, bg=C["bg"])
        self.wrap_skip = wrap_skip
        wrap_skip.grid(row=0, column=1, sticky="nsew", padx=(4,0))
        self.card_skip_sec = self._section(wrap_skip, "KHÓA TỪ KHÔNG DỊCH")
        inner_skip = tk.Frame(self.card_skip_sec, bg=C["surface"])
        self.inner_skip = inner_skip
        inner_skip.pack(fill="x", padx=P, pady=(0,P))

        self.lbl_skip_hint = tk.Label(
            inner_skip, text="Các từ muốn giữ nguyên (ngăn cách bằng dấu phẩy):",
            font=("Georgia",9), bg=C["surface"], fg=C["text_muted"], anchor="w")
        self.lbl_skip_hint.pack(fill="x", pady=(0,4))

        self.skip_row = skip_row = tk.Frame(inner_skip, bg=C["surface"])
        skip_row.pack(fill="x")
        skip_row.columnconfigure(0, weight=1)

        self.entry_skip = tk.Entry(
            skip_row, textvariable=self.var_skip_words, font=FL,
            bg=C["surface2"], fg=C["text"], insertbackground=C["accent"],
            relief="flat", bd=3,
            highlightbackground=C["border"], highlightthickness=1,
            highlightcolor=C["accent"])
        self.entry_skip.grid(row=0, column=0, sticky="ew", ipady=4)

        self.btn_skip_clear = tk.Button(
            skip_row, text="✕", font=("Georgia",9),
            bg=C["surface2"], fg=C["text_muted"],
            activebackground=C["border"], activeforeground=C["text"],
            relief="flat", bd=0, padx=7, pady=4, cursor="hand2",
            command=lambda: self.var_skip_words.set(""))
        self.btn_skip_clear.grid(row=0, column=1, padx=(4,0))

        self.lbl_skip_eg = tk.Label(
            inner_skip, text='VD: "Quân, Tom,...."',
            font=("Courier New",8), bg=C["surface"], fg=C["text_dim"], anchor="w")
        self.lbl_skip_eg.pack(fill="x", pady=(4,0))

        self.frame_row_pair = row_frame

    # ---------- Hang 5: Log + Progress ----------------------------------------
    def _build_log_section(self) -> None:
        C = self._C
        sec = self._section(self.frame_body, "NHẬT KÝ XỬ LÝ")

        self.text_log = tk.Text(
            sec, height=4, wrap="word",
            font=FM, bd=0, relief="flat",
            bg=C["log_bg"], fg=C["text_muted"],
            insertbackground=C["accent"],
            selectbackground=C["accent"], selectforeground="#ffffff",
            state="disabled")
        self.text_log.pack(fill="x", padx=P, pady=(8, 6))

        # Progress bar
        self.frame_prog_track = tk.Frame(sec, bg=C["surface2"], height=3)
        self.frame_prog_track.pack(fill="x", padx=P, pady=(0,P))
        self.frame_prog_fill = tk.Frame(self.frame_prog_track, bg=C["accent"], height=3)
        self.frame_prog_fill.place(x=0, y=0, relheight=1, width=0)

        self.card_log = sec
        self._log("Hệ thống sẵn sàng")

    # ---------- Hang 6: Buttons -----------------------------------------------
    def _build_actions(self) -> None:
        C = self._C
        self.frame_actions = tk.Frame(self.frame_body, bg=C["bg"])
        self.frame_actions.pack(fill="x", pady=(4, 0))

        self.btn_run = tk.Button(
            self.frame_actions, text="▶ Chạy",
            font=FB, bg=C["accent"], fg="#ffffff",
            activebackground=C["accent2"], activeforeground="#ffffff",
            relief="flat", bd=0, padx=22, pady=10, cursor="hand2",
            command=self._start)
        self.btn_run.pack(side="left")

        self.btn_clear_log = tk.Button(
            self.frame_actions, text="Xóa log",
            font=("Georgia",10), bg=C["surface2"], fg=C["text_muted"],
            activebackground=C["border"], activeforeground=C["text"],
            relief="flat", bd=0, padx=14, pady=10, cursor="hand2",
            command=self._clear_log)
        self.btn_clear_log.pack(side="left", padx=8)

        self.btn_quit = tk.Button(
            self.frame_actions, text="Thoát",
            font=("Georgia",10), bg=C["surface2"], fg=C["text_muted"],
            activebackground=C["border"], activeforeground=C["text"],
            relief="flat", bd=0, padx=14, pady=10, cursor="hand2",
            command=self.quit)
        self.btn_quit.pack(side="right")

    # ==========================================================================
    # WIDGET HELPERS
    # ==========================================================================
    def _section(self, parent: tk.Frame, title: str) -> tk.Frame:
        """Card voi thanh tieu de."""
        C = self._C
        wrap = tk.Frame(parent, bg=C["bg"])
        wrap.pack(fill="x", pady=(0, 6))

        outer = tk.Frame(wrap, bg=C["surface"],
                         highlightbackground=C["border"], highlightthickness=1)
        outer.pack(fill="x")

        hbar = tk.Frame(outer, bg=C["surface2"], height=26)
        hbar.pack(fill="x")
        hbar.pack_propagate(False)
        tk.Frame(hbar, bg=C["accent"], width=3).place(x=0, y=0, relheight=1)
        tk.Label(hbar, text=f"  {title}", font=FS,
                 bg=C["surface2"], fg=C["text_muted"]).pack(side="left", padx=10)
        return outer

    def _lbl(self, parent: tk.Frame, row: int, col: int, text: str) -> tk.Label:
        lbl = tk.Label(parent, text=text, font=FL,
                       bg=self._C["surface"], fg=self._C["text_muted"], anchor="w")
        lbl.grid(row=row, column=col, padx=(0,8) if col > 0 else (0,12),
                 pady=8, sticky="w")
        return lbl

    def _seg(self, parent: tk.Frame, row: int, col: int,
             options: list[str], var: tk.StringVar,
             on_change: Optional[Callable] = None) -> tk.Frame:
        """Segmented buttons dung grid."""
        C = self._C
        frame = tk.Frame(parent, bg=C["surface"])
        frame.grid(row=row, column=col, sticky="ew", pady=6,
                   padx=(0, P) if col > 1 else 0)
        buttons: list[tuple[tk.Button, str]] = []

        def refresh(val: str) -> None:
            T = self._C   # luon lay mau hien tai, khong dung closure C cu
            frame.config(bg=T["surface"])
            for b, v in buttons:
                a = v == val
                b.config(bg=T["sa"] if a else T["si"],
                         fg=T["sfa"] if a else T["sfi"],
                         activebackground=T["sa"],
                         activeforeground=T["sfa"])

        for opt in options:
            b = tk.Button(frame, text=opt, font=("Courier New",9,"bold"),
                          relief="flat", bd=0, padx=9, pady=4, cursor="hand2",
                          command=lambda v=opt: (var.set(v), refresh(v),
                                                 on_change(v) if on_change else None))
            b.pack(side="left", padx=2)
            buttons.append((b, opt))

        refresh(var.get())
        self._segs.append((buttons, var, refresh))
        return frame

    def _seg_pack(self, parent: tk.Frame, options: list[str],
                  var: tk.StringVar,
                  on_change: Optional[Callable] = None) -> tk.Frame:
        """Segmented buttons dung pack."""
        C = self._C
        frame = tk.Frame(parent, bg=C["surface"])
        buttons: list[tuple[tk.Button, str]] = []

        def refresh(val: str) -> None:
            T = self._C   # luon lay mau hien tai
            frame.config(bg=T["surface"])
            for b, v in buttons:
                a = v == val
                b.config(bg=T["sa"] if a else T["si"],
                         fg=T["sfa"] if a else T["sfi"],
                         activebackground=T["sa"],
                         activeforeground=T["sfa"])

        for opt in options:
            b = tk.Button(frame, text=opt, font=("Courier New",9,"bold"),
                          relief="flat", bd=0, padx=9, pady=4, cursor="hand2",
                          command=lambda v=opt: (var.set(v), refresh(v),
                                                 on_change(v) if on_change else None))
            b.pack(side="left", padx=2)
            buttons.append((b, opt))

        refresh(var.get())
        self._segs.append((buttons, var, refresh))
        return frame

    def _smart_entry(self, parent: tk.Frame, row: int,
                     var: tk.StringVar, data: list[str]) -> tk.Entry:
        C = self._C
        e = tk.Entry(parent, textvariable=var, font=FL,
                     bg=C["surface2"], fg=C["text"],
                     insertbackground=C["accent"],
                     relief="flat", bd=3,
                     highlightbackground=C["border"],
                     highlightthickness=1, highlightcolor=C["accent"])
        e.grid(row=row, column=1, sticky="ew", pady=6, ipady=4)
        e.last_valid = var.get()  # type: ignore[attr-defined]
        e.bind("<FocusIn>",    lambda _ev: self._fi(e, var, data))
        e.bind("<FocusOut>",   lambda _ev: self._fo(e, var, data))
        e.bind("<KeyRelease>", lambda ev:  self._kt(ev, e, var, data))
        e.bind("<Escape>",     lambda _ev: self.focus_set())
        return e

    # ==========================================================================
    # PROVIDER CHANGE
    # ==========================================================================
    def _on_provider_change(self, provider: str) -> None:
        C = self._C
        for w in self.frame_api_model_seg.winfo_children():
            w.destroy()
        if provider == "Local":
            tk.Label(self.frame_api_model_seg,
                     text="(Whisper offline)",
                     font=("Courier New",9), bg=C["surface"],
                     fg=C["text_dim"]).pack(side="left")
            self.entry_api_key.config(state="disabled")
            self.btn_toggle_key.config(state="disabled")
        else:
            model_list = {"OpenAI": OPENAI_MODELS,
                          "DeepSeek": DEEPSEEK_MODELS,
                          "Gemini": GEMINI_MODELS}.get(provider, [])
            if model_list and self.var_api_model.get() not in model_list:
                self.var_api_model.set(model_list[0])
            buttons: list[tuple[tk.Button, str]] = []

            def refresh_model(val: str) -> None:
                T = self._C   # luon lay mau hien tai
                self.frame_api_model_seg.config(bg=T["surface"])
                for b, v in buttons:
                    a = v == val
                    b.config(bg=T["sa"] if a else T["si"],
                             fg=T["sfa"] if a else T["sfi"],
                             activebackground=T["sa"],
                             activeforeground=T["sfa"])

            for opt in model_list:
                b = tk.Button(
                    self.frame_api_model_seg, text=opt,
                    font=("Courier New",9,"bold"),
                    relief="flat", bd=0, padx=8, pady=4, cursor="hand2",
                    command=lambda v=opt: (self.var_api_model.set(v),
                                          refresh_model(v)))
                b.pack(side="left", padx=2)
                buttons.append((b, opt))
            refresh_model(self.var_api_model.get())
            self.entry_api_key.config(state="normal")
            self.btn_toggle_key.config(state="normal")

    def _on_style_change(self, style: str) -> None:
        self.lbl_style_desc.config(text=STYLE_DESC.get(style, ""))

    # ==========================================================================
    # AUTOCOMPLETE
    # ==========================================================================
    def _fi(self, e: tk.Entry, var: tk.StringVar, data: list[str]) -> None:
        if var.get() in data:
            e.last_valid = var.get()  # type: ignore[attr-defined]
        var.set("")
        self.after(10, lambda: self._refresh_dd(e, var, data))

    def _fo(self, e: tk.Entry, var: tk.StringVar, data: list[str]) -> None:
        def restore() -> None:
            if self._dd:
                self._dd.destroy()
                self._dd = None
            if var.get() not in data:
                var.set(getattr(e, "last_valid", data[0]))
        self.after(200, restore)

    def _kt(self, ev: tk.Event, e: tk.Entry,
            var: tk.StringVar, data: list[str]) -> None:
        if ev.keysym in ("Up", "Down", "Return"):
            return
        self._refresh_dd(e, var, data)

    def _refresh_dd(self, e: tk.Entry,
                    var: tk.StringVar, data: list[str]) -> None:
        typed = var.get().lower()
        hits  = data if not typed else [x for x in data if typed in x.lower()]
        self._show_dd(e, var, hits)

    def _show_dd(self, e: tk.Entry,
                 var: tk.StringVar, hits: list[str]) -> None:
        C = self._C
        if self._dd:
            self._dd.destroy()
            self._dd = None
        if not hits:
            return
        x = e.winfo_rootx() - self.winfo_rootx()
        y = e.winfo_rooty() - self.winfo_rooty() + e.winfo_height() + 2
        lb = tk.Listbox(self, font=FL, bg=C["surface"], fg=C["text"],
                        selectbackground=C["accent"], selectforeground="#ffffff",
                        highlightthickness=1, highlightbackground=C["border"],
                        relief="flat", activestyle="none",
                        height=min(6, len(hits)), bd=0)
        lb.place(x=x, y=y, width=e.winfo_width())
        for h in hits:
            lb.insert("end", h)

        def pick(_ev: tk.Event) -> None:
            if lb.curselection():
                val = lb.get(lb.curselection()[0])
                var.set(val)
                e.last_valid = val  # type: ignore[attr-defined]
                lb.destroy()
                self._dd = None
                self.focus_set()

        lb.bind("<<ListboxSelect>>", pick)
        lb.lift()
        self._dd = lb

    # ==========================================================================
    # TOGGLE KEY / THEME
    # ==========================================================================
    def _toggle_key_vis(self) -> None:
        self._key_visible = not self._key_visible
        self.entry_api_key.config(show="" if self._key_visible else "●")
        self.btn_toggle_key.config(
            fg=self._C["accent"] if self._key_visible else self._C["text_muted"])

    def _toggle_theme(self) -> None:
        self._mode = "light" if self._mode == "dark" else "dark"
        self._C    = THEMES[self._mode]
        ctk.set_appearance_mode(self._mode)
        self._apply_theme()

    # ==========================================================================
    # APPLY THEME
    # ==========================================================================
    def _apply_theme(self) -> None:
        C = self._C
        btn_lbl = "☀ Light" if self._mode == "dark" else "◑ Dark"

        # ── Header ──────────────────────────────────────────────────────────
        self.frame_root.config(bg=C["bg"])
        self.frame_header.config(bg=C["surface"])
        self.frame_hline.config(bg=C["accent"])
        self.lbl_icon.config(bg=C["surface"], fg=C["accent"])
        self.lbl_title.config(bg=C["surface"], fg=C["text"])
        self.lbl_ver.config(bg=C["surface"], fg=C["text_muted"])
        self.btn_theme.config(text=btn_lbl, bg=C["surface2"], fg=C["accent"],
                              activebackground=C["border"],
                              activeforeground=C["accent"])

        # ── Body wrapper frames ──────────────────────────────────────────────
        self.frame_body.config(bg=C["bg"])
        self.frame_row_config_style.config(bg=C["bg"])
        self.frame_row_pair.config(bg=C["bg"])
        self.wrap_cfg.config(bg=C["bg"])
        self.wrap_sty.config(bg=C["bg"])
        self.wrap_out.config(bg=C["bg"])
        self.wrap_skip.config(bg=C["bg"])

        # ── File row ────────────────────────────────────────────────────────
        self.btn_browse.config(bg=C["accent"], fg="#ffffff",
                               activebackground=C["accent2"],
                               activeforeground="#ffffff")
        self.lbl_file_icon.config(bg=C["surface"], fg=C["text_dim"])
        self.lbl_file_name.config(bg=C["surface"], fg=C["text_muted"])

        # ── Tat ca Section cards: chi cap nhat border + bg ───────────────────
        # Ham nho: to mau 1 card (outer frame)
        def paint_card(card: tk.Frame) -> None:
            # Cap nhat ca wrap frame (parent cua outer card)
            card_parent = card.master
            if isinstance(card_parent, tk.Frame):
                card_parent.config(bg=C["bg"])
            card.config(bg=C["surface"], highlightbackground=C["border"])
            for child in card.winfo_children():
                if not isinstance(child, tk.Frame):
                    continue
                # Phan biet header bar (cao < 40px) vs inner frame
                child.config(bg=C["surface2"] if child.winfo_reqheight() <= 30
                             else C["surface"])
                # Chi cap nhat Label va Frame con truc tiep (accent bar 3px)
                for sub in child.winfo_children():
                    if isinstance(sub, tk.Label):
                        sub.config(bg=child.cget("bg"), fg=C["text_muted"])
                    elif isinstance(sub, tk.Frame) and sub.winfo_reqwidth() == 3:
                        sub.config(bg=C["accent"])   # chi accent bar 3px

        for card in (self.card_file_sec, self.card_api_sec,
                     self.card_cfg_sec, self.card_sty_sec,
                     self.card_out_sec, self.card_skip_sec,
                     self.card_log):
            paint_card(card)

        # ── Row labels ───────────────────────────────────────────────────────
        for lbl_w in (self.lbl_api_prov, self.lbl_api_model, self.lbl_api_key_lbl,
                      self.lbl_model, self.lbl_src_lang, self.lbl_dst_lang):
            lbl_w.config(bg=C["surface"], fg=C["text_muted"])

        # ── Desc / hint labels ───────────────────────────────────────────────
        for lbl_w in (self.lbl_style_desc, self.lbl_fmt_desc,
                      self.lbl_skip_hint, self.lbl_skip_eg):
            lbl_w.config(bg=C["surface"], fg=C["text_dim"])

        # ── Inner content frames (bg surface, khong phai header) ─────────────
        for f in (self.inner_file, self.inner_api, self.inner_cfg,
                  self.inner_sty, self.inner_out, self.inner_skip,
                  self.key_row, self.skip_row):
            f.config(bg=C["surface"])
            self.lbl_style_desc.config(bg=C["surface"])

        # ── Seg frames ───────────────────────────────────────────────────────
        for frame in (self.frame_prov_seg, self.frame_api_model_seg,
                      self.frame_model_seg, self.frame_style_seg,
                      self.frame_out_seg):
            frame.config(bg=C["surface"])

        # ── Segmented buttons ─────────────────────────────────────────────────
        for buttons, var, rf in self._segs:
            for b, _ in buttons:
                b.config(bg=C["si"], fg=C["sfi"],
                         activebackground=C["sa"], activeforeground=C["sfa"])
            rf(var.get())

        # ── Entries ───────────────────────────────────────────────────────────
        for e in (self.entry_src_lang, self.entry_dst_lang,
                  self.entry_skip, self.entry_api_key):
            e.config(bg=C["surface2"], fg=C["text"],
                     insertbackground=C["accent"],
                     highlightbackground=C["border"],
                     highlightcolor=C["accent"])

        # ── Nut phu ───────────────────────────────────────────────────────────
        self.btn_toggle_key.config(bg=C["surface2"], fg=C["text_muted"],
                                   activebackground=C["border"],
                                   activeforeground=C["accent"])
        self.btn_skip_clear.config(bg=C["surface2"], fg=C["text_muted"],
                                   activebackground=C["border"],
                                   activeforeground=C["text"])

        # ── Log ───────────────────────────────────────────────────────────────
        self.card_log.config(bg=C["surface"], highlightbackground=C["border"])
        self.text_log.config(bg=C["log_bg"], fg=C["text_muted"],
                             insertbackground=C["accent"],
                             selectbackground=C["accent"],
                             selectforeground=C["text"])
        self.frame_prog_track.config(bg=C["surface2"])
        self.frame_prog_fill.config(bg=C["accent"])

        # ── Action buttons ────────────────────────────────────────────────────
        self.frame_actions.config(bg=C["bg"])
        self.btn_run.config(bg=C["accent"], fg="#ffffff",
                            activebackground=C["accent2"],
                            activeforeground="#ffffff")
        self.btn_clear_log.config(bg=C["surface2"], fg=C["text_muted"],
                                  activebackground=C["border"],
                                  activeforeground=C["text"])
        self.btn_quit.config(bg=C["surface2"], fg=C["text_muted"],
                             activebackground=C["border"],
                             activeforeground=C["text"])

        # Cap nhat provider (refresh model buttons)
        self._on_provider_change(self.var_api_provider.get())

    # ==========================================================================
    # LOG / PROGRESS
    # ==========================================================================
    def _log(self, message: str, tag: Optional[str] = None) -> None:
        prefix = {"ok":"✓  ","err":"✗  ","warn":"⚠  "}.get(tag, "›  ")
        self.text_log.config(state="normal")
        self.text_log.insert("end", prefix + message + "\n")
        self.text_log.see("end")
        self.text_log.config(state="disabled")

    def _clear_log(self) -> None:
        self.text_log.config(state="normal")
        self.text_log.delete("1.0", "end")
        self.text_log.config(state="disabled")

    def _set_progress(self, percent: int) -> None:
        self.update_idletasks()
        w = self.frame_prog_track.winfo_width()
        self.frame_prog_fill.place(x=0, y=0, relheight=1,
                                   width=int(w * percent / 100))

    # ==========================================================================
    # BROWSE FILE
    # ==========================================================================
    def _browse_file(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Media","*.mp4 *.mkv *.avi *.m4a *.mp3 *.wav"),
                       ("All files","*.*")])
        if not path:
            return
        self.selected_file = path
        name = os.path.basename(path)
        size = os.path.getsize(path) / 1024 / 1024
        self.lbl_file_icon.config(text="✔", fg=self._C["success"])
        self.lbl_file_name.config(text=f"{name}  ({size:.1f} MB)",
                                  fg=self._C["accent"])
        self._log(f"Da chon: {name}", "ok")

    # ==========================================================================
    # PROCESS
    # ==========================================================================
    def _start(self) -> None:
        if self._busy:
            return
        if not self.selected_file:
            self._log("Vui long chon file media truoc!", "err")
            return
        self._busy = True
        self.btn_run.config(state="disabled", text="⏳  Dang xu ly ...")
        self._set_progress(0)
        threading.Thread(target=self._pipeline, daemon=True).start()

    def _pipeline(self) -> None:
        try:
            model_size  = self.var_model.get()
            target_lang = self.var_dst_lang.get()
            out_format  = self.var_output_format.get()
            skip_list   = [w.strip() for w in
                           self.var_skip_words.get().split(",") if w.strip()]

            self.after(0, self._log, f"Tai model Whisper [{model_size}] ...")
            self.after(0, self._set_progress, 10)
            engine = AIEngine(model_size=model_size)

            self.after(0, self._log, "Nhan dien giong noi ...")
            self.after(0, self._set_progress, 30)
            results = engine.transcribe_audio(self.selected_file)

            if not results:
                self.after(0, self._log, "Khong nhan dien duoc.", "err")
                return

            self.after(0, self._log, f"Xong: {len(results)} doan.", "ok")
            self.after(0, self._set_progress, 60)

            lang_code = LANGUAGE_CODES.get(target_lang, "vi")
            self.after(0, self._log, f"Dang dich sang {target_lang} ...")
            translator = SubtitleTranslator(target_language=lang_code)
            translated = translator.translate_segments(results)

            if skip_list:
                self.after(0, self._log,
                           f"Giu nguyen: {', '.join(skip_list)}")

            self.after(0, self._set_progress, 85)
            os.makedirs("output", exist_ok=True)
            out_path = f"output/result{out_format}"

            if out_format == ".srt":
                translator.save_to_srt(translated, out_path)
            else:
                with open(out_path, "w", encoding="utf-8") as f:
                    for seg in translated:
                        t = seg.get("text", "").strip()
                        if t:
                            f.write(t + "\n")

            self.after(0, self._set_progress, 100)
            self.after(0, self._log, f"Hoan tat! Da luu: {out_path}", "ok")

        except Exception as err:
            self.after(0, self._log, str(err), "err")
        finally:
            self.after(0, self._done)

    def _done(self) -> None:
        self._busy = False
        self.btn_run.config(state="normal", text="▶  Bat dau xu ly")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = SubtitleAppUI()
    app.mainloop()