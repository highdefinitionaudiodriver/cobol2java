"""
GUI View layer.
tkinterウィジェットの生成・配置・スタイリングのみを担当。
イベントハンドリングはController経由でバインドする。
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Callable, Dict, List

from .i18n import I18n, LANGUAGES
from .gui_model import VENDOR_OPTIONS


class CobolToJavaView:
    """View: ウィジェットの生成・レイアウトのみ."""

    def __init__(self, root: tk.Tk, i18n: I18n):
        self.root = root
        self.i18n = i18n
        self.root.geometry("850x750")
        self.root.minsize(720, 620)
        self.root.resizable(True, True)

        self._widgets: Dict[str, ttk.Widget] = {}

        # tkinter variables (View owns display state)
        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.package_var = tk.StringVar(value="com.migrated")
        self.encoding_var = tk.StringVar(value="utf-8")
        self.extensions_var = tk.StringVar(value=".cbl,.cob,.cobol,.CBL,.COB")
        self.vendor_var = tk.StringVar(value="auto")

        self.getter_setter_var = tk.BooleanVar(value=True)
        self.big_decimal_var = tk.BooleanVar(value=True)
        self.javadoc_var = tk.BooleanVar(value=True)
        self.extract_classes_var = tk.BooleanVar(value=True)
        self.extract_enums_var = tk.BooleanVar(value=True)
        self.extract_services_var = tk.BooleanVar(value=True)
        self.toString_var = tk.BooleanVar(value=True)
        self.extract_file_handlers_var = tk.BooleanVar(value=True)

        self.progress_var = tk.DoubleVar(value=0)
        self.status_var = tk.StringVar()

        # Language mapping
        lang_display = [f"{v}" for v in LANGUAGES.values()]
        lang_codes = list(LANGUAGES.keys())
        self._lang_code_map = dict(zip(lang_display, lang_codes))

        # Vendor mapping
        self._vendor_options = VENDOR_OPTIONS
        self._vendor_code_map: Dict[str, str] = {}

        self._setup_styles()
        self._build_ui()

    def _t(self, key: str, **kwargs) -> str:
        return self.i18n.t(key, **kwargs)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), foreground="#2c3e50")
        style.configure("Header.TLabel", font=("Segoe UI", 10, "bold"))
        style.configure("Run.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", font=("Segoe UI", 9, "bold"))

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Top bar: Title + Language selector ---
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        self._widgets["title"] = ttk.Label(top_frame, style="Title.TLabel")
        self._widgets["title"].pack(side=tk.LEFT)

        lang_frame = ttk.Frame(top_frame)
        lang_frame.pack(side=tk.RIGHT)

        self._widgets["lang_label"] = ttk.Label(lang_frame)
        self._widgets["lang_label"].pack(side=tk.LEFT, padx=(0, 4))

        lang_display = list(self._lang_code_map.keys())
        lang_combo = ttk.Combobox(
            lang_frame, textvariable=tk.StringVar(value="English"),
            values=lang_display, width=12, state="readonly"
        )
        lang_combo.pack(side=tk.LEFT)
        self._widgets["lang_combo"] = lang_combo

        # --- Folder Selection ---
        self._widgets["folder_frame"] = ttk.LabelFrame(main_frame, padding=10)
        self._widgets["folder_frame"].pack(fill=tk.X, pady=(0, 8))
        folder_frame = self._widgets["folder_frame"]

        self._widgets["input_label"] = ttk.Label(folder_frame, style="Header.TLabel")
        self._widgets["input_label"].grid(row=0, column=0, sticky=tk.W, pady=2)

        ttk.Entry(folder_frame, textvariable=self.input_var, width=60).grid(
            row=0, column=1, padx=5, pady=2, sticky=tk.EW
        )
        self._widgets["browse_input"] = ttk.Button(folder_frame)
        self._widgets["browse_input"].grid(row=0, column=2, padx=2, pady=2)

        self._widgets["output_label"] = ttk.Label(folder_frame, style="Header.TLabel")
        self._widgets["output_label"].grid(row=1, column=0, sticky=tk.W, pady=2)

        ttk.Entry(folder_frame, textvariable=self.output_var, width=60).grid(
            row=1, column=1, padx=5, pady=2, sticky=tk.EW
        )
        self._widgets["browse_output"] = ttk.Button(folder_frame)
        self._widgets["browse_output"].grid(row=1, column=2, padx=2, pady=2)

        folder_frame.columnconfigure(1, weight=1)

        # --- Options ---
        self._widgets["options_frame"] = ttk.LabelFrame(main_frame, padding=10)
        self._widgets["options_frame"].pack(fill=tk.X, pady=(0, 8))
        options_frame = self._widgets["options_frame"]

        # Left column
        left_opts = ttk.Frame(options_frame)
        left_opts.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        pkg_frame = ttk.Frame(left_opts)
        pkg_frame.pack(fill=tk.X, pady=2)
        self._widgets["pkg_label"] = ttk.Label(pkg_frame)
        self._widgets["pkg_label"].pack(side=tk.LEFT)
        ttk.Entry(pkg_frame, textvariable=self.package_var, width=30).pack(side=tk.LEFT, padx=5)

        enc_frame = ttk.Frame(left_opts)
        enc_frame.pack(fill=tk.X, pady=2)
        self._widgets["enc_label"] = ttk.Label(enc_frame)
        self._widgets["enc_label"].pack(side=tk.LEFT)
        ttk.Combobox(
            enc_frame, textvariable=self.encoding_var, width=15,
            values=["utf-8", "shift_jis", "euc-jp", "cp932", "iso-8859-1", "cp1252", "ascii"],
            state="readonly"
        ).pack(side=tk.LEFT, padx=5)

        ext_frame = ttk.Frame(left_opts)
        ext_frame.pack(fill=tk.X, pady=2)
        self._widgets["ext_label"] = ttk.Label(ext_frame)
        self._widgets["ext_label"].pack(side=tk.LEFT)
        ttk.Entry(ext_frame, textvariable=self.extensions_var, width=30).pack(side=tk.LEFT, padx=5)

        vendor_frame = ttk.Frame(left_opts)
        vendor_frame.pack(fill=tk.X, pady=2)
        self._widgets["vendor_label"] = ttk.Label(vendor_frame)
        self._widgets["vendor_label"].pack(side=tk.LEFT)

        vendor_display = [name for _, name in self._vendor_options]
        self._vendor_code_map = {name: code for code, name in self._vendor_options}

        self._widgets["vendor_combo"] = ttk.Combobox(
            vendor_frame, values=vendor_display, width=30, state="readonly"
        )
        self._widgets["vendor_combo"].set(vendor_display[0])
        self._widgets["vendor_combo"].pack(side=tk.LEFT, padx=5)

        # Right column - checkboxes
        right_opts = ttk.Frame(options_frame)
        right_opts.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0))

        self._widgets["cb_getters"] = ttk.Checkbutton(right_opts, variable=self.getter_setter_var)
        self._widgets["cb_getters"].pack(anchor=tk.W, pady=1)

        self._widgets["cb_bigdecimal"] = ttk.Checkbutton(right_opts, variable=self.big_decimal_var)
        self._widgets["cb_bigdecimal"].pack(anchor=tk.W, pady=1)

        self._widgets["cb_javadoc"] = ttk.Checkbutton(right_opts, variable=self.javadoc_var)
        self._widgets["cb_javadoc"].pack(anchor=tk.W, pady=1)

        self._widgets["cb_classes"] = ttk.Checkbutton(right_opts, variable=self.extract_classes_var)
        self._widgets["cb_classes"].pack(anchor=tk.W, pady=1)

        self._widgets["cb_enums"] = ttk.Checkbutton(right_opts, variable=self.extract_enums_var)
        self._widgets["cb_enums"].pack(anchor=tk.W, pady=1)

        self._widgets["cb_services"] = ttk.Checkbutton(right_opts, variable=self.extract_services_var)
        self._widgets["cb_services"].pack(anchor=tk.W, pady=1)

        self._widgets["cb_tostring"] = ttk.Checkbutton(right_opts, variable=self.toString_var)
        self._widgets["cb_tostring"].pack(anchor=tk.W, pady=1)

        self._widgets["cb_filehandlers"] = ttk.Checkbutton(right_opts, variable=self.extract_file_handlers_var)
        self._widgets["cb_filehandlers"].pack(anchor=tk.W, pady=1)

        # --- Action Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 8))

        self._widgets["run_btn"] = ttk.Button(button_frame, style="Run.TButton", width=20)
        self._widgets["run_btn"].pack(side=tk.LEFT, padx=5)

        self._widgets["cancel_btn"] = ttk.Button(button_frame, state=tk.DISABLED, width=12)
        self._widgets["cancel_btn"].pack(side=tk.LEFT, padx=5)

        self._widgets["clear_btn"] = ttk.Button(button_frame, width=12)
        self._widgets["clear_btn"].pack(side=tk.RIGHT, padx=5)

        # --- Progress ---
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 4))

        ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100, mode="determinate"
        ).pack(fill=tk.X, side=tk.LEFT, expand=True)

        ttk.Label(progress_frame, textvariable=self.status_var, width=30).pack(side=tk.RIGHT, padx=5)

        # --- Log Output ---
        self._widgets["log_frame"] = ttk.LabelFrame(main_frame, padding=5)
        self._widgets["log_frame"].pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            self._widgets["log_frame"], wrap=tk.WORD, font=("Consolas", 9),
            bg="#1e1e1e", fg="#d4d4d4", insertbackground="white",
            selectbackground="#264f78"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.log_text.tag_configure("info", foreground="#4ec9b0")
        self.log_text.tag_configure("success", foreground="#6a9955")
        self.log_text.tag_configure("warning", foreground="#dcdcaa")
        self.log_text.tag_configure("error", foreground="#f44747")
        self.log_text.tag_configure("header", foreground="#569cd6", font=("Consolas", 9, "bold"))

    # ---- Binding API (called by Controller) ----

    def bind_browse_input(self, callback: Callable):
        self._widgets["browse_input"].configure(command=callback)

    def bind_browse_output(self, callback: Callable):
        self._widgets["browse_output"].configure(command=callback)

    def bind_run(self, callback: Callable):
        self._widgets["run_btn"].configure(command=callback)

    def bind_cancel(self, callback: Callable):
        self._widgets["cancel_btn"].configure(command=callback)

    def bind_clear_log(self, callback: Callable):
        self._widgets["clear_btn"].configure(command=callback)

    def bind_language_change(self, callback: Callable):
        self._widgets["lang_combo"].bind(
            "<<ComboboxSelected>>",
            lambda e: callback(self._lang_code_map.get(self._widgets["lang_combo"].get(), "en"))
        )

    # ---- View update methods ----

    def log(self, message: str, tag: str = "info"):
        from datetime import datetime
        self.log_text.configure(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)

    def clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)

    def set_running_state(self, running: bool):
        if running:
            self._widgets["run_btn"].configure(state=tk.DISABLED)
            self._widgets["cancel_btn"].configure(state=tk.NORMAL)
        else:
            self._widgets["run_btn"].configure(state=tk.NORMAL)
            self._widgets["cancel_btn"].configure(state=tk.DISABLED)

    def get_selected_vendor_code(self) -> str:
        display = self._widgets["vendor_combo"].get()
        return self._vendor_code_map.get(display, "auto")

    def apply_language(self):
        t = self._t

        self.root.title(t("app_title"))
        self._widgets["title"].configure(text=t("app_heading"))
        self._widgets["lang_label"].configure(text=t("language_label"))

        self._widgets["folder_frame"].configure(text=t("folders_frame"))
        self._widgets["input_label"].configure(text=t("input_folder_label"))
        self._widgets["output_label"].configure(text=t("output_folder_label"))
        self._widgets["browse_input"].configure(text=t("browse_button"))
        self._widgets["browse_output"].configure(text=t("browse_button"))

        self._widgets["options_frame"].configure(text=t("options_frame"))
        self._widgets["pkg_label"].configure(text=t("package_name_label"))
        self._widgets["enc_label"].configure(text=t("encoding_label"))
        self._widgets["ext_label"].configure(text=t("extensions_label"))
        self._widgets["vendor_label"].configure(text=t("vendor_label"))

        # Update vendor dropdown display names
        vendor_display_i18n = [
            t("vendor_auto"), t("vendor_standard"), t("vendor_ibm"),
            t("vendor_fujitsu"), t("vendor_nec"), t("vendor_hitachi"),
            t("vendor_microfocus"), t("vendor_unisys"), t("vendor_bull"),
            t("vendor_hp"), t("vendor_gnucobol"),
        ]
        current_vendor_idx = self._widgets["vendor_combo"].current()
        self._widgets["vendor_combo"]["values"] = vendor_display_i18n
        vendor_codes = [code for code, _ in self._vendor_options]
        self._vendor_code_map = dict(zip(vendor_display_i18n, vendor_codes))
        if current_vendor_idx >= 0:
            self._widgets["vendor_combo"].current(current_vendor_idx)
        else:
            self._widgets["vendor_combo"].current(0)

        self._widgets["cb_getters"].configure(text=t("opt_getters_setters"))
        self._widgets["cb_bigdecimal"].configure(text=t("opt_big_decimal"))
        self._widgets["cb_javadoc"].configure(text=t("opt_javadoc"))
        self._widgets["cb_classes"].configure(text=t("opt_extract_classes"))
        self._widgets["cb_enums"].configure(text=t("opt_extract_enums"))
        self._widgets["cb_services"].configure(text=t("opt_extract_services"))
        self._widgets["cb_tostring"].configure(text=t("opt_toString"))
        self._widgets["cb_filehandlers"].configure(text=t("opt_file_handlers"))

        self._widgets["run_btn"].configure(text=t("convert_button"))
        self._widgets["cancel_btn"].configure(text=t("cancel_button"))
        self._widgets["clear_btn"].configure(text=t("clear_log_button"))

        self.status_var.set(t("status_ready"))
        self._widgets["log_frame"].configure(text=t("log_frame"))
