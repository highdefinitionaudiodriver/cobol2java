"""
COBOL to Java Migration Tool
A GUI application that converts COBOL source code to Java (59 languages supported)
"""
import os
import sys
import threading
import traceback
import argparse
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from datetime import datetime

# Support running as script or frozen exe
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

from src.cobol_parser import CobolParser
from src.oop_transformer import OopTransformer, TransformOptions
from src.java_generator import JavaCodeGenerator
from src.i18n import I18n, LANGUAGES
from src.vendor_extensions import (
    VendorType, VENDOR_DISPLAY_NAMES, detect_vendor
)


class CobolToJavaApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.i18n = I18n("en")  # Default: English
        self.root.geometry("850x750")
        self.root.minsize(720, 620)
        self.root.resizable(True, True)

        self.is_running = False
        self.cancel_flag = False

        # Store widget references for language switching
        self._widgets = {}

        self._setup_styles()
        self._build_ui()
        self._apply_language()

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

        # Language selector (right side)
        lang_frame = ttk.Frame(top_frame)
        lang_frame.pack(side=tk.RIGHT)

        self._widgets["lang_label"] = ttk.Label(lang_frame)
        self._widgets["lang_label"].pack(side=tk.LEFT, padx=(0, 4))

        self.lang_var = tk.StringVar(value="en")
        lang_display = [f"{v}" for v in LANGUAGES.values()]
        lang_codes = list(LANGUAGES.keys())
        self._lang_code_map = dict(zip(lang_display, lang_codes))

        lang_combo = ttk.Combobox(
            lang_frame, textvariable=tk.StringVar(value="English"),
            values=lang_display, width=12, state="readonly"
        )
        lang_combo.pack(side=tk.LEFT)
        lang_combo.bind("<<ComboboxSelected>>", lambda e: self._on_language_change(
            self._lang_code_map.get(lang_combo.get(), "en")
        ))
        self._widgets["lang_combo"] = lang_combo

        # --- Folder Selection ---
        self._widgets["folder_frame"] = ttk.LabelFrame(main_frame, padding=10)
        self._widgets["folder_frame"].pack(fill=tk.X, pady=(0, 8))
        folder_frame = self._widgets["folder_frame"]

        self._widgets["input_label"] = ttk.Label(folder_frame, style="Header.TLabel")
        self._widgets["input_label"].grid(row=0, column=0, sticky=tk.W, pady=2)

        self.input_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.input_var, width=60).grid(
            row=0, column=1, padx=5, pady=2, sticky=tk.EW
        )
        self._widgets["browse_input"] = ttk.Button(folder_frame, command=self._browse_input)
        self._widgets["browse_input"].grid(row=0, column=2, padx=2, pady=2)

        self._widgets["output_label"] = ttk.Label(folder_frame, style="Header.TLabel")
        self._widgets["output_label"].grid(row=1, column=0, sticky=tk.W, pady=2)

        self.output_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.output_var, width=60).grid(
            row=1, column=1, padx=5, pady=2, sticky=tk.EW
        )
        self._widgets["browse_output"] = ttk.Button(folder_frame, command=self._browse_output)
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
        self.package_var = tk.StringVar(value="com.migrated")
        ttk.Entry(pkg_frame, textvariable=self.package_var, width=30).pack(side=tk.LEFT, padx=5)

        enc_frame = ttk.Frame(left_opts)
        enc_frame.pack(fill=tk.X, pady=2)
        self._widgets["enc_label"] = ttk.Label(enc_frame)
        self._widgets["enc_label"].pack(side=tk.LEFT)
        self.encoding_var = tk.StringVar(value="utf-8")
        ttk.Combobox(
            enc_frame, textvariable=self.encoding_var, width=15,
            values=["utf-8", "shift_jis", "euc-jp", "cp932", "iso-8859-1", "cp1252", "ascii"],
            state="readonly"
        ).pack(side=tk.LEFT, padx=5)

        ext_frame = ttk.Frame(left_opts)
        ext_frame.pack(fill=tk.X, pady=2)
        self._widgets["ext_label"] = ttk.Label(ext_frame)
        self._widgets["ext_label"].pack(side=tk.LEFT)
        self.extensions_var = tk.StringVar(value=".cbl,.cob,.cobol,.CBL,.COB")
        ttk.Entry(ext_frame, textvariable=self.extensions_var, width=30).pack(side=tk.LEFT, padx=5)

        # Vendor dialect selector
        vendor_frame = ttk.Frame(left_opts)
        vendor_frame.pack(fill=tk.X, pady=2)
        self._widgets["vendor_label"] = ttk.Label(vendor_frame)
        self._widgets["vendor_label"].pack(side=tk.LEFT)

        self.vendor_var = tk.StringVar(value="auto")
        self._vendor_options = [
            ("auto", "Auto Detect"),
            ("standard", "COBOL Standard"),
            ("ibm", "IBM Enterprise COBOL"),
            ("fujitsu", "Fujitsu NetCOBOL"),
            ("nec", "NEC ACOS COBOL"),
            ("hitachi", "Hitachi VOS3 COBOL"),
            ("microfocus", "Micro Focus Visual COBOL"),
            ("unisys", "Unisys MCP/ClearPath"),
            ("bull", "Bull/Atos GCOS"),
            ("hp", "HP NonStop COBOL"),
            ("gnucobol", "GnuCOBOL"),
        ]
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

        self.getter_setter_var = tk.BooleanVar(value=True)
        self._widgets["cb_getters"] = ttk.Checkbutton(right_opts, variable=self.getter_setter_var)
        self._widgets["cb_getters"].pack(anchor=tk.W, pady=1)

        self.big_decimal_var = tk.BooleanVar(value=True)
        self._widgets["cb_bigdecimal"] = ttk.Checkbutton(right_opts, variable=self.big_decimal_var)
        self._widgets["cb_bigdecimal"].pack(anchor=tk.W, pady=1)

        self.javadoc_var = tk.BooleanVar(value=True)
        self._widgets["cb_javadoc"] = ttk.Checkbutton(right_opts, variable=self.javadoc_var)
        self._widgets["cb_javadoc"].pack(anchor=tk.W, pady=1)

        self.extract_classes_var = tk.BooleanVar(value=True)
        self._widgets["cb_classes"] = ttk.Checkbutton(right_opts, variable=self.extract_classes_var)
        self._widgets["cb_classes"].pack(anchor=tk.W, pady=1)

        self.extract_enums_var = tk.BooleanVar(value=True)
        self._widgets["cb_enums"] = ttk.Checkbutton(right_opts, variable=self.extract_enums_var)
        self._widgets["cb_enums"].pack(anchor=tk.W, pady=1)

        self.extract_services_var = tk.BooleanVar(value=True)
        self._widgets["cb_services"] = ttk.Checkbutton(right_opts, variable=self.extract_services_var)
        self._widgets["cb_services"].pack(anchor=tk.W, pady=1)

        self.toString_var = tk.BooleanVar(value=True)
        self._widgets["cb_tostring"] = ttk.Checkbutton(right_opts, variable=self.toString_var)
        self._widgets["cb_tostring"].pack(anchor=tk.W, pady=1)

        self.extract_file_handlers_var = tk.BooleanVar(value=True)
        self._widgets["cb_filehandlers"] = ttk.Checkbutton(right_opts, variable=self.extract_file_handlers_var)
        self._widgets["cb_filehandlers"].pack(anchor=tk.W, pady=1)

        # --- Action Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 8))

        self._widgets["run_btn"] = ttk.Button(
            button_frame, command=self._start_conversion,
            style="Run.TButton", width=20
        )
        self._widgets["run_btn"].pack(side=tk.LEFT, padx=5)
        self.run_button = self._widgets["run_btn"]

        self._widgets["cancel_btn"] = ttk.Button(
            button_frame, command=self._cancel_conversion,
            state=tk.DISABLED, width=12
        )
        self._widgets["cancel_btn"].pack(side=tk.LEFT, padx=5)
        self.cancel_button = self._widgets["cancel_btn"]

        self._widgets["clear_btn"] = ttk.Button(
            button_frame, command=self._clear_log, width=12
        )
        self._widgets["clear_btn"].pack(side=tk.RIGHT, padx=5)

        # --- Progress ---
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 4))

        self.progress_var = tk.DoubleVar(value=0)
        ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100, mode="determinate"
        ).pack(fill=tk.X, side=tk.LEFT, expand=True)

        self.status_var = tk.StringVar()
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

    def _apply_language(self):
        """Apply current language to all widgets."""
        t = self._t

        self.root.title(t("app_title"))
        self._widgets["title"].configure(text=t("app_heading"))
        self._widgets["lang_label"].configure(text=t("language_label"))

        # Folders
        self._widgets["folder_frame"].configure(text=t("folders_frame"))
        self._widgets["input_label"].configure(text=t("input_folder_label"))
        self._widgets["output_label"].configure(text=t("output_folder_label"))
        self._widgets["browse_input"].configure(text=t("browse_button"))
        self._widgets["browse_output"].configure(text=t("browse_button"))

        # Options
        self._widgets["options_frame"].configure(text=t("options_frame"))
        self._widgets["pkg_label"].configure(text=t("package_name_label"))
        self._widgets["enc_label"].configure(text=t("encoding_label"))
        self._widgets["ext_label"].configure(text=t("extensions_label"))

        # Vendor
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

        # Buttons
        self._widgets["run_btn"].configure(text=t("convert_button"))
        self._widgets["cancel_btn"].configure(text=t("cancel_button"))
        self._widgets["clear_btn"].configure(text=t("clear_log_button"))

        # Status
        if not self.is_running:
            self.status_var.set(t("status_ready"))

        # Log frame
        self._widgets["log_frame"].configure(text=t("log_frame"))

    def _on_language_change(self, lang_code: str):
        self.i18n.lang = lang_code
        self._apply_language()

    def _browse_input(self):
        folder = filedialog.askdirectory(title=self._t("browse_input_title"))
        if folder:
            self.input_var.set(folder)

    def _browse_output(self):
        folder = filedialog.askdirectory(title=self._t("browse_output_title"))
        if folder:
            self.output_var.set(folder)

    def _clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)

    def _log(self, message: str, tag: str = "info"):
        self.log_text.configure(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)

    def _start_conversion(self):
        t = self._t
        input_dir = self.input_var.get().strip()
        output_dir = self.output_var.get().strip()

        if not input_dir:
            messagebox.showwarning(t("warn_title"), t("warn_no_input"))
            return
        if not output_dir:
            messagebox.showwarning(t("warn_title"), t("warn_no_output"))
            return
        if not os.path.isdir(input_dir):
            messagebox.showerror(t("error_title"), t("error_no_input_dir", path=input_dir))
            return

        self.is_running = True
        self.cancel_flag = False
        self.run_button.configure(state=tk.DISABLED)
        self.cancel_button.configure(state=tk.NORMAL)
        self.progress_var.set(0)

        thread = threading.Thread(target=self._run_conversion, args=(input_dir, output_dir), daemon=True)
        thread.start()

    def _cancel_conversion(self):
        self.cancel_flag = True
        self._log(self._t("log_cancel_request"), "warning")

    def _run_conversion(self, input_dir: str, output_dir: str):
        t = self._t
        try:
            self._log("=" * 60, "header")
            self._log(t("log_starting"), "header")
            self._log("=" * 60, "header")
            self._log(t("log_input", path=input_dir))
            self._log(t("log_output", path=output_dir))

            extensions = [e.strip() for e in self.extensions_var.get().split(",")]
            cobol_files = []
            for root_dir, dirs, files in os.walk(input_dir):
                for f in files:
                    if any(f.endswith(ext) for ext in extensions):
                        cobol_files.append(os.path.join(root_dir, f))

            if not cobol_files:
                self._log(t("log_no_files", ext=str(extensions)), "warning")
                self._finish()
                return

            self._log(t("log_found_files", count=len(cobol_files)), "info")

            # Resolve vendor selection
            vendor_display_sel = self._widgets["vendor_combo"].get()
            selected_vendor = self._vendor_code_map.get(vendor_display_sel, "auto")

            options = TransformOptions(
                package_name=self.package_var.get().strip() or "com.migrated",
                generate_getters_setters=self.getter_setter_var.get(),
                use_big_decimal=self.big_decimal_var.get(),
                generate_javadoc=self.javadoc_var.get(),
                generate_toString=self.toString_var.get(),
                extract_data_classes=self.extract_classes_var.get(),
                extract_enums=self.extract_enums_var.get(),
                extract_file_handlers=self.extract_file_handlers_var.get(),
                group_related_paragraphs=self.extract_services_var.get(),
                vendor_type=selected_vendor,
            )

            parser = CobolParser(encoding=self.encoding_var.get())
            transformer = OopTransformer(options)
            generator = JavaCodeGenerator(options)

            success_count = 0
            error_count = 0

            for i, filepath in enumerate(cobol_files):
                if self.cancel_flag:
                    self._log(t("log_cancelled"), "warning")
                    break

                rel_path = os.path.relpath(filepath, input_dir)
                filename = os.path.basename(filepath)
                display_name = rel_path if os.path.dirname(rel_path) else filename
                progress = ((i + 1) / len(cobol_files)) * 100
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                self.root.after(0, lambda f=display_name: self.status_var.set(
                    t("status_processing", file=f)
                ))

                self._log(f"\n{t('log_processing', file=display_name)}", "header")

                try:
                    self._log(t("log_parsing"), "info")
                    program = parser.parse_file(filepath)

                    # Vendor detection / assignment
                    if selected_vendor == "auto":
                        with open(filepath, "r", encoding=self.encoding_var.get(), errors="replace") as vf:
                            src_lines = vf.readlines()
                        detected = detect_vendor(src_lines)
                        program.vendor_type = detected.value
                        self._log(t("log_vendor_detected",
                                     vendor=VENDOR_DISPLAY_NAMES.get(detected, detected.value)), "info")
                    else:
                        program.vendor_type = selected_vendor
                        self._log(t("log_vendor_set", vendor=selected_vendor), "info")

                    self._log(t("log_program_id", id=program.program_id or "(unknown)"))
                    self._log(t("log_ws_items", count=len(program.working_storage)))
                    self._log(t("log_paragraphs", count=len(program.paragraphs)))
                    self._log(t("log_sections", count=len(program.sections)))
                    self._log(t("log_files", count=len(program.files)))
                    if program.has_exec_sql:
                        self._log(t("log_exec_sql", count="detected"), "info")
                    if program.has_exec_cics:
                        self._log(t("log_exec_cics", count="detected"), "info")
                    if program.has_exec_dli:
                        self._log(t("log_exec_dli"), "info")
                    if program.has_class_id:
                        self._log(t("log_oo_cobol"), "info")
                    if program.screen_section:
                        self._log(t("log_screen_section", count=len(program.screen_section)), "info")

                    self._log(t("log_transforming"), "info")
                    project = transformer.transform(program)

                    if project.main_class:
                        self._log(t("log_main_class", name=project.main_class.name))
                        self._log(t("log_fields", count=len(project.main_class.fields)))
                        self._log(t("log_methods", count=len(project.main_class.methods)))
                    self._log(t("log_data_classes", count=len(project.data_classes)))
                    self._log(t("log_enum_classes", count=len(project.enum_classes)))
                    self._log(t("log_service_classes", count=len(project.service_classes)))
                    self._log(t("log_file_handlers", count=len(project.file_handler_classes)))

                    self._log(t("log_generating"), "info")
                    # Preserve subfolder structure in output
                    rel_dir = os.path.relpath(os.path.dirname(filepath), input_dir)
                    if rel_dir == ".":
                        file_output_dir = output_dir
                    else:
                        file_output_dir = os.path.join(output_dir, rel_dir)
                    generator.generate_project(project, file_output_dir)

                    total_classes = (
                        (1 if project.main_class else 0) +
                        len(project.data_classes) +
                        len(project.enum_classes) +
                        len(project.service_classes) +
                        len(project.file_handler_classes)
                    )
                    self._log(t("log_generated", count=total_classes), "success")
                    success_count += 1

                except Exception as e:
                    error_count += 1
                    self._log(f"  ERROR: {str(e)}", "error")
                    self._log(f"  {traceback.format_exc()}", "error")

            self._log(f"\n{'=' * 60}", "header")
            self._log(t("log_migration_complete"), "header")
            self._log(f"{'=' * 60}", "header")
            self._log(t("log_success", count=success_count), "success")
            if error_count > 0:
                self._log(t("log_errors", count=error_count), "error")
            self._log(t("log_output", path=output_dir), "info")

        except Exception as e:
            self._log(f"Fatal error: {str(e)}", "error")
            self._log(traceback.format_exc(), "error")

        finally:
            self._finish()

    def _finish(self):
        self.is_running = False
        self.root.after(0, lambda: self.run_button.configure(state=tk.NORMAL))
        self.root.after(0, lambda: self.cancel_button.configure(state=tk.DISABLED))
        self.root.after(0, lambda: self.status_var.set(self._t("status_complete")))
        self.root.after(0, lambda: self.progress_var.set(100))


def run_cli(args):
    """Execute conversion without GUI."""
    print("=" * 60)
    print("COBOL to Java Migration - Starting (CLI Mode)")
    print("=" * 60)

    input_dir = args.input.strip()
    output_dir = args.output.strip()

    if not os.path.isdir(input_dir):
        print(f"[ERROR] Input directory does not exist: {input_dir}")
        sys.exit(1)

    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Vendor: {args.vendor}")
    print(f"Package: {args.package}")

    extensions = [e.strip() for e in args.ext.split(",")]
    cobol_files = []
    for root_dir, dirs, files in os.walk(input_dir):
        for f in files:
            if any(f.endswith(ext) for ext in extensions):
                cobol_files.append(os.path.join(root_dir, f))

    if not cobol_files:
        print(f"[WARNING] No COBOL files found with extensions: {extensions}")
        sys.exit(0)

    print(f"Found {len(cobol_files)} COBOL file(s).")

    options = TransformOptions(
        package_name=args.package,
        generate_getters_setters=not args.no_getters,
        use_big_decimal=not args.no_bigdecimal,
        generate_javadoc=not args.no_javadoc,
        generate_toString=not args.no_tostring,
        extract_data_classes=not args.no_classes,
        extract_enums=not args.no_enums,
        extract_file_handlers=not args.no_filehandlers,
        group_related_paragraphs=not args.no_services,
        vendor_type=args.vendor,
    )

    parser = CobolParser(encoding=args.encoding)
    transformer = OopTransformer(options)
    generator = JavaCodeGenerator(options)

    success_count = 0
    error_count = 0

    for filepath in cobol_files:
        filename = os.path.basename(filepath)
        print(f"\n--- Processing: {filename} ---")
        try:
            program = parser.parse_file(filepath)

            if args.vendor == "auto":
                try:
                    with open(filepath, "r", encoding=args.encoding, errors="replace") as vf:
                        src_lines = vf.readlines()
                    detected = detect_vendor(src_lines)
                    program.vendor_type = detected.value
                    vendor_name = VENDOR_DISPLAY_NAMES.get(detected, detected.value)
                    print(f"  Vendor detected: {vendor_name}")
                except Exception as e:
                    print(f"  Warning: Vendor detection failed: {str(e)}")
            else:
                program.vendor_type = args.vendor

            project = transformer.transform(program)

            rel_dir = os.path.relpath(os.path.dirname(filepath), input_dir)
            if rel_dir == ".":
                file_output_dir = output_dir
            else:
                file_output_dir = os.path.join(output_dir, rel_dir)

            generator.generate_project(project, file_output_dir)
            success_count += 1
            print("  Success.")

        except Exception as e:
            error_count += 1
            print(f"  [ERROR] {str(e)}")
            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print("Migration Complete")
    print(f"{'=' * 60}")
    print(f"  Success: {success_count} file(s)")
    if error_count > 0:
        print(f"  Errors:  {error_count} file(s)")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="COBOL to Java Migration Tool")
    parser.add_argument("-i", "--input", help="Input folder containing COBOL files (CLI execution)")
    parser.add_argument("-o", "--output", help="Output folder for generated Java files")
    parser.add_argument("-p", "--package", default="com.migrated", help="Package name for generated classes (default: com.migrated)")
    parser.add_argument("-e", "--encoding", default="utf-8", help="Source encoding (default: utf-8)")
    parser.add_argument("--ext", default=".cbl,.cob,.cobol,.CBL,.COB", help="Comma-separated file extensions to process (default: .cbl,.cob,.cobol,.CBL,.COB)")
    parser.add_argument("--vendor", default="auto", choices=["auto", "standard", "ibm", "fujitsu", "nec", "hitachi", "microfocus", "unisys", "bull", "hp", "gnucobol"], help="Vendor dialect (default: auto)")

    parser.add_argument("--no-getters", action="store_true", help="Disable generating Getters/Setters")
    parser.add_argument("--no-bigdecimal", action="store_true", help="Disable using BigDecimal for decimals")
    parser.add_argument("--no-javadoc", action="store_true", help="Disable generating Javadoc comments")
    parser.add_argument("--no-tostring", action="store_true", help="Disable generating toString()")
    parser.add_argument("--no-classes", action="store_true", help="Disable extracting Data Classes")
    parser.add_argument("--no-enums", action="store_true", help="Disable extracting Enums")
    parser.add_argument("--no-services", action="store_true", help="Disable extracting Services")
    parser.add_argument("--no-filehandlers", action="store_true", help="Disable extracting File Handlers")

    args = parser.parse_args()

    # If standard inputs are provided, run CLI, else GUI
    if args.input and args.output:
        run_cli(args)
    elif args.input or args.output:
        print("[ERROR] Both -i/--input and -o/--output must be provided for CLI execution.")
        sys.exit(1)
    else:
        root = tk.Tk()

        icon_path = os.path.join(BASE_DIR, "icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)

        app = CobolToJavaApp(root)
        root.mainloop()


if __name__ == "__main__":
    main()
